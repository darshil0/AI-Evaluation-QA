import logging
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate data quality and completeness"""

    REQUIRED_COLUMNS = {
        "raw_results": ["prompt_id", "prompt", "response", "timestamp"],
        "scored_results": ["prompt_id", "response", "overall_score", "grade"],
    }

    SCORE_RANGE = (0.0, 5.0)
    VALID_GRADES = ["A", "B", "C", "D", "F"]

    @classmethod
    def validate_dataframe(
        cls, df: pd.DataFrame, df_type: str = "raw_results"
    ) -> Tuple[bool, List[str]]:
        """Validate dataframe structure and content"""

        issues = []

        # Check if empty
        if df.empty:
            issues.append("Dataframe is empty")
            return False, issues

        # Check required columns
        required_cols = cls.REQUIRED_COLUMNS.get(df_type, [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")

        # Check for duplicate prompt IDs
        if "prompt_id" in df.columns:
            duplicates = df[df.duplicated("prompt_id", keep=False)]
            if not duplicates.empty:
                dup_ids = duplicates["prompt_id"].unique().tolist()
                issues.append(f"Duplicate prompt IDs found: {dup_ids}")

        # Validate scored results
        if df_type == "scored_results":
            score_issues = cls._validate_scores(df)
            issues.extend(score_issues)

            grade_issues = cls._validate_grades(df)
            issues.extend(grade_issues)

        # Check for null values in critical columns
        for col in required_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    issues.append(
                        f"Column '{col}' has {null_count} null values "
                        f"({null_count/len(df)*100:.1f}%)"
                    )

        # Check data types
        if "timestamp" in df.columns:
            try:
                pd.to_datetime(df["timestamp"])
            except (ValueError, TypeError) as e:
                issues.append(f"Invalid timestamp format: {str(e)}")

        is_valid = len(issues) == 0
        return is_valid, issues

    @classmethod
    def _validate_scores(cls, df: pd.DataFrame) -> List[str]:
        """Validate score values"""
        issues = []

        score_columns = [col for col in df.columns if col.startswith("score_")]

        for col in score_columns:
            # Check range
            out_of_range = df[(df[col] < cls.SCORE_RANGE[0]) | (df[col] > cls.SCORE_RANGE[1])]
            if not out_of_range.empty:
                issues.append(
                    f"Column '{col}' has {len(out_of_range)} values "
                    f"outside valid range {cls.SCORE_RANGE}"
                )

            # Check for suspicious patterns
            if col in df.columns:
                unique_values = df[col].nunique()
                if unique_values == 1:
                    issues.append(
                        f"Column '{col}' has only one unique value "
                        f"({df[col].iloc[0]}), possible scoring issue"
                    )

        return issues

    @classmethod
    def _validate_grades(cls, df: pd.DataFrame) -> List[str]:
        """Validate grade values"""
        issues = []

        if "grade" not in df.columns:
            return issues

        invalid_grades = df[~df["grade"].isin(cls.VALID_GRADES)]
        if not invalid_grades.empty:
            invalid_values = invalid_grades["grade"].unique().tolist()
            issues.append(
                f"Invalid grade values found: {invalid_values}. "
                f"Valid grades are: {cls.VALID_GRADES}"
            )

        # Check grade-score consistency
        if "overall_score" in df.columns:
            inconsistent = cls._check_grade_score_consistency(df)
            if not inconsistent.empty:
                issues.append(
                    f"Found {len(inconsistent)} rows with inconsistent "
                    f"grade-score relationships"
                )

        return issues

    @staticmethod
    def _check_grade_score_consistency(df: pd.DataFrame) -> pd.DataFrame:
        """Check if grades match scores"""

        def expected_grade(score):
            if pd.isna(score):
                return "F"
            if score >= 4.5:
                return "A"
            elif score >= 3.5:
                return "B"
            elif score >= 2.5:
                return "C"
            elif score >= 1.5:
                return "D"
            else:
                return "F"

        df_check = df.copy()
        df_check["expected_grade"] = df_check["overall_score"].apply(expected_grade)
        inconsistent = df_check[df_check["grade"] != df_check["expected_grade"]]

        return inconsistent

    @classmethod
    def clean_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataframe safely.

        **Preconditions:**
        - df: pandas.DataFrame (may be empty)

        **Postconditions:**
        - Returns: cleaned DataFrame
        - Duplicates: removed
        - Whitespace: trimmed on string cols
        - Scores: clipped to SCORE_RANGE
        - Grades: uppercase, validated

        **Failure Modes:**
        - Empty input -> return empty DataFrame
        - Invalid SCORE_RANGE -> raise ValueError
        - Clip exception -> re-raise with context
        """
        if df.empty:
            logger.warning("Input DataFrame is empty")
            return df.copy()

        df_clean = df.copy()

        # Validate SCORE_RANGE precondition
        if not (isinstance(cls.SCORE_RANGE, tuple) and len(cls.SCORE_RANGE) == 2):
            raise ValueError(f"SCORE_RANGE must be tuple of (min, max), got {cls.SCORE_RANGE}")

        # Trim whitespace on string columns safely preserving NaN/None
        string_columns = df_clean.select_dtypes(include=["object", "string"]).columns
        for col in string_columns:
            try:
                # Use series.apply to facilitate easier mocking in tests
                df_clean[col] = df_clean[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not trim column '{col}': {e}")

        # Remove duplicates AFTER trimming
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        duplicates_removed = initial_rows - len(df_clean)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate rows")

        # Clip scores safely
        score_columns = [
            col for col in df_clean.columns if col.startswith("score_") or col == "overall_score"
        ]
        for col in score_columns:
            try:
                df_clean[col] = df_clean[col].clip(*cls.SCORE_RANGE)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Could not clip column '{col}': {e}") from e

        # Fix grades
        if "grade" in df_clean.columns:
            df_clean["grade"] = df_clean["grade"].astype(str).str.upper()
            df_clean.loc[~df_clean["grade"].isin(cls.VALID_GRADES), "grade"] = "F"

        return df_clean

    @staticmethod
    def generate_data_quality_report(df: pd.DataFrame) -> Dict:
        """Generate comprehensive data quality report"""

        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024**2),
            "duplicate_rows": df.duplicated().sum(),
            "columns": {},
        }

        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
                "unique_values": int(df[col].nunique()),
                "memory_usage_mb": df[col].memory_usage(deep=True) / (1024**2),
            }

            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update(
                    {
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    }
                )

            report["columns"][col] = col_info

        return report

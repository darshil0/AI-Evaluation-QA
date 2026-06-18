import pandas as pd
import pytest

from scripts.data_validator import DataValidator


@pytest.fixture
def valid_raw_df():
    return pd.DataFrame(
        {
            "prompt_id": ["P1", "P2", "P3"],
            "prompt": ["Prompt 1", "Prompt 2", "Prompt 3"],
            "response": ["Response 1", "Response 2", "Response 3"],
            "timestamp": pd.date_range("2024-01-01", periods=3),
        }
    )


@pytest.fixture
def valid_scored_df():
    return pd.DataFrame(
        {
            "prompt_id": ["P1", "P2", "P3"],
            "response": ["Response 1", "Response 2", "Response 3"],
            "overall_score": [4.5, 3.8, 2.1],
            "score_accuracy": [4.5, 4.0, 2.0],
            "grade": ["A", "B", "D"],
        }
    )


def test_validate_valid_dataframe(valid_raw_df):
    """Test validation of valid dataframe"""
    is_valid, issues = DataValidator.validate_dataframe(valid_raw_df, "raw_results")

    assert is_valid == True
    assert len(issues) == 0


def test_validate_empty_dataframe():
    """Test validation of empty dataframe"""
    empty_df = pd.DataFrame()
    is_valid, issues = DataValidator.validate_dataframe(empty_df)

    assert is_valid == False
    assert "Dataframe is empty" in issues[0]


def test_validate_missing_columns():
    """Test detection of missing columns"""
    df = pd.DataFrame({"prompt_id": ["P1"], "response": ["Response 1"]})

    is_valid, issues = DataValidator.validate_dataframe(df, "raw_results")

    assert is_valid == False
    assert any("Missing required columns" in issue for issue in issues)


def test_validate_duplicate_ids():
    """Test detection of duplicate prompt IDs"""
    df = pd.DataFrame(
        {
            "prompt_id": ["P1", "P1", "P2"],
            "prompt": ["A", "B", "C"],
            "response": ["X", "Y", "Z"],
            "timestamp": pd.date_range("2024-01-01", periods=3),
        }
    )

    is_valid, issues = DataValidator.validate_dataframe(df, "raw_results")

    assert is_valid == False
    assert any("Duplicate prompt IDs" in issue for issue in issues)


def test_validate_scores_out_of_range():
    """Test detection of scores outside valid range"""
    df = pd.DataFrame(
        {
            "prompt_id": ["P1", "P2"],
            "response": ["R1", "R2"],
            "overall_score": [6.0, -1.0],  # Invalid scores
            "score_accuracy": [6.0, -1.0],
            "grade": ["A", "F"],
        }
    )

    is_valid, issues = DataValidator.validate_dataframe(df, "scored_results")

    assert is_valid == False
    assert any("outside valid range" in issue for issue in issues)


def test_validate_invalid_grades():
    """Test detection of invalid grades"""
    df = pd.DataFrame(
        {
            "prompt_id": ["P1"],
            "response": ["R1"],
            "overall_score": [4.0],
            "grade": ["X"],  # Invalid grade
        }
    )

    is_valid, issues = DataValidator.validate_dataframe(df, "scored_results")

    assert is_valid == False
    assert any("Invalid grade values" in issue for issue in issues)


def test_validate_invalid_timestamp(monkeypatch):
    """Test detection of invalid timestamp formats"""
    df = pd.DataFrame({"prompt_id": ["P1"], "response": ["R1"], "timestamp": ["invalid_time"]})

    def mock_to_datetime(*args, **kwargs):
        raise ValueError("Mock datetime error")

    monkeypatch.setattr(pd, "to_datetime", mock_to_datetime)

    # Missing other columns will create issues, but we only check for timestamp issue
    is_valid, issues = DataValidator.validate_dataframe(df, "raw_results")

    assert is_valid == False
    assert any("Invalid timestamp format" in issue for issue in issues)


def test_clean_dataframe():
    """Test dataframe cleaning"""
    df = pd.DataFrame(
        {
            "prompt_id": [" P1 ", "P2", "P2"],  # Whitespace and duplicate
            "response": ["  R1  ", "R2", "R2"],
            "overall_score": [6.0, 3.0, 3.0],  # Out of range
            "grade": ["a", "B", "B"],  # Lowercase
        }
    )

    cleaned_df = DataValidator.clean_dataframe(df)

    # Check whitespace trimmed
    assert cleaned_df.loc[0, "prompt_id"] == "P1"

    # Check score clamped
    assert cleaned_df.loc[0, "overall_score"] == 5.0

    # Check grade uppercase
    assert cleaned_df.loc[0, "grade"] == "A"

    # Check duplicates removed
    assert len(cleaned_df) < len(df)


def test_generate_data_quality_report(valid_scored_df):
    """Test data quality report generation"""
    report = DataValidator.generate_data_quality_report(valid_scored_df)

    assert "total_rows" in report
    assert "total_columns" in report
    assert "columns" in report
    assert report["total_rows"] == 3

    # Check column info
    assert "overall_score" in report["columns"]
    assert "mean" in report["columns"]["overall_score"]


def test_check_grade_score_consistency(valid_scored_df):
    """Test grade-score consistency checking"""
    inconsistent = DataValidator._check_grade_score_consistency(valid_scored_df)

    # Should have no inconsistencies with valid data
    assert len(inconsistent) == 0


def test_clean_dataframe_invalid_score_range():
    df = pd.DataFrame({"overall_score": [1.0]})
    original_range = DataValidator.SCORE_RANGE
    DataValidator.SCORE_RANGE = "invalid"
    try:
        with pytest.raises(ValueError, match="SCORE_RANGE must be tuple"):
            DataValidator.clean_dataframe(df)
    finally:
        DataValidator.SCORE_RANGE = original_range


def test_clean_dataframe_trim_exception(caplog, monkeypatch):
    df = pd.DataFrame({"text_col": ["test"]})

    # Mock series.apply to raise TypeError
    def mock_apply(*args, **kwargs):
        raise TypeError("Mock error")

    monkeypatch.setattr(pd.Series, "apply", mock_apply)

    cleaned = DataValidator.clean_dataframe(df)
    assert "Could not trim column" in caplog.text


def test_clean_dataframe_clip_exception(monkeypatch):
    df = pd.DataFrame({"score_test": [1.0]})

    # Mock clip to raise ValueError
    def mock_clip(*args, **kwargs):
        raise ValueError("Mock error")

    monkeypatch.setattr(pd.Series, "clip", mock_clip)

    with pytest.raises(ValueError, match="Mock error"):
        DataValidator.clean_dataframe(df)


def test_clean_dataframe_empty_warning(caplog):
    df = pd.DataFrame()
    DataValidator.clean_dataframe(df)
    assert "Input DataFrame is empty" in caplog.text

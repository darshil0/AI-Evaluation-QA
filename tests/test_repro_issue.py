import pandas as pd

from scripts.data_validator import DataValidator


def test_repro():
    df = pd.DataFrame(
        {
            "prompt_id": [" P1 ", "P2", "P2"],
            "response": ["  R1  ", "R2", "R2"],
            "overall_score": [6.0, 3.0, 3.0],
            "grade": ["a", "B", "B"],
        }
    )
    print("Original df types:")
    print(df.dtypes)

    cleaned_df = DataValidator.clean_dataframe(df)
    print("\nCleaned df:")
    print(cleaned_df)
    print("\nCleaned prompt_id at 0:", repr(cleaned_df.loc[0, "prompt_id"]))

    assert cleaned_df.loc[0, "prompt_id"] == "P1"


if __name__ == "__main__":
    try:
        test_repro()
        print("\nTest passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")

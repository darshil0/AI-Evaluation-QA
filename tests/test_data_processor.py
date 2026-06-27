import os
import tempfile

import pandas as pd
import pytest

from evaluation.data_processor import DataProcessor


def test_process_large_csv():
    # Create a dummy CSV
    data = {"col1": [1, 2, 3, 4, 5], "col2": ["a", "b", "c", "d", "e"]}
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_csv = f.name

    def processing_func(chunk):
        chunk["col1"] = chunk["col1"] * 2
        return chunk

    try:
        output_csv = temp_csv.replace(".csv", "_processed.csv")
        result_df = DataProcessor.process_large_csv(
            temp_csv, processing_func, chunk_size=2, output_path=output_csv
        )

        assert len(result_df) == 5
        assert result_df["col1"].tolist() == [2, 4, 6, 8, 10]
        assert os.path.exists(output_csv)

        processed_df = pd.read_csv(output_csv)
        assert len(processed_df) == 5

    finally:
        os.unlink(temp_csv)
        if os.path.exists(output_csv):
            os.unlink(output_csv)


def test_stream_large_file():
    data = {"col1": range(10)}
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_csv = f.name

    try:
        chunks = list(DataProcessor.stream_large_file(temp_csv, chunk_size=3))
        assert len(chunks) == 4  # 3, 3, 3, 1
        assert len(chunks[0]) == 3
        assert len(chunks[-1]) == 1
    finally:
        os.unlink(temp_csv)


def test_estimate_memory_usage():
    df = pd.DataFrame({"col1": range(1000)})
    usage = DataProcessor.estimate_memory_usage(df)
    assert "bytes" in usage
    assert "megabytes" in usage
    assert usage["bytes"] > 0


def test_process_large_csv_error():
    with pytest.raises(FileNotFoundError):
        DataProcessor.process_large_csv("non_existent.csv", lambda x: x)

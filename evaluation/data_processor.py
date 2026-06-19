import logging
from typing import Callable, Dict, Iterator, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataProcessor:
    @staticmethod
    def process_large_csv(
        file_path: str,
        processing_func: Callable[[pd.DataFrame], pd.DataFrame],
        chunk_size: int = 1000,
        output_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """Process large CSV files in chunks to avoid memory issues"""

        logger.info(f"Processing {file_path} in chunks of {chunk_size}")

        chunks = []
        total_rows = 0

        try:
            # Process in chunks
            for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                logger.debug(f"Processing chunk {i+1}")

                processed_chunk = processing_func(chunk)
                chunks.append(processed_chunk)
                total_rows += len(processed_chunk)

            # Combine all chunks
            result_df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Processed {total_rows} total rows")

            # Save if output path provided
            if output_path:
                result_df.to_csv(output_path, index=False)
                logger.info(f"Saved results to {output_path}")

            return result_df

        except MemoryError:
            logger.error("Memory error during processing. Try smaller chunk_size.")
            raise
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    @staticmethod
    def stream_large_file(file_path: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream large CSV file without loading into memory"""
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            yield chunk

    @staticmethod
    def estimate_memory_usage(df: pd.DataFrame) -> Dict[str, float]:
        """Estimate memory usage of dataframe"""
        memory_bytes = df.memory_usage(deep=True).sum()

        return {
            "bytes": memory_bytes,
            "kilobytes": memory_bytes / 1024,
            "megabytes": memory_bytes / (1024**2),
            "gigabytes": memory_bytes / (1024**3),
        }

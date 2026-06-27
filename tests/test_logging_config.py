import logging

from config.logging_config import JsonFormatter, get_logger, setup_logging


def test_json_formatter():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="test message",
        args=None,
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "test message" in formatted
    assert "INFO" in formatted

    try:
        raise ValueError("test exception")
    except ValueError:
        import sys

        record.exc_info = sys.exc_info()

    formatted_with_exc = formatter.format(record)
    assert "test exception" in formatted_with_exc

    record.extra_data = {"key": "value"}
    formatted_with_extra = formatter.format(record)
    assert '"key": "value"' in formatted_with_extra


def test_setup_logging(tmp_path):
    log_dir = tmp_path / "logs"
    log_file = "test.log"

    logger = setup_logging(log_level="DEBUG", log_file=log_file, log_dir=str(log_dir))
    assert logger.level == logging.DEBUG
    assert (log_dir / log_file).exists()

    logger = setup_logging(log_level="INFO", log_dir=str(log_dir), enable_json_logging=True)
    jsonl_files = list(log_dir.glob("structured_*.jsonl"))
    assert len(jsonl_files) > 0


def test_get_logger():
    logger = get_logger("test_module")
    assert logger.name == "test_module"

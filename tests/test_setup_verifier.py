from unittest.mock import patch

from scripts.setup_verifier import verify_setup


def test_verify_setup_success():
    with (
        patch("scripts.setup_verifier.Path") as mock_path,
        patch("scripts.setup_verifier.os.getenv") as mock_getenv,
    ):

        mock_path.return_value.exists.return_value = True
        mock_getenv.return_value = "fake-key"

        assert verify_setup() is True


def test_verify_setup_failure():
    with (
        patch("scripts.setup_verifier.Path") as mock_path,
        patch("scripts.setup_verifier.os.getenv") as mock_getenv,
    ):

        mock_path.return_value.exists.return_value = False
        mock_getenv.return_value = None

        assert verify_setup() is False


def test_verify_setup_exception():
    with patch("scripts.setup_verifier.Path") as mock_path:
        mock_path.side_effect = Exception("error")
        assert verify_setup() is False

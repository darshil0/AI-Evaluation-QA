"""
Compatibility tests for legacy API support.
"""

import os
import tempfile
import warnings
import pytest
from evaluation.prompt_runner import PromptRunner

def test_save_responses_legacy_format_param():
    """Test that the legacy 'format' parameter still works with a warning."""
    runner = PromptRunner()
    results = [{"a": 1}]

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "test.csv")

        with pytest.warns(DeprecationWarning, match="use 'file_format' instead"):
            # Ensure it correctly handles the 'format' kwarg
            runner.save_responses(results, output_file, format="csv")

        assert os.path.exists(output_file), "File should be created using legacy 'format' param"

        # Verify it also works with the new 'file_format' param without warning
        output_file_new = os.path.join(tmp_dir, "test_new.csv")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            runner.save_responses(results, output_file_new, file_format="csv")
            # We filter for our specific warning as other libraries might trigger some
            relevant_warnings = [warn for warn in w if "use 'file_format' instead" in str(warn.message)]
            assert len(relevant_warnings) == 0, "New param should not trigger DeprecationWarning"

        assert os.path.exists(output_file_new)

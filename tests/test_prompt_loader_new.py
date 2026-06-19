import json
import os
import tempfile

import pytest

from scripts.prompt_loader import PromptLoader


def test_prompt_loader_no_schema():
    loader = PromptLoader()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"test": "data"}, f)
        temp_file = f.name

    try:
        data = loader.load_and_validate(temp_file)
        assert data == {"test": "data"}
    finally:
        os.unlink(temp_file)


def test_prompt_loader_with_schema():
    schema = {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
        json.dump(schema, sf)
        schema_file = sf.name

    loader = PromptLoader(schema_file)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"id": "p1"}, f)
        valid_file = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"no_id": "data"}, f)
        invalid_file = f.name

    try:
        assert loader.load_and_validate(valid_file) == {"id": "p1"}
        with pytest.raises(ValueError, match="Schema validation failed"):
            loader.load_and_validate(invalid_file)
    finally:
        os.unlink(schema_file)
        os.unlink(valid_file)
        os.unlink(invalid_file)


def test_prompt_loader_file_not_found():
    loader = PromptLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_and_validate("non_existent.json")

import json
import os
from typing import Any, Dict, Optional

from jsonschema import ValidationError, validate


class PromptLoader:
    def __init__(self, schema_path: Optional[str] = None):
        if schema_path and os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)
        else:
            self.schema = None

    def load_and_validate(self, filepath: str) -> Dict[str, Any]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                f"Prompt file {filepath} must contain a JSON object"
            )  # pragma: no cover

        if self.schema:
            try:
                validate(instance=data, schema=self.schema)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed: {e.message}")

        return data

import json
import os

from jsonschema import ValidationError, validate


class PromptLoader:
    def __init__(self, schema_path=None):
        if schema_path and os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                self.schema = json.load(f)
        else:
            self.schema = None

    def load_and_validate(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        if self.schema:
            try:
                validate(instance=data, schema=self.schema)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed: {e.message}")

        return data

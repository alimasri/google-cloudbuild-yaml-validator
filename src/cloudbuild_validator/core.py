from pathlib import Path
from typing import Any, Dict, List, Union

import yamale

from cloudbuild_validator import validators


class CloudBuildValidator:
    def __init__(
        self, schema_file: Path | str | None = None, add_default_validators: bool = True
    ):
        self.validators = []
        self.schema = None
        if schema_file is not None:
            self.schema = yamale.make_schema(schema_file)
        if add_default_validators:
            for validator in dir(validators):
                if (
                    isinstance(getattr(validators, validator), type)
                    and issubclass(getattr(validators, validator), validators.Validator)
                    and getattr(validators, validator) != validators.Validator
                ):
                    self.add_validator(getattr(validators, validator)())

    def add_validator(self, validator: validators.Validator):
        self.validators.append(validator)

    def remove_validator(self, validator: validators.Validator):
        self.validators.remove(validator)

    def validate_file(self, yaml_file_path: Path) -> List[str]:
        if not self.schema:
            raise ValueError("No schema provided for validation")

        yamale_data = yamale.make_data(yaml_file_path)
        if len(yamale_data) > 1:
            raise validators.CloudBuildValidationError(
                "Multiple documents found in the file"
            )

        content = yamale_data[0][0]

        return self.validate(content, yamale_data)

    def validate(
        self, content: Dict[str, Any], yamale_data: List | None = None
    ) -> List[str]:
        if not self.schema:
            raise ValueError("No schema provided for validation")

        errors = []

        if yamale_data is not None:
            try:
                yamale.validate(self.schema, yamale_data)
            except yamale.YamaleError as e:
                for result in e.results:
                    errors.extend(result.errors)
                return errors

        for validator in self.validators:
            try:
                validator.validate(content)
            except validators.CloudBuildValidationError as e:
                errors.append(str(e))
        return errors

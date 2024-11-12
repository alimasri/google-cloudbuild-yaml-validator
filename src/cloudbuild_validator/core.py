from pathlib import Path
from typing import List

import yamale

from cloudbuild_validator import validators


class CloudBuildValidator:
    def __init__(self, speficifactions_file: Path, add_default_validators: bool = True):
        self.validators = []
        self.schema = yamale.make_schema(speficifactions_file)
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

    def validate(self, yaml_file_path: Path) -> List[str]:
        content = yamale.make_data(yaml_file_path)
        if len(content) > 1:
            raise validators.CloudBuildValidationError(
                "Multiple documents found in the file"
            )
        try:
            yamale.validate(self.schema, content)
        except yamale.YamaleError as e:
            errors = []
            for result in e.results:
                errors.extend(result.errors)
            return errors

        content = content[0][0]

        errors = []
        for validator in self.validators:
            try:
                validator.validate(content)
            except validators.CloudBuildValidationError as e:
                errors.append(str(e))
        return errors

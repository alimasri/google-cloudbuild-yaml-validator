import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import List

from cloudbuild_validator.config import settings


class Validator(ABC):
    @abstractmethod
    def validate(self, yaml_file_content: str) -> List[str]: ...


class CloudBuildValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DuplicateStepIdsValidator(Validator):
    """Check for duplicate step ids in the content"""

    def validate(self, content: dict) -> None:
        step_ids = [step["id"] for step in content["steps"]]
        counter = Counter(step_ids)
        duplicates = {step_id for step_id, count in counter.items() if count > 1}
        if duplicates:
            raise CloudBuildValidationError(f"Duplicate step ids found: {step_ids}")


class InvalidDependenciesValidator(Validator):
    """Check for invalid step ids in waitFor"""

    def validate(self, content: dict) -> None:
        all_step_ids = {step["id"] for step in content["steps"]}
        for step in content["steps"]:
            wait_for = step.get("waitFor", [])
            if not wait_for:
                continue
            for step_id in wait_for:
                if step_id == "-":
                    continue
                if step_id not in all_step_ids:
                    raise CloudBuildValidationError(
                        f"Invalid step id `{step_id}` in `waitFor` for step `{step['id']}`"
                    )


class SubstitutionVariablesValidator(Validator):
    """Check for substitution variable errors"""

    def validate(self, content: dict) -> None:
        substitution = content.get("substitutions", {})
        for variable in substitution:
            if not variable.startswith("_") or not variable.isupper():
                raise CloudBuildValidationError(
                    f"Substitution variable `{variable}` must start with `_` and be uppercase"
                )

        pattern = re.compile(settings.SUBSTITUTION_VARIABLE_PATTERN)
        for step in content["steps"]:
            args = step.get("args", [])
            if not args:
                continue
            for arg in args:
                for match in pattern.finditer(arg):
                    variable = match.group(1)
                    if (
                        variable not in substitution
                        and variable not in settings.DEFAULT_SUBSTITUTIONS
                    ):
                        raise CloudBuildValidationError(
                            f"Undefined substitution variable {variable} in step `{step['id']}`"
                        )


class UndefinedSecretsValidator(Validator):
    """Check for undefined secrets in the content"""

    def validate(self, content: dict) -> None:
        secrets = content.get("availableSecrets", [])
        if not secrets:
            all_secrets = set()
        else:
            all_secrets = {
                secret.get("env")
                for secret_store in secrets.values()
                for secret in secret_store
            }

        errors = []
        for step in content["steps"]:
            step_secrets = step.get("secretEnv", [])
            if not step_secrets:
                continue
            for secret in step_secrets:
                if secret not in all_secrets:
                    errors.append(f"Undefined secret `{secret}` in step `{step['id']}`")
        if errors:
            raise CloudBuildValidationError("\n".join(errors))


class UnusedSecretsValidator(Validator):
    """Check for unused secrets in the content"""

    def validate(self, content: dict) -> None:
        secrets = content.get("availableSecrets", [])
        if not secrets:
            return
        all_secrets = {
            secret.get("env")
            for secret_store in secrets.values()
            for secret in secret_store
        }

        for step in content["steps"]:
            step_secrets = step.get("secretEnv", [])
            if not step_secrets:
                continue
            for secret in step_secrets:
                all_secrets.discard(secret)

        if all_secrets:
            raise CloudBuildValidationError(
                f"Secret(s) {all_secrets} are defined but not used"
            )

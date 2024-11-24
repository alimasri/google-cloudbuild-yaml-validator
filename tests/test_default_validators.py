import pytest

from cloudbuild_validator import validators
from cloudbuild_validator.validators import CloudBuildValidationError


def test_check_duplicate_step_ids():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2"},
            {"id": "step1"},
        ]
    }
    with pytest.raises(CloudBuildValidationError):
        validators.DuplicateStepIdsValidator().validate(content)


def test_check_duplicate_step_ids_no_duplicates():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2"},
            {"id": "step3"},
        ]
    }
    validators.DuplicateStepIdsValidator().validate(content)


def test_check_invalid_dependencies():
    content = {
        "steps": [
            {"id": "step1", "waitFor": ["step4"]},
            {"id": "step2", "waitFor": ["step3"]},
            {"id": "step3", "waitFor": ["step1"]},
        ]
    }
    with pytest.raises(CloudBuildValidationError):
        validators.InvalidDependenciesValidator().validate(content)


def test_check_invalid_dependencies_no_invalid():
    content = {
        "steps": [
            {"id": "step1", "waitFor": ["-"]},
            {"id": "step2"},
            {"id": "step3", "waitFor": ["step1"]},
        ]
    }
    validators.InvalidDependenciesValidator().validate(content)


def test_check_invalid_dependencies_no_wait_for():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2"},
            {"id": "step3"},
        ]
    }
    validators.InvalidDependenciesValidator().validate(content)


def test_invalid_subsitution_variables():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2", "args": ["--project=${_NOT_DEFINED}"]},
        ]
    }
    with pytest.raises(CloudBuildValidationError):
        validators.SubstitutionVariablesValidator().validate(content)


def test_invalid_subsitution_variables_no_invalid():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2", "args": ["--var=${_DEFINED_VAR}"]},
        ],
        "substitutions": {"_DEFINED_VAR": "defined_value"},
    }

    validators.SubstitutionVariablesValidator().validate(content)


def test_invalid_substitution_variables_default_substitution():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2", "args": ["--var=${SHORT_SHA}"]},
        ],
    }

    validators.SubstitutionVariablesValidator().validate(content)


def test_invalid_substitution_variable_names():
    content = {
        "substitutions": {
            "not_uppercase": "value",
            "not_starting_with_": "value",
        }
    }
    with pytest.raises(CloudBuildValidationError):
        validators.SubstitutionVariablesValidator().validate(content)


def test_undefined_secret_undefined():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2", "secretEnv": ["SECRET"]},
        ],
    }
    with pytest.raises(CloudBuildValidationError):
        validators.UndefinedSecretsValidator().validate(content)


def test_unsed_secret_defined():
    content = {
        "steps": [
            {"id": "step1", "secretEnv": ["SECRET"]},
            {"id": "step2"},
        ],
        "availableSecrets": {
            "secretManager": [{"env": "SECRET"}],
        },
    }
    validators.UndefinedSecretsValidator().validate(content)


def test_unsed_secret_unused():
    content = {
        "steps": [
            {"id": "step1"},
            {"id": "step2"},
        ],
        "availableSecrets": {
            "secretManager": [{"env": "SECRET"}],
        },
    }
    with pytest.raises(CloudBuildValidationError):
        validators.UnusedSecretsValidator().validate(content)


def test_unsed_secret_used():
    content = {
        "steps": [
            {"id": "step1", "secretEnv": ["SECRET"]},
            {"id": "step2"},
        ],
        "availableSecrets": {
            "secretManager": [{"env": "SECRET"}],
        },
    }
    validators.UnusedSecretsValidator().validate(content)

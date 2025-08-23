from typing import List

import pytest

from cloudbuild_validator import validators
from cloudbuild_validator.core import CloudBuildValidator
from cloudbuild_validator.validators import Validator


@pytest.fixture(scope="module")
def fake_validator():
    class FakeValidator(Validator):
        def validate(self, yaml_file_content: str) -> List[str]:
            return []

    return FakeValidator()


@pytest.fixture(scope="module")
def valid_yaml_content():
    return """
    steps:
      - id: step1
        name: "gcr.io/cloud-builders/gcloud"
        args: ["projects", "list"]
    options:
        workerPool: "default-pool"
    serviceAccount: "email@project-id.iam.gserviceaccount.com"
    """


@pytest.fixture(scope="module")
def valid_yaml_invalid_rules_content():
    return """
    steps:
      - id: step1
        name: "gcr.io/cloud-builders/gcloud"
        args: ["projects", "list"]
        waitFor: ["step2"]
    options:
        workerPool: "default-pool"
    serviceAccount: "email@project-id.iam.gserviceaccount.com"
    """


@pytest.fixture(scope="module")
def invalid_yaml_content():
    return """
    steps:
      - id: step1
        name: "gcr.io/cloud-builders/gcloud"
        workerPool: "default-pool"
    """


@pytest.fixture(scope="module")
def temp_file_factory(tmp_path_factory):
    def _factory(content: str, filename: str):
        tmpdir = tmp_path_factory.mktemp("data")
        file_path = tmpdir / filename
        with open(file_path, "w") as f:
            f.write(content)
        return str(file_path.absolute().as_posix())

    return _factory


@pytest.fixture(scope="module")
def valid_yaml_path(temp_file_factory, valid_yaml_content):
    return temp_file_factory(valid_yaml_content, "valid.yaml")


@pytest.fixture(scope="module")
def invalid_yaml_path(temp_file_factory, invalid_yaml_content):
    return temp_file_factory(invalid_yaml_content, "invalid.yaml")


@pytest.fixture(scope="module")
def valid_yaml_invalid_rules_path(temp_file_factory, valid_yaml_invalid_rules_content):
    return temp_file_factory(
        valid_yaml_invalid_rules_content, "valid_invalid_rules.yaml"
    )


@pytest.fixture(scope="module")
def multiple_documents_yaml_path(temp_file_factory):
    content = """foo: bar\n---\nbaz: qux\n"""
    return temp_file_factory(content, "multiple_documents.yaml")


@pytest.fixture(scope="module")
def valid_specifications_path(temp_file_factory):
    specifications = """
steps: list(include('Step'), min=1)
timeout: str(required=False)
queueTtl: str(required=False)
logsBucket: str(required=False)
options:
  env: list(str(), required=False)
  secretEnv: str(required=False)
  volumes: include('Volume', required=False)
  sourceProvenanceHash: enum('MD5', 'SHA256', 'SHA1', required=False)
  machineType: enum('UNSPECIFIED', 'N1_HIGHCPU_8', 'N1_HIGHCPU_32', 'E2_HIGHCPU_8', 'E2_HIGHCPU_32', required=False)
  diskSizeGb: int(required=False)
  substitutionOption: enum('MUST_MATCH', 'ALLOW_LOOSE', required=False)
  dynamicSubstitutions: bool(required=False)
  automapSubstitutions: bool(required=False)
  logStreamingOption: enum('STREAM_DEFAULT', 'STREAM_ON', 'STREAM_OFF', required=False)
  logging: enum('GCS_ONLY', 'CLOUD_LOGGING_ONLY', required=False)
  defaultLogsBucketBehavior: str(required=False)
  pool: map(required=False)
  requestedVerifyOption: enum('NOT_VERIFIED', 'VERIFIED', required=False)
  workerPool: str(required=True)
substitutions: map(str(), str(), required=False)
tags: list(str(), required=False)
serviceAccount: str()
secrets: map(required=False)
availableSecrets: map(required=False)
artifacts: include('Artifact', required=False)
images: list(list(str()), required=False)
---
Artifact:
  mavenArtifacts: list(map(), required=False)
  pythonPackages: list(map(), required=False)
  npmPackages: list(map(), required=False)
Volume: list(map(name=str(), path=str()), required=False)
TimeSpan:
  startTime: str()
  endTime: str()
Step:
  name: str()
  args: list(str(), required=False)
  env: list(str(), required=False)
  allowFailure: bool(required=False)
  dir: str(required=False)
  id: str()
  waitFor: list(str(), required=False)
  entrypoint: str(required=False)
  secretEnv: list(str(), required=False)
  volumes: include('Volume', required=False)
  timeout: str(required=False)
  script: str(required=False)
  automapSubstitutions: bool(required=False)
    """
    return temp_file_factory(specifications, "cloudbuild-specifications.yaml")


@pytest.mark.dependency()
def test_no_default_validators():
    validator = CloudBuildValidator(schema_file=None, add_default_validators=False)
    assert len(validator.validators) == 0


@pytest.mark.dependency(depends=["test_no_default_validators"])
def test_add_validator(fake_validator):
    validator = CloudBuildValidator(schema_file=None, add_default_validators=False)
    assert len(validator.validators) == 0
    validator.add_validator(fake_validator)
    assert len(validator.validators) == 1
    assert validator.validators[0] == fake_validator


def test_default_validators_added():
    validator = CloudBuildValidator(None)
    assert len(validator.validators) > 0


@pytest.mark.dependency(depends=["test_add_validator"])
def test_remove_validators(fake_validator):
    validator = CloudBuildValidator(None, add_default_validators=False)
    validator.add_validator(fake_validator)
    assert len(validator.validators) == 1
    validator.remove_validator(fake_validator)
    assert len(validator.validators) == 0


def test_validate_valid_yaml(valid_specifications_path, valid_yaml_path):
    validator = CloudBuildValidator(schema_file=valid_specifications_path)
    assert validator.validate_file(valid_yaml_path) == []


def test_validate_valid_yaml_invalid_rules(
    valid_specifications_path, valid_yaml_invalid_rules_path
):
    validator = CloudBuildValidator(schema_file=valid_specifications_path)
    errors = validator.validate_file(valid_yaml_invalid_rules_path)
    assert len(errors) >= 1


def test_invalid_yaml(valid_specifications_path, invalid_yaml_path):
    validator = CloudBuildValidator(schema_file=valid_specifications_path)
    errors = validator.validate_file(invalid_yaml_path)
    assert len(errors) > 0


def test_multiple_documents_in_yaml(
    valid_specifications_path, multiple_documents_yaml_path
):
    with pytest.raises(validators.CloudBuildValidationError) as e:
        validator = CloudBuildValidator(schema_file=valid_specifications_path)
        validator.validate_file(multiple_documents_yaml_path)
    assert "Multiple documents found in the file" in str(e.value)


def test_validate_content_directly(valid_specifications_path):
    validator = CloudBuildValidator(schema_file=valid_specifications_path)
    content = {
        "steps": [
            {
                "id": "step1",
                "name": "gcr.io/cloud-builders/gcloud",
                "args": ["projects", "list"],
            }
        ],
        "options": {"workerPool": "default-pool"},
        "serviceAccount": "email@project-id.iam.gserviceaccount.com",
    }
    errors = validator.validate(content)
    assert errors == []


def test_validate_content_with_validation_errors(valid_specifications_path):
    validator = CloudBuildValidator(schema_file=valid_specifications_path)
    content = {
        "steps": [
            {
                "id": "step1",
                "name": "gcr.io/cloud-builders/gcloud",
                "args": ["projects", "list"],
                "waitFor": ["step2"],  # This will cause a validation error
            }
        ],
        "options": {"workerPool": "default-pool"},
        "serviceAccount": "email@project-id.iam.gserviceaccount.com",
    }
    errors = validator.validate(content)
    assert len(errors) >= 1

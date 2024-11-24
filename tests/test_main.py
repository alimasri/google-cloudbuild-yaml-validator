from pathlib import Path
from typing import List

import pytest

from cloudbuild_validator import validators
from cloudbuild_validator.core import CloudBuildValidator
from cloudbuild_validator.validators import Validator


@pytest.fixture
def fake_validator():
    class FakeValidator(Validator):
        def validate(self, _: str) -> List[str]:
            pass

    return FakeValidator()


@pytest.fixture
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


@pytest.fixture
def valid_yaml_invalid_rules_content(tmpdir):
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


@pytest.fixture
def invalid_yaml_content(tmpdir):
    return """
    steps:
      - id: step1
        name: "gcr.io/cloud-builders/gcloud"
        workerPool: "default-pool"
    """


@pytest.fixture
def valid_yaml_path(tmpdir, valid_yaml_content):
    with open(tmpdir / "valid.yaml", "w") as f:
        f.write(valid_yaml_content)
    yield Path(tmpdir / "valid.yaml")


@pytest.fixture
def invalid_yaml_path(tmpdir, invalid_yaml_content):
    with open(tmpdir / "invalid.yaml", "w") as f:
        f.write(invalid_yaml_content)
    yield Path(tmpdir / "invalid.yaml")


@pytest.fixture
def valid_yaml_invalid_rules_path(tmpdir, valid_yaml_invalid_rules_content):
    with open(tmpdir / "valid_invalid_rules.yaml", "w") as f:
        f.write(valid_yaml_invalid_rules_content)
    yield Path(tmpdir / "valid_invalid_rules.yaml")


@pytest.fixture
def multiple_documents_yaml_path(tmpdir):
    content = """\
foo: bar
---
baz: qux
    """
    with open(tmpdir / "multiple_documents.yaml", "w") as f:
        f.write(content)
    yield Path(tmpdir / "multiple_documents.yaml")


@pytest.fixture
def valid_specifications_path(tmpdir):
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
    with open(tmpdir / "schema.yaml", "w") as f:
        f.write(specifications)
    yield Path(tmpdir / "schema.yaml")


def test_add_validator(monkeypatch, fake_validator):
    monkeypatch.setattr("cloudbuild_validator.core.yamale.make_schema", lambda x: None)
    validator = CloudBuildValidator(None, add_default_validators=False)
    assert len(validator.validators) == 0
    validator.add_validator(fake_validator)
    assert len(validator.validators) == 1
    assert validator.validators[0] == fake_validator


def test_default_validators_added(monkeypatch):
    monkeypatch.setattr("cloudbuild_validator.core.yamale.make_schema", lambda x: None)
    validator = CloudBuildValidator(None)
    assert len(validator.validators) > 0


def test_remove_validators(monkeypatch, fake_validator):
    monkeypatch.setattr("cloudbuild_validator.core.yamale.make_schema", lambda x: None)
    validator = CloudBuildValidator(None, add_default_validators=False)
    validator.add_validator(fake_validator)
    assert len(validator.validators) == 1
    validator.remove_validator(fake_validator)
    assert len(validator.validators) == 0


def test_validate_valid_yaml(valid_specifications_path, valid_yaml_path):
    validator = CloudBuildValidator(valid_specifications_path)
    assert validator.validate(valid_yaml_path) == []


def test_validate_valid_yaml_invalid_rules(
    valid_specifications_path, valid_yaml_invalid_rules_path
):
    validator = CloudBuildValidator(valid_specifications_path)
    errors = validator.validate(valid_yaml_invalid_rules_path)
    assert len(errors) >= 1


def test_invalid_yaml(valid_specifications_path, invalid_yaml_path):
    validator = CloudBuildValidator(valid_specifications_path)
    errors = validator.validate(invalid_yaml_path)
    assert len(errors) > 0


def test_multiple_documents_in_yaml(
    valid_specifications_path, multiple_documents_yaml_path
):
    with pytest.raises(validators.CloudBuildValidationError) as e:
        validator = CloudBuildValidator(valid_specifications_path)
        validator.validate(multiple_documents_yaml_path)
    assert "Multiple documents found in the file" in str(e.value)

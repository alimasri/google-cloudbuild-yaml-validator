# Google Cloud Build YAML Validator

A robust and extensible tool for validating Google Cloud Build YAML configuration files against [schema specifications](https://cloud.google.com/build/docs/build-config-file-schema) and custom rules.
By providing a comprehensive set of validation checks and the ability to extend its functionality, this program helps ensure the correctness and consistency of your Cloud Build configuration files, potentially saving time and resources in your CI/CD pipeline

## Features

The Cloud Build YAML Validator performs comprehensive checks on your configuration files:

- **YAML Syntax**: Ensures the file is a valid YAML document.
- **Schema Compliance**: Validates the YAML structure against Cloud Build specifications.
- **Duplicate Step IDs**: Identifies duplicate step IDs within the configuration file.
- **Step Dependencies**: Verifies that all `waitFor` references point to valid step IDs.
- **Substitution Variables**: Checks for unreferenced substitution variables and ensures they start with an underscore (`_`).
- **Custom Validations**: Easily extendable with additional custom validation rules.

## Installation

You can install the Cloud Build YAML Validator using `pip`, `uv`, or your preferred Python package manager:

```bash
git clone https://github.com/alimasri/google-cloudbuild-yaml-validator
cd google-cloudbuild-yaml-validator
pip install -e .
```

## Usage

### Command Line Interface

The validator can be run from the command line with the following syntax:

```bash
usage: cloudbuild-validator [-h] [-s SCHEMA] file

positional arguments:
  file                  Path to the content file to validate

options:
  -h, --help            show this help message and exit
  -s SCHEMA, --schema SCHEMA
                        Path to the schema file to validate against
```

### Example

```bash
cloudbuild-validator /path/to/cloudbuild.yaml
```

### Programmatic Usage

You can also use the validator as a Python library:

```python
from cloudbuild_validator.core import CloudbuildValidator

validator = CloudbuildValidator(speficifactions_file="/path/to/specifications/file.yaml")
validator.validate_file('/path/to/cloudbuild.yaml')
```

## Specifications

The validator enforces schema specifications for Google Cloud Build YAML configuration files, based on the official Cloud Build documentation. Users can provide a custom schema file using the `-s` or `--schema` option. The default schema file is located at `src/cloudbuild_validator/data/cloudbuild-specifcations.yaml`, which can be used as a reference for creating custom schemas.

By adhering to this schema, users ensure their Cloud Build configuration files are valid and correctly interpreted by the Cloud Build service. Example modifications could include adding organization-specific patterns for image names, environment variables, or other configuration options.

## Extending the Validator

### Adding New Validations

#### Method 1: Extending the default validations

The validator automatically discovers and executes all `Validator` subclasses in the `validators.py` file. To add a new validation rule:

1. Create a new class that inherits from `cloudbuild_validator.validators.Validator`
2. Implement the `validate` method

The `validate` method should accept a dictionary representing the Cloud Build configuration file and raise a `cloudbuild_validator.exceptions.CloudBuildValidationError` if the validation fails.

##### Example

```python
class StepIdPrefixValidator(Validator):
    """Ensures that step IDs start with a specific prefix."""
    
    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    def validate(self, content: dict) -> None:
        for step in content.get('steps', []):
            step_id = step.get('id', '')
            if not step_id.startswith(self.prefix):
                raise CloudBuildValidationError(f"Step ID '{step_id}' does not start with the expected prefix '{self.prefix}'.")
```

#### Method 2: Using the `add_validator` method

The `CloudbuildValidator` class provides an `add_validator` method that allows users to add custom validation rules. This method accepts a `Validator` subclass and adds it to the list of validators that will be executed during the validation process.

##### Example

```python
from cloudbuild_validator import CloudbuildValidator
from cloudbuild_validator.validators import Validator

class CustomValidator(Validator):
    def validate(self, content: dict) -> None:
        # Custom validation logic here
        pass

validator = CloudbuildValidator()
validator.add_validator(CustomValidator())
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for more information.

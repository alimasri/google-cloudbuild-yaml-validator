from argparse import ArgumentParser
from pathlib import Path

from loguru import logger

from cloudbuild_validator.core import CloudBuildValidator


def main(schema: Path, content: Path):
    logger.info("Program started")

    logger.info(f"Validating {content} against {schema}...")
    validator = CloudBuildValidator(schema)
    errors = validator.validate(content)
    if not errors:
        logger.info("Validation passed")
        raise SystemExit(0)

    logger.error("Validation failed")
    for error_msg in errors:
        logger.error(f"\t{error_msg}")

    raise SystemExit(1)


def run():
    default_schema = Path(__file__).parent / "data" / "cloudbuild-specifications.yaml"
    parser = ArgumentParser()
    parser.add_argument(
        "-s",
        "--schema",
        type=Path,
        help="Path to the schema file to validate against",
        required=False,
        default=default_schema,
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to the content file to validate",
        required=True,
    )
    args = parser.parse_args()
    main(args.schema, args.file)


if __name__ == "__main__":
    run()

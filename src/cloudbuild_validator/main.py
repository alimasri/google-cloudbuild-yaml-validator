from argparse import ArgumentParser
from pathlib import Path

from loguru import logger

from cloudbuild_validator.core import CloudBuildValidator


def main(schema: Path, content: Path):
    log_prefix = f"[{content.name}]"
    logger.info(f"{log_prefix} validating...")
    validator = CloudBuildValidator(schema)
    errors = validator.validate(content)
    if not errors:
        logger.info(f"{log_prefix} passed")
        raise SystemExit(0)

    logger.error(f"{log_prefix} failed")
    for error_msg in errors:
        logger.error(f"\t{error_msg}")

    raise SystemExit(1)


def run():
    default_schema = Path(__file__).parent / "data" / "cloudbuild-specifications.yaml"
    parser = ArgumentParser()
    parser.add_argument(
        "file",
        type=Path,
        help="Path to the content file to validate",
    )
    parser.add_argument(
        "-s",
        "--schema",
        type=Path,
        help="Path to the schema file to validate against",
        required=False,
        default=default_schema,
    )
    args = parser.parse_args()
    main(args.schema, args.file)


if __name__ == "__main__":
    run()

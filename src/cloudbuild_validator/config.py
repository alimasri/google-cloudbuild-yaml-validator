from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEFAULT_SUBSTITUTIONS: list[str] = [
        "PROJECT_ID",
        "BUILD_ID",
        "PROJECT_NUMBER",
        "LOCATION",
        "TRIGGER_NAME",
        "COMMIT_SHA",
        "REVISION_ID",
        "SHORT_SHA",
        "REPO_NAME",
        "REPO_FULL_NAME",
        "BRANCH_NAME",
        "TAG_NAME",
        "REF_NAME",
        "TRIGGER_BUILD_CONFIG_PATH",
        "SERVICE_ACCOUNT_EMAIL",
        "SERVICE_ACCOUNT",
        "_HEAD_BRANCH",
        "_BASE_BRANCH",
        "_HEAD_REPO_URL",
        "_PR_NUMBER",
    ]

    SUBSTITUTION_VARIABLE_PATTERN: str = r"\$\{(_\w+)\}"


settings = Settings()

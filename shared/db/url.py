import os


def build_database_url() -> str:
    postgres_user = os.environ["POSTGRES_USER"]
    postgres_password = os.environ["POSTGRES_PASSWORD"]
    postgres_db = os.environ["POSTGRES_DB"]
    postgres_host = os.environ.get("POSTGRES_HOST", "postgres")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")

    return (
        f"postgresql+psycopg://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}"
    )

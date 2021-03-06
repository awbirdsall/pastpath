from functools import lru_cache

from pydantic import BaseSettings

# Subclassing from BaseSettings allows reading from env vars, see
# https://pydantic-docs.helpmanual.io/usage/settings and
# https://github.com/tiangolo/fastapi/issues/508#issuecomment-532360198
class AppSettings(BaseSettings):
    host: str = "localhost"
    db_name: str = "marker_db"
    port: int = 5432


# TODO refactor into single AppSettings
class InstanceSettings(BaseSettings):
    sql_user: str
    sql_key: str
    ors_key: str


@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache()
def get_instance_settings() -> InstanceSettings:
    return InstanceSettings()


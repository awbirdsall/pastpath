from functools import lru_cache

from pydantic import BaseSettings

# https://github.com/tiangolo/fastapi/issues/508#issuecomment-532360198
class AppSettings(BaseSettings):
    host: str
    db_name: str
    port: str

    class Config:
        env_file = 'config.py'

class InstanceSettings(BaseSettings):
    sql_user: str
    sql_key: str
    ors_key: str

    class Config:
        env_file = 'instance/config.py'

@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()

@lru_cache()
def get_instance_settings() -> InstanceSettings:
    return InstanceSettings()


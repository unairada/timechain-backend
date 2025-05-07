from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    blast_rpc_url : AnyHttpUrl 
    model_config = SettingsConfigDict(env_file='variables.env', env_file_encoding='utf-8')

settings = Settings()
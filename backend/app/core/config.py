"""应用配置 — 从环境变量加载，支持 .env 文件"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置单例"""

    # 应用
    APP_NAME: str = "习题知识点标注智能体"
    DEBUG: bool = True

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # SQLite
    SQLITE_PATH: str = "data/app.db"
    CHROMA_PATH: str = "data/chroma"

    # 大模型（开发阶段默认值，后续通过配置页管理）
    LLM_PROVIDER: str = "deepseek"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# import os

# class DatabaseConfig:
#     BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
#     DB_PATH = os.path.join(BASE_DIR, "app.db")

# db_config = DatabaseConfig()

import os
from src.utils import utils

class DatabaseConfig:
    _direct_url = utils.DIRECT_DATABASE_URL or utils.DATABASE_URL

    PG_CONN = (
        _direct_url
        .replace("postgresql+psycopg://", "postgresql://")
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("&channel_binding=require", "")
        .replace("?channel_binding=require", "")
    )

db_config = DatabaseConfig()
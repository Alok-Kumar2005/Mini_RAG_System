import os

class DatabaseConfig:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    DB_PATH = os.path.join(BASE_DIR, "app.db")

db_config = DatabaseConfig()
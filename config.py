import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "campusgo")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "campusgo-clave-secreta-cambiar")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

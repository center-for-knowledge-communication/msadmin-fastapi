from curses import echo
from sqlite3 import connect
from sqlalchemy import text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker
import os
import dotenv
import json

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Doudou0619@127.0.0.1:3306/wayangoutpostdb"
DB_TYPE = "mysql"
DB_INTERFACE = "pymysql"
DB_ADDRESS = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "mytestdb"
DB_USERNAME = "root"
DB_PASSWORD = "Doudou0619"
SQLALCHEMY_DATABASE_URL = f"{DB_TYPE}+{DB_INTERFACE}://{DB_USERNAME}:{DB_PASSWORD}@{DB_ADDRESS}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBContext:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

# result = engine.execute(
#     text(
#         "SELECT * FROM auth_user LIMIT 5;"
#     )
# )
# print(f"Selected {result.rowcount} rows.")
# for row in result.fetchall():
#     print(row)
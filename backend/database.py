import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



load_dotenv()

DB_URL = os.getenv(
	"DB_URL",
	"mysql+pymysql://root:password@localhost/finance_mentor_db",
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

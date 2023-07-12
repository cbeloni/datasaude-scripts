from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

BaseSqlite = declarative_base()

db1_url = 'sqlite:///db1.sqlite'
engineSqlite = create_engine(db1_url)
SessionSqlite = sessionmaker(bind=engineSqlite)
sessionSqlite = SessionSqlite()

def create_all():
    BaseSqlite.metadata.create_all(engineSqlite)
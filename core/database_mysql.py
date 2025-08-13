from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from core.database import criar_engine_sqlalchemy

BaseMysql = declarative_base()

engineMysql = criar_engine_sqlalchemy()
SessionMysql = sessionmaker(bind=engineMysql)

def create_all():
    BaseMysql.metadata.create_all(engineMysql)

if __name__ == '__main__':
    create_all()
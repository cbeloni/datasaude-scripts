from sqlalchemy import Column, Unicode, BigInteger, DateTime, Integer, String

from core.database_sqlite import BaseSqlite

class PoluenteHistorico(BaseSqlite):
    __tablename__ = "poluente_historico"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    data = Column(Unicode(255))
    data_atual = Column(DateTime)
    endereco = Column(Unicode(255))
    indice = Column(Integer)
    municipio = Column(Unicode(50))
    nome = Column(Unicode(50))
    poluente = Column(Unicode(50))
    qualidade = Column(Unicode(50))
    situacao_rede = Column(Unicode(50))
    tipo_rede = Column(Unicode(50))

class Tabela1(BaseSqlite):
    __tablename__ = 'tabela3'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
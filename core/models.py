
from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer
from sqlalchemy.orm import declarative_base
from core.database import criar_engine_sqlalchemy

# engine = criar_engine_sqlalchemy()
Base = declarative_base()

class PoluenteHistorico(Base):
    __tablename__ = 'poluente_historico'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_rede = Column(String)
    tipo_monitoramento = Column(String)
    tipo = Column(String)
    data = Column(DateTime)
    hora = Column(String)
    codigo_estacao = Column(String)
    nome_estacao = Column(String)
    nome_parametro = Column(String)
    unidade_medida = Column(String)
    media_horaria = Column(Integer)
    media_movel = Column(String)
    valido = Column(String)
    dt_amostragem = Column(String)
    dt_instalacao = Column(String)
    dt_retirada = Column(String)
    concentracao = Column(String)
    taxa = Column(String)
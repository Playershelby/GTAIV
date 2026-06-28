import os
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Configurações da aplicação / pagamento
MERCADO_PAGO_ACCESS_TOKEN = os.getenv("MERCADO_PAGO_ACCESS_TOKEN", "APP_USR-52219040370356-062721-892f99da7948034721ca6ea95f22cce6-231703249")
MERCADO_PAGO_PUBLIC_KEY = os.getenv("MERCADO_PAGO_PUBLIC_KEY", "APP_USR-ad478a0d-135b-49c3-af3b-d2aff866677c")
PRICE_PER_NUMBER = float(os.getenv("PRICE_PER_NUMBER", "10"))

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    status_pagamento = Column(String(20), default="não pago")

import os
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Configurações da aplicação / pagamento
MERCADO_PAGO_ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
MERCADO_PAGO_PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRICE_PER_NUMBER = float(os.getenv("PRICE_PER_NUMBER", "10"))

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    status_pagamento = Column(String(20), default="não pago")

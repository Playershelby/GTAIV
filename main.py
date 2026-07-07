import mimetypes
from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import mercadopago
from config import (
    MERCADO_PAGO_ACCESS_TOKEN,
    MERCADO_PAGO_PUBLIC_KEY,
    PRICE_PER_NUMBER,
)

sdk = mercadopago.SDK("APP_USR-5663590239019254-070621-4746a7410d1bbd7babae74306b0f9ca8-3500885824")

# Adicione esta linha logo antes de inicializar o app Flask:
mimetypes.add_type('text/css', '.css')

app = Flask(__name__)
# ... (resto do seu código continua exatamente igual)

# 1. Configuração do SQLAlchemy
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///meubanco.db"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Definição do Modelo do Cliente
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)                  # Mudado para phone
    numeros_escolhidos = Column(String(255), nullable=True)
    status_pagamento = Column(String(20), default="não pago")

# Cria a tabela no banco caso ela não exista
Base.metadata.create_all(bind=engine)

# Migração simples para SQLite local: adiciona coluna se ainda não existir
if DATABASE_URL.startswith("sqlite:///"):
    db_file_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if os.path.exists(db_file_path):
        with engine.connect() as conn:
            columns_result = conn.exec_driver_sql("PRAGMA table_info(clientes)")
            existing_columns = [row[1] for row in columns_result.fetchall()]
            if "numeros_escolhidos" not in existing_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE clientes ADD COLUMN numeros_escolhidos VARCHAR(255)"
                )
                conn.commit()

# 3. Rotas da API Flask

# Rota para Criar um Cliente (POST)
@app.route("/clientes", methods=["POST"])
def criar_cliente():
    dados = request.get_json()
    
    # ---- LINHA DE DIAGNÓSTICO IMPORTANTE ----
    print(f"--> DADOS RECEBIDOS NO BACKEND: {dados}")
    # -----------------------------------------
    
    if not dados or "name" not in dados or "email" not in dados:
        return jsonify({"erro": "Nome e email são obrigatórios"}), 400

    selected_numbers = dados.get("selected_numbers")
    if not isinstance(selected_numbers, list) or len(selected_numbers) == 0:
        return jsonify({"erro": "Selecione ao menos um número para participar do sorteio"}), 400

    try:
        selected_numbers = [int(n) for n in selected_numbers]
    except (TypeError, ValueError):
        return jsonify({"erro": "Lista de números selecionados inválida"}), 400

    db = SessionLocal()
    try:
        novo_cliente = Cliente(
            nome=dados["name"],
            email=dados["email"],
            phone=dados.get("phone"),
            numeros_escolhidos=",".join(str(n) for n in selected_numbers),
            status_pagamento="não pago"  # Todo cliente inicia como 'não pago'
        )
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        
        return jsonify({"mensagem": "Cliente registrado com sucesso!", "id": novo_cliente.id}), 201
    except Exception as e:
        db.rollback()
        # ESSA LINHA ABAIXO VAI PRINTAR O ERRO REAL NO SEU TERMINAL
        print(f"❌ ERRO REAL DO BANCO DE DADOS: {str(e)}") 
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 400

    finally:
        db.close()

# Rota para Listar todos os Clientes (GET)
@app.route("/clientes", methods=["GET"])
def listar_clientes():
    db = SessionLocal()
    clientes = db.query(Cliente).all()
    db.close()

    resultado = []
    resultado.extend(
        {
            "id": c.id,
            "nome": c.nome,
            "email": c.email,
            "phone": c.phone,
            "numeros_escolhidos": (
                [int(n) for n in c.numeros_escolhidos.split(",")]
                if c.numeros_escolhidos
                else []
            ),
            "status_pagamento": c.status_pagamento,
        }
        for c in clientes
    )
    return jsonify(resultado), 200

# Rota principal que vai renderizar o seu arquivo index.html
@app.route("/")
def pagina_inicial():
    db = SessionLocal()
    try:
        clientes = db.query(Cliente).all()
        return render_template(
            "index.html",
            clientes=clientes,
            mp_public_key=MERCADO_PAGO_PUBLIC_KEY,
            price_per_number=PRICE_PER_NUMBER
        )
    finally:
        db.close()

@app.route("/create-preference", methods=["POST"])
def create_preference():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Payload inválido"}), 400

    required_fields = ["name", "email", "quantity"]
    if any(field not in dados for field in required_fields):
        return jsonify({"erro": "Campos obrigatórios ausentes"}), 400

    try:
        quantity = int(dados.get("quantity", 0))
    except (TypeError, ValueError):
        return jsonify({"erro": "Quantidade inválida"}), 400

    if quantity <= 0:
        return jsonify({"erro": "Quantidade deve ser maior que zero"}), 400

    backend_total = round(quantity * PRICE_PER_NUMBER, 2)

    preference_data = {
        "items": [
            {
                "title": f"Rifa GTA VI - {quantity} número(s)",
                "quantity": 1,
                "unit_price": backend_total,
                "currency_id": "BRL",
            }
        ],
        "payer": {
            "name": dados["name"],
            "email": dados["email"],
        },
        "payment_methods": {
            "excluded_payment_types": [],
            "installments": 12,
        },
        "external_reference": f"rifa-gta-vi-{dados.get('email', 'cliente')}",
    }

    try:
        response = sdk.preference().create(preference_data)
        body = response.get("response", {})
        preference_id = body.get("id")
        init_point = body.get("init_point")

        if not preference_id:
            print(f"⚠️ RESPOSTA MP SEM ID: {response}")
            fallback_init_point = (
                body.get("sandbox_init_point")
                or body.get("init_point")
                or (response.get("response", {}).get("sandbox_init_point") if isinstance(response, dict) else None)
            )
            if fallback_init_point:
                return jsonify({
                    "preference_id": body.get("id", "fallback-no-id"),
                    "init_point": fallback_init_point,
                    "total": backend_total
                }), 200
            return jsonify({"erro": "Falha ao gerar preferência no Mercado Pago"}), 500

        return jsonify({
            "preference_id": preference_id,
            "init_point": init_point,
            "total": backend_total
        }), 200
    except Exception as e:
        print(f"❌ ERRO MERCADO PAGO: {str(e)}")
        return jsonify({"erro": f"Erro ao criar preferência: {str(e)}"}), 500

@app.route("/termos", methods=["GET"])
def termos_uso():
    return render_template("TermosUso.html")

@app.route("/política", methods=["GET"])
def politica_privacidade():
    return render_template("PoliticaPriv.html")

# Executa o servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
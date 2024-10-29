import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importar o CORS
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime

# Carregar variáveis do arquivo .env apenas em desenvolvimento, evitando utiliza-las em produção
if os.getenv("ENV") != "PRODUCTION":
    load_dotenv()

# Inicializar a aplicação Flask
app = Flask(__name__)
application = app  # permitindo que o EB (Elastic Beanstalk) reconheça o aplicativo Flask como 'application'
CORS(app)  # Aplicar o CORS

# Conectar ao MongoDB usando a URI do .env
mongo_uri = os.getenv("MONGO_URI")

try:
    # Conectando ao MongoDB
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)  # Timeout de 5 segundos
    db = client["UserAnalyticsCluster"]
except PyMongoError as err:
    print(f"Erro ao conectar ao MongoDB: {err}")
    db = None  # Banco de dados é None se a conexão falhar

# Função para registrar uma interação no MongoDB
def log_interaction(button_clicked, user_ip):
    if db is not None:
        interactions_collection = db["interactions"]  # Nome da coleção

        # Dados da interação
        interaction = {
            "button": button_clicked,
            "timestamp": datetime.now(),
            "user_ip": user_ip  # Recebendo o IP do usuário como parâmetro p/ em seguida, utilizar o recurso de localizar a UF
        }

        # Inserir a interação no MongoDB
        try:
            result = interactions_collection.insert_one(interaction)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Erro ao inserir interação no MongoDB: {e}")
            return None
    else:
        print("Banco de dados não está disponível.")
        return None

# Rota para registrar uma interação via API
@app.route('/api/log_interaction', methods=['POST'])
def log_interaction_endpoint():
    # Verifica se o banco de dados está disponível
    if db is None:
        return jsonify({'error': 'Banco de dados não disponível'}), 503  # Status 503 para indicar serviço indisponível

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados JSON inválidos ou ausentes'}), 400

    button = data.get('button')
    if not button:
        return jsonify({'error': 'O nome do botão é necessário'}), 400

    user_ip = request.remote_addr  # Capturar o IP do usuário

    interaction_id = log_interaction(button, user_ip)

    if interaction_id:
        return jsonify({'message': 'Interação registrada com sucesso!', 'interaction_id': interaction_id}), 201
    else:
        return jsonify({'error': 'Falha ao registrar a interação.'}), 500

# Rota para testar se a API está funcionando corretamente
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'API funcionando corretamente!'}), 200

# Executar a aplicação localmente
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

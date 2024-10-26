import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime

# Carregar variáveis do arquivo .env
if os.getenv("VERCEL") is None:
    load_dotenv()

# Inicializar a aplicação Flask
app = Flask(__name__)

# Conectar ao MongoDB usando a URI do .env
mongo_uri = os.getenv("MONGO_URI")

def connect_mongo():
    try:
        # Conectar ao MongoDB
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)  # Timeout de 5 segundos
        db = client["UserAnalyticsCluster"]
        if db is not None:
            return db
        else:
            raise Exception("Conexão com o MongoDB falhou.")
        
    except PyMongoError as err:
        print(f"Erro ao conectar ao MongoDB: {err}")
        return None
    
# Função para registrar uma interação no MongoDB
def log_interaction(button_clicked):
    db = connect_mongo()
    if db is not None:
        interactions_collection = db["interactions"]  # nome da coleção
        
        # Dados da interação
        interaction = {
            "button": button_clicked,
            "timestamp": datetime.now(),
            "user_ip": request.remote_addr  # Capturar o IP do usuário
        }
        
        # Inserir a interação no MongoDB
        result = interactions_collection.insert_one(interaction)
        return str(result.inserted_id)
    else:
        return None

# Rota para registrar uma interação via API
@app.route('/api/log_interaction', methods=['POST'])
def log_interaction_endpoint():
    try:
        data = request.get_json()
        button = data.get('button')
        
        if not button:
            return jsonify({'error': 'O nome do botão é necessário'}), 400
        
        interaction_id = log_interaction(button)
        
        if interaction_id:
            return jsonify({'message': 'Interação registrada com sucesso!', 'interaction_id': interaction_id}), 201
        else:
            return jsonify({'error': 'Falha ao registrar a interação.'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rota para testar se a API está funcionando corretamente
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({'message': 'API funcionando corretamente!'}), 200

# Testar o registro de uma interação manualmente no terminal
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) 

from bson import ObjectId
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

from common.mongo_config import MongoDB
from tagfilter import tagFilter, getAditionalQuestions, detect_positive_answers, filterServicesByTag

# Cargar variables de entorno
load_dotenv()

# Obtener la base de datos
db = MongoDB()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "TagFilter Service Running!"

@app.route('/filter', methods=['POST'])
def filter_services():
    """
    Endpoint que recibe el input del usuario y devuelve los servicios filtrados por tags y campos obligatorios.
    """
    try:
        data = request.get_json()
        user_input = data.get('userinput')
        intent = data.get('intent')
        domain = data.get('domain')
        data_from_client = data

        if not user_input or not intent or not domain:
            return jsonify({"error": "Missing 'userinput', 'intent' or 'domain' in request body."}), 400

        services = tagFilter(user_input, intent, data_from_client, domain)
        services = [str(service) for service in services]  # Asegúrate de pasar IDs como strings
        return jsonify({"services": services}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/additional-questions', methods=['POST'])
def generate_additional_questions():
    """
    Endpoint que recibe servicios candidatos y devuelve preguntas discriminativas para decidir entre ellos.
    """
    try:
        data = request.get_json()
        services = data.get('services')
        user_input = data.get('userinput')
        intent = data.get('intent')
        domain = data.get('domain')
        data_from_client = data

        if not services or not user_input or not intent or not domain:
            return jsonify({"error": "Missing 'services', 'userinput', 'intent' or 'domain' in request body."}), 400

        additional_questions, filled_params = getAditionalQuestions(services, user_input, intent, data_from_client, domain)

        return jsonify({
            "additional_questions": additional_questions,
            "filledslots": filled_params
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/filter-by-tags', methods=['POST'])
def filter_by_tags():
    try:
        data = request.get_json()
        services = data.get('services', [])
        filledslots = data.get('filledslots', {})
        domain = data.get('domain')

        if not services or not domain:
            return jsonify({"error": "Missing 'services' or 'domain'."}), 400

        positive_tags = detect_positive_answers(filledslots)
        print("[DEBUG] TAGS POSITIVOS DETECTADOS:", positive_tags)

        object_ids = [ObjectId(s) for s in services]
        selected_services = filterServicesByTag(object_ids, positive_tags, domain)

        return jsonify({"filtered_services": selected_services}), 200

    except Exception as e:
        print("[ERROR] En /filter-by-tags:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/detect-positive', methods=['POST'])
def detect_positive():
    """
    Recibe un diccionario con los parámetros llenados por el usuario
    y devuelve una lista con los nombres de los parámetros cuya respuesta
    indica una preferencia afirmativa.
    """
    try:
        data = request.get_json()
        filled_params = data.get("filled_params", {})

        if not isinstance(filled_params, dict):
            return jsonify({"error": "El campo 'filled_params' debe ser un diccionario."}), 400

        positive_keywords = ["yes", "yeah", "yep", "sure", "absolutely", "definitely", "of course"]
        positive_tags = []

        for tag, answer in filled_params.items():
            if isinstance(answer, str):
                response_lower = answer.lower()
                if any(word in response_lower for word in positive_keywords):
                    positive_tags.append(tag)

        return jsonify({"positive_tags": positive_tags}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

from disc_parameter import (
    get_top_parameters_combined,
    update_frequencies_for_requested_slots,
    detect_and_update_other_slots
)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Disc Parameter Service Running!"

@app.route('/top-parameters', methods=['POST'])
def top_parameters():
    """
    Devuelve los dos parámetros con mayor frecuencia combinada en el dominio especificado.
    """
    try:
        data = request.get_json()
        domain = data.get('domain')

        if not domain:
            return jsonify({"error": "Missing 'domain' in request body."}), 400

        top_parameters = get_top_parameters_combined(domain)
        print("[DEBUG] Top parameters (raw):", top_parameters)
        return jsonify(top_parameters), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-frequencies', methods=['POST'])
def update_frequencies():
    """
    Actualiza las frecuencias de los slots solicitados si han sido mencionados en el input.
    """
    try:
        data = request.get_json()
        slots_list = data.get('slots_list', [])
        req_slots = data.get('reqslots', [])
        domain = data.get('domain')

        if not slots_list or not req_slots or not domain:
            return jsonify({"error": "Missing 'slots_list', 'reqslots' or 'domain' in request body."}), 400

        update_frequencies_for_requested_slots(slots_list, req_slots, domain)

        return jsonify({"message": "Frequencies updated successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/detect-and-update', methods=['POST'])
def detect_and_update():
    """
    Detecta menciones de otros parámetros y actualiza su frecuencia en MongoDB.
    """
    try:
        data = request.get_json()
        user_input = data.get('userinput')
        top_slots_list = data.get('top_slots_list', [])
        domain = data.get('domain')

        if not user_input or not top_slots_list or not domain:
            return jsonify({"error": "Missing 'userinput', 'top_slots_list' or 'domain' in request body."}), 400

        detect_and_update_other_slots(user_input, top_slots_list, domain)

        return jsonify({"message": "Detection and frequency update done successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
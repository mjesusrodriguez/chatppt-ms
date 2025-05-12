from flask import Flask, request, jsonify
from common.serviceselection import serviceSelection, impServiceSelection, selectServiceByIntent

app = Flask(__name__)

@app.route('/serviceselection', methods=['POST'])
def handle_service_selection():
    try:
        data = request.get_json()

        required_fields = ['tagServices', 'user_input', 'slots', 'intent', 'domain']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing one of required fields: {required_fields}"}), 400

        tagServices = data['tagServices']
        user_input = data['user_input']
        slots = data['slots']
        intent = data['intent']
        domain = data['domain']

        # Call the service selection function - MODIFICADO
        selected_services = impServiceSelection(tagServices, user_input, slots, intent, domain)

        return jsonify({"selected_services": selected_services}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/improvedserviceselection', methods=['POST'])
def handle_improved_service_selection():
    try:
        data = request.get_json()

        required_fields = ['tagServices', 'user_input', 'slots', 'intent', 'domain']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing one of required fields: {required_fields}"}), 400

        tagServices = data['tagServices']
        user_input = data['user_input']
        slots = data['slots']
        intent = data['intent']
        domain = data['domain']

        selected_services = impServiceSelection(tagServices, user_input, slots, intent, domain)

        return jsonify({"selected_services": selected_services}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/select_service_by_intent', methods=['POST'])
def handle_select_service_by_intent():
    try:
        data = request.get_json()

        if 'intent' not in data or 'domain' not in data:
            return jsonify({"error": "Missing 'intent' or 'domain' field in the request."}), 400

        intent = data['intent']
        domain = data['domain']

        services = selectServiceByIntent(intent, domain)

        return jsonify({"services": services}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
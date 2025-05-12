from flask import Flask, request, jsonify
from slotfilling import slotFillingGPT, extractSlots

app = Flask(__name__)

@app.route('/slotfilling', methods=['POST'])
def handle_slotfilling():
    try:
        data = request.get_json()

        if 'input' not in data or 'slots' not in data:
            return jsonify({"error": "Missing 'userInput' or 'slots' field in the request."}), 400

        userInput = data['input']
        slots = data['slots']
        userAnswers = data.get('userAnswers')  # Opcional

        result = slotFillingGPT(userInput, slots, userAnswers)

        return jsonify({"filled_slots": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/extract-slots', methods=['POST'])
def extract_slots_route():
    data = request.get_json()
    intent = data.get('intent')
    service_id = data.get('service_id')
    domain = data.get('domain')

    if not all([intent, service_id, domain]):
        return jsonify({"error": "Missing required fields: intent, service_id, or domain"}), 400

    try:
        slots = extractSlots(intent, service_id, domain)
        return jsonify({"slots": slots}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
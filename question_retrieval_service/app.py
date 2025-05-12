from flask import Flask, request, jsonify
from questionretrieval import questionsRetrieval

app = Flask(__name__)

@app.route('/retrieve_questions', methods=['POST'])
def handle_retrieve_questions():
    try:
        data = request.get_json()

        if 'service_id' not in data or 'intent' not in data or 'domain' not in data:
            return jsonify({"error": "Missing 'service_id', 'intent' or 'domain' fields in the request."}), 400

        service_id = data['service_id']
        intent = data['intent']
        domain = data['domain']

        print(f"[DEBUG] Llamando a questionsRetrieval con: service_id={service_id}, intent={intent}, domain={domain}")
        questions = questionsRetrieval(service_id, intent, domain)
        print("[DEBUG] Resultado de questionsRetrieval:", questions["intent"]["slots"])

        return jsonify({"questions": questions["intent"]["slots"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
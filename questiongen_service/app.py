from flask import Flask, request, jsonify
from questionimprovement import createQuestionGPT

app = Flask(__name__)

@app.route('/create_question', methods=['POST'])
def handle_create_question():
    try:
        data = request.get_json()

        if 'slot' not in data or 'domain' not in data:
            return jsonify({"error": "Missing 'slot' or 'domain' field in the request."}), 400

        slot = data['slot']
        domain = data['domain']

        created_question = createQuestionGPT(slot, domain)

        return jsonify({"created_question": created_question}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
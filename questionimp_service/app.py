from flask import Flask, request, jsonify
from questionimprovement import improveQuestionchatGPT

app = Flask(__name__)

@app.route('/questionimprovement', methods=['POST'])
def handle_question_improvement():
    try:
        data = request.get_json()

        if 'question' not in data or 'domain' not in data:
            return jsonify({"error": "Missing 'question' or 'domain' field in the request."}), 400

        question = data['question']
        domain = data['domain']

        improved_question = improveQuestionchatGPT(question, domain)

        return jsonify({"improved_question": improved_question}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
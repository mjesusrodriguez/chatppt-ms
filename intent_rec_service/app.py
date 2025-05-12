from flask import Flask, request, jsonify
from intentrec import intentRecWithChatGPT

app = Flask(__name__)

@app.route('/intent_recognition', methods=['POST'])
def handle_intent_recognition():
    try:
        data = request.get_json()

        if 'input' not in data or 'domain' not in data:
            return jsonify({"error": "Missing 'input' or 'domain' field in the request."}), 400

        user_input = data['input']
        domain = data['domain']

        intent = intentRecWithChatGPT(user_input, domain)

        return jsonify({"intent": intent}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
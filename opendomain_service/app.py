from flask import Flask, request, jsonify
from opendomain import opendomainconversation

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_opendomain():
    data = request.get_json()
    user_input = data.get("input", "")
    dialogue_history = data.get("dialogue_history", [])

    if not user_input:
        return jsonify({"error": "Missing 'input' field"}), 400

    try:
        response = opendomainconversation(user_input, dialogue_history)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
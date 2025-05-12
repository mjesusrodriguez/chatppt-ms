from flask import Flask, request, jsonify
from domain_manager import domain_manager_gpt

app = Flask(__name__)

@app.route('/domain_manager', methods=['POST'])
def handle_domain_manager():
    try:
        data = request.get_json()

        if 'input' not in data:
            return jsonify({"error": "Missing 'input' field in the request."}), 400

        user_input = data['input']
        result = domain_manager_gpt(user_input)

        return jsonify({"domains": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
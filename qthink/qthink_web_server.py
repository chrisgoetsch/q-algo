from flask import Flask, request, jsonify, send_from_directory
from qthink_engine import ask_qthink
import os

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('qthink', 'web_ui.html')

@app.route('/qthink', methods=['POST'])
def qthink_chat():
    data = request.get_json()
    response = ask_qthink(data.get('message', ''))
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

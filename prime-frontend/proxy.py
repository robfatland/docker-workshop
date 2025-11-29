from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/check/<int:number>')
def check_prime(number):
    # Call prime-api using Docker network hostname
    response = requests.get(f'http://prime-api:5000/check/{number}')
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

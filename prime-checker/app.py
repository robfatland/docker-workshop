from flask import Flask, request, jsonify

app = Flask(__name__)

def is_prime(n):
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

@app.route('/check/<int:number>', methods=['GET'])
def check_prime(number):
    result = is_prime(number)
    return jsonify({'number': number, 'is_prime': result})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

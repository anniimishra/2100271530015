from flask import Flask, jsonify, request
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

window_prev_state = []

def fetch_with_timeout(url, timeout=5000):
    try:
        token = os.getenv('ACCESS_TOKEN')
        if not token:
            raise ValueError("ACCESS_TOKEN not set in environment variables")

        logging.debug(f"Using token: {token}")

        headers = {'Authorization': f'Bearer {token}'}
        logging.debug(f"Request headers: {headers}")
        logging.debug(f"Requesting URL: {url}")

        response = requests.get(url, headers=headers, timeout=timeout / 1000)
        response.raise_for_status()
        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response data: {response.json()}")

        return response.json()
    except requests.Timeout:
        logging.error('Request took too long and was ignored.')
        return None
    except requests.HTTPError as http_err:
        if response.status_code == 401:
            logging.error('Unauthorized: Check the ACCESS_TOKEN')
        logging.error(f'HTTP error occurred: {http_err}')
        logging.error(f'Response content: {response.content}')
        return None
    except requests.RequestException as e:
        logging.error(f'Request failed: {e}')
        return None

def calculate_average(numbers):
    return sum(numbers) / len(numbers) if numbers else 0

@app.route('/numbers/<string:number_id>', methods=['POST'])
def get_numbers(number_id):
    global window_prev_state

    number_id = number_id.lower()
    url = None

    if number_id == 'e':
        url = 'http://20.244.56.144/test/even'
    elif number_id == 'f':
        url = 'http://20.244.56.144/test/fib'
    elif number_id == 'p':
        url = 'http://20.244.56.144/test/primes'
    elif number_id == 'r':
        url = 'http://20.244.56.144/test/rand'
    else:
        return jsonify({"message": "Error number type"}), 400

    data = fetch_with_timeout(url, timeout=10000)  # Increased timeout to 10 seconds

    if data:
        numbers = data.get('numbers', [])
        window_curr_state = list(set(numbers))[-10:]
        avg = calculate_average(window_curr_state)
        response = {
            "numbers": numbers,
            "windowPrevState": window_prev_state,
            "windowCurrState": window_curr_state,
            "avg": avg
        }
        window_prev_state = window_curr_state
        return jsonify(response)
    else:
        return jsonify({'message': 'Request timed out and was ignored'}), 504

@app.errorhandler(500)
def internal_error(error):
    return "Something broke!", 500

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 5000)))

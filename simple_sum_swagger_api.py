import numpy as np
import json
from flask import Flask, request, jsonify
from flasgger import Swagger
from flasgger.utils import swag_from


def add_2_numbers(num1,num2):
	output = {'sum_of_numbers':0}
	sum_of_2_numbers = num1 + num2
	output['sum_of_numbers'] = sum_of_2_numbers
	return output


app = Flask(__name__)
swagger = Swagger(app)


@app.route("/")
def index():
	return "Add 2 Numbers!"


@app.route("/add_2_numbers", methods = ['POST'])
@swag_from('swagger_config.yml')
def add_numbers():
	input_json = request.get_json()
	try:
		num1 = int(input_json['x1'])
		num2 = int(input_json['x2'])
		res = add_2_numbers(num1,num2)
	except:
		res = {
			'success': False,
			'message': 'Unknown error'
		}
		
	return json.dumps(res)

if __name__ == "__main__":
	app.run(debug = True, port = 8791)

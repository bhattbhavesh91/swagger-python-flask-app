import json
import numpy as np
import requests
from flask import Flask, request, jsonify
from flasgger import Swagger
from flasgger.utils import swag_from
from flasgger import LazyString, LazyJSONEncoder
from py_zipkin.zipkin import create_http_headers_for_new_span
from py_zipkin.zipkin import zipkin_span
from py_zipkin.zipkin import ZipkinAttrs

ZIPKIN_SERVER = 'http://localhost:9411/api/v1/spans'
SQUARE_URL = 'http://localhost:7000/square_numbers'

def http_transport(encoded_span):
    body = encoded_span
    response = requests.post(ZIPKIN_SERVER, data=body, headers={
                         'Content-Type': 'application/x-thrift'})
    if response.ok:
        print("HTTP trace posted to Zipkin")
    else:
        print("response: {}".format(response.content))
        print("HTTP trace not posted to Zipkin")
    return 1

@zipkin_span(service_name='sum_api', span_name='adding_2_numbers')
def add_2_numbers_and_square_it(num1, num2):
    output = {"sum_of_numbers": 0}
    sum_of_2_numbers = num1 + num2
    headers_new = create_http_headers_for_new_span()
    response_square = requests.post(
        SQUARE_URL, json={"num": sum_of_2_numbers}, headers=headers_new)
    if response_square.ok:
        resp_sq_json = response_square.json()
        output["sum_of_numbers"] = resp_sq_json['square_of_number']
    return output


app = Flask(__name__)
app.config["SWAGGER"] = {"title": "Swagger-UI", "uiversion": 2}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/swagger/",
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)

app.json_encoder = LazyJSONEncoder
swagger = Swagger(app, config=swagger_config, template=template)


@app.route("/")
def index():
    with zipkin_span(
        service_name='sum_api',
        span_name='index_span',
        transport_handler=http_transport, 
        sample_rate=100):
        return "Add 2 Numbers!"


@app.route("/add_2_numbers", methods=["POST"])
@swag_from("swagger_config.yml")
def add_numbers():
    with zipkin_span(
        service_name="sum_api",
        span_name="receive_inp_and_run_add_method",
        transport_handler=http_transport,
        sample_rate=100,
    ):
        input_json = request.get_json()
        try:
            num1 = int(input_json["x1"])
            num2 = int(input_json["x2"])
            res = add_2_numbers_and_square_it(num1, num2)
        except:
            res = {"success": False, "message": "Unknown error"}
        return json.dumps(res)


if __name__ == "__main__":
    app.run(debug=True, port=7001)

import json
import numpy as np
import requests
import time
from flask import Flask, request, jsonify
from flasgger import Swagger
from flasgger.utils import swag_from
from flasgger import LazyString, LazyJSONEncoder
from py_zipkin.zipkin import create_http_headers_for_new_span
from py_zipkin.zipkin import zipkin_span
from py_zipkin.zipkin import ZipkinAttrs

ZIPKIN_SERVER = 'http://localhost:9411/api/v1/spans'

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


@zipkin_span(service_name='square_api', span_name='computing_the_square')
def square_nums(num):
    output = {"square_of_number": 0}
    square_of_numbers = num ** 2
    time.sleep(3)
    output["square_of_number"] = square_of_numbers
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
        service_name='square_api',
        span_name='index_span',
        transport_handler=http_transport, 
        sample_rate=100):
        return "Square the inputted Number!"


@app.route("/square_numbers", methods=["POST"])
@swag_from("swagger_config_square.yml")
def square_number():
    with zipkin_span(
        service_name='square_api',
        zipkin_attrs=ZipkinAttrs(
            trace_id=request.headers['X-B3-TraceID'],
            span_id=request.headers['X-B3-SpanID'],
            parent_span_id=request.headers['X-B3-ParentSpanID'],
            flags=request.headers['X-B3-Flags'],
            is_sampled=request.headers['X-B3-Sampled'],
        ),
        span_name='receive_inp_and_run_square_method',
        transport_handler=http_transport,
        sample_rate=100,
        port=7000,
    ):
        input_json = request.get_json()
        try:
            inp_num = int(input_json["num"])
            res = square_nums(inp_num)
        except:
            res = {"success": False, "message": "Unknown error"}

        return json.dumps(res)


if __name__ == "__main__":
    app.run(debug=True, port=7000)
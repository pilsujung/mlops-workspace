import requests
import json

# MLflow Serving Endpoint
URL = "http://localhost:17001/invocations"

headers = {
    "Content-Type": "application/json"
}

# cache 구조
# key : 입력 tuple
# value : {"count": 요청횟수, "result": 예측결과}
cache = {}

CACHE_THRESHOLD = 2


def request_model(values):
    payload = {
        "dataframe_split": {
            "columns": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
            "data": [values]
        }
    }

    response = requests.post(URL, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed: {response.text}")


while True:

    print("\nEnter 4 values (sepal_length sepal_width petal_length petal_width)")
    user_input = input("> ")

    try:
        values = list(map(float, user_input.split()))
        if len(values) != 4:
            print("Please enter exactly 4 numbers.")
            continue
    except:
        print("Invalid input.")
        continue

    key = tuple(values)

    # cache 존재 여부 확인. cache hit -> cache[key]["result"] 출력 후 continue.
    #
    #
    #
    #
    #
    #
    #
    #
    #

    # cache no hit -> REST API 호출
    print("Calling REST API...")

    result = request_model(values)

    print("Prediction:", result)

    # cache 업데이트
    #
    #
    #
    #

import requests
import json
from circuit_breaker import CircuitBreaker

URL = "http://localhost:17001/invocations"

headers = {
    "Content-Type": "application/json"
}

cache = {}

CACHE_THRESHOLD = 2


breaker = CircuitBreaker(
    failure_threshold=2,
    recovery_timeout=10
)


def request_model(values):

    payload = {
        "dataframe_split": {
            "columns": [
                "sepal_length",
                "sepal_width",
                "petal_length",
                "petal_width"
            ],
            "data": [values]
        }
    }

    response = requests.post(URL, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(response.text)


def fallback():
    return {"prediction": "fallback_response"}


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

    # cache 확인
    if key in cache:

        cache[key]["count"] += 1

        if cache[key]["count"] >= CACHE_THRESHOLD:
            print("CACHE HIT")
            print("Prediction:", cache[key]["result"])
            continue

    print("Calling service through CircuitBreaker...")

    result = breaker.call(
        request_model,
        fallback,
        values
    )

    print("Prediction:", result)

    # cache 업데이트
    if key not in cache:
        cache[key] = {
            "count": 1,
            "result": result
        }
    else:
        cache[key]["result"] = result

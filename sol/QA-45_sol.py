import requests
import json
from circuit_breaker import CircuitBreaker
from guardrail import Guardrail

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

# Guardrail 객체 생성
guardrail = Guardrail("iris.csv")

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

    # =========================
    # Guardrail (OOD 입력 탐지)
    # =========================

    if guardrail.is_ood(values):
        print("⚠ OOD input detected")

        # OOD 입력을 파일에 기록
        guardrail.log_ood(values)

        print("Input logged to OOD.csv")

        # 모델 호출을 하지 않고 다음 입력으로 넘어감
        # Rule-based Logic으로 대체 가능
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

import os
import mlflow
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
from airflow import DAG
import pandas as pd
import random
import pendulum
import numpy as np
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from airflow.utils.dates import days_ago

mlflow.set_tracking_uri("http://mlflow:600")
mlflow.set_experiment("exercise_drift")

local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

dag = DAG(
    dag_id="DataDriftRetrainDAG",
    default_args=default_args,
    schedule_interval="*/2 * * * *",  # 매 2분
    catchup=False,
)

REFERENCE_STATS_PATH = "./reference_stats.csv"

# 1️⃣ 시간에 따라 분포가 바뀌는 데이터 생성
def get_data(**context):
    X, y = load_iris(return_X_y=True, as_frame=True)
    df = pd.concat([X, y], axis="columns")

    run_id = context["dag_run"].run_id

    if "odd" in run_id or int(context["execution_date"].minute / 2) % 2 == 1:
        df["sepal length (cm)"] += 15
        df["petal length (cm)"] *= 6
        df["sepal width (cm)"] = np.random.uniform(0, 15, len(df))

        df = df[df["target"] != 0]

    else:
        df.iloc[:, :-1] += np.random.normal(0, 0.01, df.iloc[:, :-1].shape)

    path = "./iris_drift.csv"
    df.to_csv(path, index=False)
    return path

# Data Drift 탐지
def detect_drift(**context):
    distribution_diff = 0

    # detect drift logic
    #
    #
    #
    #
    #


    if distribution_diff > 0.2:
        return "train_fit"
    else:
        return "no_drift"

# 3️⃣ 모델 학습
def train_fit(**context):
    path = context["task_instance"].xcom_pull(task_ids="get_data")
    df = pd.read_csv(path)

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, train_size=0.8, random_state=2024
    )

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC())
    ])

    model.fit(X_train, y_train)

    train_acc = accuracy_score(y_train, model.predict(X_train))
    valid_acc = accuracy_score(y_valid, model.predict(X_valid))

    with mlflow.start_run():
        mlflow.log_metrics({
            "train_acc": train_acc,
            "valid_acc": valid_acc
        })
        mlflow.sklearn.log_model(model, "sk_model")

    X.to_csv(REFERENCE_STATS_PATH, index=False)
    print("Retraining completed due to data drift")

# === Airflow Operators ===

get_data_task = PythonOperator(
    task_id="get_data",
    python_callable=get_data,
    dag=dag,
)

detect_drift_task = BranchPythonOperator(
    task_id="detect_drift",
    python_callable=detect_drift,
    dag=dag,
)

train_task = PythonOperator(
    task_id="train_fit",
    python_callable=train_fit,
    dag=dag,
)

no_drift_task = EmptyOperator(
    task_id="no_drift",
    dag=dag,
)

# === DAG Flow ===
get_data_task >> detect_drift_task
detect_drift_task >> train_task
detect_drift_task >> no_drift_task

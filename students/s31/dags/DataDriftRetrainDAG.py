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
mlflow.set_experiment("DataDriftRetrainDAG_experiments")

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

TRAINING_DATASET_PATH = "./training_dataset.csv"

# 1️⃣ 시간에 따라 분포가 바뀌는 데이터 생성
def get_data(**context):
    X, y = load_iris(return_X_y=True, as_frame=True)
    X.columns = [
        "sepal_length",
        "sepal_width",
        "petal_length",
        "petal_width"
    ]
    df = pd.concat([X, y], axis="columns")

    run_id = context["dag_run"].run_id

    # apply data distribution shift
    if "odd" in run_id or int(context["execution_date"].minute / 2) % 2 == 1:
        df["sepal_length"] += 15
        df["petal_length"] *= 6
        df["sepal_width"] = np.random.uniform(0, 15, len(df))

        df = df[df["target"] != 0]

    else:
        df.iloc[:, :-1] += np.random.normal(0, 0.01, df.iloc[:, :-1].shape)

    path = "./iris_drift.csv"
    df.to_csv(path, index=False)
    return path

# Data Drift 탐지
def detect_drift(**context):
    path = context['task_instance'].xcom_pull(task_ids='get_data')
    df = pd.read_csv(path)  # 현재 데이터 셋

    distribution_diff = 0.3

    # detect drift logic
    # 과거 데이터 셋과 현재 데이터셋 간 분포 비교
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
    path = context['task_instance'].xcom_pull(task_ids='get_data')
    df = pd.read_csv(path)

    # ==============================
    # Dataset logging
    # ==============================

    dataset = mlflow.data.from_pandas(
        df,
        source=path,
        name="iris_dataset"
    )

    # Preprocess
    X = df.drop(["target"], axis="columns")
    y = df["target"]

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y,
        train_size=0.8,
        random_state=2024
    )

    # model develop
    model_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC())
    ])

    with mlflow.start_run():

        # ==============================
        # Dataset 기록
        # ==============================
        mlflow.log_artifact(path)       # 학습 데이터 파일을 artifact로 기록
        mlflow.log_input(dataset, context="training")

        # ==============================
        # Parameter 기록
        # ==============================

        mlflow.log_params({
            "model_type": "SVC",
            "train_size": 0.8,
            "random_state": 2024
        })

        # ==============================
        # Model training
        # ==============================

        model_pipeline.fit(X_train, y_train)

        train_pred = model_pipeline.predict(X_train)
        valid_pred = model_pipeline.predict(X_valid)

        train_acc = accuracy_score(y_train, train_pred)
        valid_acc = accuracy_score(y_valid, valid_pred)

        print("Train Accuracy :", train_acc)
        print("Valid Accuracy :", valid_acc)

        # ==============================
        # Metric 기록
        # ==============================

        mlflow.log_metrics({
            "train_acc": train_acc,
            "valid_acc": valid_acc
        })

        # ==============================
        # Model logging
        # ==============================

        # Model Serving 시 입력 검증을 하기 위한 코드 (입출력에 대한 signature를 자동으로 추출)
        signature = mlflow.models.signature.infer_signature(
            model_input=X_train,
            model_output=train_pred
        )

        input_sample = X_train.iloc[:10]

        mlflow.sklearn.log_model(
            sk_model=model_pipeline,
            artifact_path="sk_model",
            signature=signature,
            input_example=input_sample
            # registered_model_name="sk_model"
        )

    X.to_csv(TRAINING_DATASET_PATH, index=False)


# === Airflow Operators ===

get_data_task = PythonOperator(
    task_id="get_data",
    python_callable=get_data,
    dag=dag,
)

detect_drift_task = BranchPythonOperator( # return 값이 다음 task를 결정 
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

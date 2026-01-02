#필요 패키지 불러오기.
import os
import mlflow
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow import DAG
from argparse import ArgumentParser
import pandas as pd
import psycopg2
from sklearn.datasets import load_iris
import random
import pendulum
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import joblib


mlflow.set_tracking_uri("http://mlflow:600")
mlflow.set_experiment("new_exp")
#Airflow의 시간대 맞추기
local_tz = pendulum.timezone("Asia/Seoul")

#airflow 환경변수 디폴트 값 설정
default_args={
        'owner' : 'airflow',
        'start_date' : datetime(year=2026,month=1,day=2,hour=10,minute=0, tzinfo=local_tz),
        'retries' : 1,
        'retry_delay' : timedelta(minutes=3),
        }

#DAG 정보 입력
dag = DAG(
        dag_id = "ModelDevelop",
        default_args = default_args,
        schedule_interval = '*/60 * * * *'
        )

# 1. airflow_db의 iris table에서 데이터 가져오는 부분 함수 정의
def get_data(**context):
    X, y = load_iris(return_X_y = True, as_frame = True)
    df = pd.concat([X,y], axis="columns")
    rename_rule = {
             "sepal length (cm)": "sepal_length",
             "sepal width (cm)": "sepal_width",
             "petal length (cm)": "petal_length",
             "petal width (cm)": "petal_width",
             }
    df = df.rename(columns = rename_rule)

    random_number = random.randint(0,len(df))
#    df = df.sample(1, random_state=random_number)
    path = "./iris.csv"
    df.to_csv(path, index=False)
    return path

    
# 2. model development and train 부분 함수 정의
def train_fit(**context):
    path = context['task_instance'].xcom_pull(task_ids = 'get_data')
    df = pd.read_csv(path)
    print(df)
    
    #Preprocess
    X = df.drop(["target"], axis="columns")
    y = df["target"]
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2024)
    
    # model develop
    model_pipeline = Pipeline([("scaler", StandardScaler()), ("svc", SVC())])
    model_pipeline.fit(X_train, y_train)
    
    train_pred = model_pipeline.predict(X_train)
    valid_pred = model_pipeline.predict(X_valid)
    
    train_acc = accuracy_score(y_true = y_train, y_pred = train_pred)
    valid_acc = accuracy_score(y_true = y_valid, y_pred = valid_pred)
    
    print("Train Accuracy :", train_acc)
    print("Valid Accuracy :", valid_acc)
    
#    os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://34.22.73.120:9000"
#    os.environ["MLFLOW_TRACKING_URI"] = "http://34.22.73.120:5001"
#    os.environ["AWS_ACCESS_KEY_ID"] = "minio"
#    os.environ["AWS_SECRET_ACCESS_KEY"] = "miniostorage"
#    print("os_set_success")    
    
    #3. save model 
    mlflow.set_experiment("new_exp")
    print("SC1")
    signature = mlflow.models.signature.infer_signature(model_input = X_train, model_output=train_pred)
    input_sample = X_train.iloc[:10]
    print(input_sample)
    print("SC2")
    with mlflow.start_run():
            mlflow.log_metrics({"train_acc":train_acc, "valid_acc": valid_acc})
            mlflow.sklearn.log_model(
                    sk_model = model_pipeline,
                    artifact_path = "sk_model",
                    signature = signature,
                    input_example = input_sample,
       #             registered_model_name="sk_model"
            )
    print("****Success Message*******")    
        
#get_data taskInstance 설정
get_data = PythonOperator(
        task_id = 'get_data',
        python_callable = get_data,
        provide_context = True,
        dag = dag
)

#train_taskInstance 설정
train_fit = PythonOperator(
        task_id = 'train_fit',
        python_callable = train_fit,
        provide_context = True,
        dag = dag
)

#taskInstance 실행 순서 설정
get_data >> train_fit

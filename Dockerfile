FROM apache/airflow:2.8.3-python3.9

USER airflow
RUN pip install --no-cache-dir \
    mlflow==2.9.2 \
    scikit-learn

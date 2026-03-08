# curl -X POST http://localhost:17009/invocations -H "Content-Type: application/json" -d '{
# "dataframe_split": {
# "columns": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
# "data": [
#   [6.4, 3.2, 4.5, 1.5]
#   ]
#  }
# }'

curl -X POST http://localhost:17009/invocations -H "Content-Type: application/json" -d '{"dataframe_split": {"columns": ["sepal_length", "sepal_width", "petal_length", "petal_width"], "data": [ [6.4, 3.2, 4.5, 1.5] ] } }'

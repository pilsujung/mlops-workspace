#!/bin/bash

BASE_DIR="../students"

echo "Removing all directories inside $BASE_DIR ..."
rm -rf "$BASE_DIR"/*

echo "Recreating student directories and copying files..."

for i in $(seq 1 40)
do
    ID=$(printf "%02d" $i)
    TARGET_DIR="$BASE_DIR/s$ID/dags"

    echo "Processing $TARGET_DIR"

    # 디렉토리 생성
    mkdir -p "$TARGET_DIR"

    # 파일 복사
    cp ../sol/exercise_drift.py "$TARGET_DIR"/
    cp ../sol/exercise_QAs.py "$TARGET_DIR"/
    cp ../sol/iris.csv "$TARGET_DIR"/
done

echo "Done."

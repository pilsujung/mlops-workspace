#!/bin/bash

BASE_DIR="../students"

for i in $(seq -w 1 9)
do
    TARGET_DIR="$BASE_DIR/s0$i/dags"

    echo "Processing $TARGET_DIR"

    # dags 폴더 내부 파일 및 폴더 삭제
    rm -rf "$TARGET_DIR"/*

    # 파일 복사
    cp ./exercise_drift.py "$TARGET_DIR"/
    cp ./exercise_QAs.py "$TARGET_DIR"/
done

echo "Done."

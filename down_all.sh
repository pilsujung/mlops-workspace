#!/bin/bash
for i in $(seq -w 1 40)
do
    echo "Stopping s$i ..."
    docker compose -p s$i down -v
done

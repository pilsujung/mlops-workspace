#!/bin/bash

for i in $(seq -w 1 9)
do
    echo "Stopping s$i ..."
    docker compose -p s0$i down -v
done

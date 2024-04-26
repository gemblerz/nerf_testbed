#!/bin/bash

topic=$1
echo "Creating meta information on objects from the simulator"
echo "Using topic name: $topic"
echo "Please count 3 and press control + C"
python3 subscribe.py --topic-name $topic
echo "Please ensure the information is generated."
#!/bin/bash

BROKER_ADDRESS='192.168.0.100'
BROKER_PORT=20000

docker run --pid=host -v .:/Client/logs -it client ${BROKER_ADDRESS} ${BROKER_PORT}
#!/bin/bash

SERVER_NAME='Rock-Paper-Scissors'
SERVER_ADDRESS='192.168.0.100'
SERVER_PORT=20100

BROKER_ADDRESS='192.168.0.100'
BROKER_PORT=20000

docker run --pid=host -v .:/RPSServer/logs -p ${SERVER_PORT}:20100/tcp rps_server ${SERVER_NAME} ${SERVER_ADDRESS} ${SERVER_PORT} ${BROKER_ADDRESS} ${BROKER_PORT}
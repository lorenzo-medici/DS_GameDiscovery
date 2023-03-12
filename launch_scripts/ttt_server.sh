#!/bin/bash

SERVER_NAME='Tic-Tac-Toe'
SERVER_ADDRESS='192.168.0.100'
SERVER_PORT=20101

BROKER_ADDRESS='192.168.0.100'
BROKER_PORT=20000

docker run --pid=host -v .:/TTTServer/logs -p ${SERVER_PORT}:20101/tcp ttt_server ${SERVER_NAME} ${SERVER_ADDRESS} ${SERVER_PORT} ${BROKER_ADDRESS} ${BROKER_PORT}
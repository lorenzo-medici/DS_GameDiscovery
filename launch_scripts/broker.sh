#!/bin/bash

BROKER_PORT=20000

docker run --pid=host -v .:/Broker/logs -p ${BROKER_PORT}:20000/udp broker

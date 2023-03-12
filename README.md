# GameDiscovery

This is the final project for the Distributed Systems project held during the Spring 2023.
This project showcases a system where many servers offering command-line multiplayer games can register themselves on a broker, which will the nbe queried by clients to know the list of available servers at the time.
The whole codebase is written in Python, each entity is then included in a separate Docker image.


## Overview

The broker is implemented using a threading UDP socketserver, that allows multiple clients to access the registry at the same time. Concistency is ensured by a MutEx lock. The particular implementation chosen is a ReadWriteLock, that allows parallel reads, and locking writes.\
The client is responsible for all interactions with the user. It will request the list of servers to the broker and make the user choose one, or aask them to manually input an address. Then it will connect to the chosen server and display to the user the prompt received, read their input and send it to the server.\
The servers implemented in this repository are an example of possible games that could be played. The server as designed for this project is more like an interface/protocol that must be followed by all implementations.
In particular, it should 
 - send a string `<name>|<address>|<port>` to the broker for registration, and recognize the different values returned `okay`, `taken`, `renewed`
 - be aware of the auto-removal of stale entries happening on the broker and periodically register itself
 - have a TCP socket open on the port specified to the broker, accept incoming ocnnections and start game threads once certain conditions are satisfied
 - send users a string and wait for an answer when moves are needed

The servers implemented let users play Rock-Paper-Scissors (rps_server) and Tic-Tac-Toe (ttt_server).

## Installation and execution

(NOTE: the described procedure is focused on Linux systems. Equivalent commands and options are available for any system)

All entities can be directly launched from their `.py` files found in the respective folders.\
Alternatively, docker images can be created by executing in each entity's directory `docker buildx build . -f <name> -t <name>`, where `<name>` is either 'client', 'rps_server', 'ttt_server' or 'broker'.
Then, they can be manually launched using `docker run`, or the utility bash files in `launch_scripts/` can be used.

**To install docker on yout machine head to [Docker's webpage](https://docs.docker.com/get-docker/)**

These files already set the necessary environment variables and ports to make each container work as expected, and for logs to be saved locally.
To mark the files as executable you can run `chmod +x launch_scripts/*.sh`.\
The scripts contain variables that can be easily modified for each deployment; of course the `BROKER_ADDRESS` variable will need to match in all files for the system to work.

The files also make it easier to run each image on a separate machine, since only the `.tar` and `.sh` files are needed.

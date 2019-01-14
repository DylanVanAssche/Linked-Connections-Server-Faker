#!/usr/bin/env bash

# Start server
cd lc-server-faker
python main.py &
cd ..

# Wait until all connections and events are generated
while [ 1 ]
do
	wget -q http://127.0.0.1:8080
	if [ $? -eq 0 ]
	then
		echo "Server is available now!"
		break
	else
		echo "Waiting ..."
		sleep 5s
	fi
done
sleep 1s

# Run tests
python tests/tests.py

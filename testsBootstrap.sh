#!/usr/bin/env bash

# Start server
cd lc-server-faker
python main.py &
cd ..

# Wait until all connections and events are generated
while [ 1 ]
do
	sleep 10s
	ping -c 3 127.0.0.1:8080 > /dev/null 2>&1
	if [ $? -eq 0 ]
	then
		echo "Server is available now!"
		break
	fi
done
sleep 5s

# Run tests
python tests/tests.py

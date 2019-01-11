#!/usr/bin/env bash

# Start server
cd lc-server-faker
python main.py &
cd ..

# Wait until all connections and events are generated
sleep 300s

# Run tests
python tests/tests.py

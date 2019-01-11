#!/usr/bin/env bash

# Start server
cd lc-server-faker
python main.py &

# Wait until all connections and events are generated
sleep 90s

# Run tests
python tests/tests.py

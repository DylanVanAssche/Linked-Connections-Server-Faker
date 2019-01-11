#!/usr/bin/env bash

# Start server
python setup.py &

# Wait until all connections and events are generated
sleep 90s

# Run tests
python tests/tests.py
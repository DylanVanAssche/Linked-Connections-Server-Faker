#!/usr/bin/python3

import requests
import datetime

HOST = "http://127.0.0.1:8080"

# Test the /connections resource
now = datetime.datetime.now()
formatted_date = now.replace(tzinfo=None).isoformat()
r = requests.get(HOST + "/sncb/connections?departureTime=" + formatted_date)
r.raise_for_status()
print("/connections resource OK")

# Test the /events resource
now = datetime.datetime.now()
formatted_date = now.replace(tzinfo=None).isoformat()
r = requests.get(HOST + "/sncb/events?lastSyncTime=" + formatted_date)
r.raise_for_status()
print("/events resource OK")

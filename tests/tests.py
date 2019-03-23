#!/usr/bin/python3

import requests
import datetime
import websockets
import asyncio
from sseclient import SSEClient

PROTOCOL_HTTP = "http://"
PROTOCOL_WS = "ws://"
HOST = "127.0.0.1:8080"
now = datetime.datetime.utcnow()
formatted_date = now.replace(tzinfo=None).isoformat()

# Test the /connections resource
r = requests.get(PROTOCOL_HTTP + HOST + "/sncb/connections?departureTime=" + formatted_date)
r.raise_for_status()
print("/connections resource OK")

# Test the /events resource
r = requests.get(PROTOCOL_HTTP + HOST + "/sncb/events?lastSyncTime=" + formatted_date)
r.raise_for_status()
print("/events/poll resource OK")

# Test the /events/sse resource
r = SSEClient(PROTOCOL_HTTP + HOST + "/sncb/events/sse?lastSyncTime=" + formatted_date)
for msg in r:
    print(msg)
    break
print("/events/sse resource OK")

# Test the /events/ws resource
async def send_time(uri):
    async with websockets.connect(uri) as websocket:
        await websocket.send(formatted_date)

asyncio.get_event_loop().run_until_complete(send_time(PROTOCOL_WS + HOST + "/sncb/events/ws"))
print("/evens/ws resource OK")

# Test the /events/new resource
r = requests.post(PROTOCOL_HTTP + HOST + "/sncb/events/new", data=dict(timestamp=formatted_date,
                                                                        connectionURI="http://irail.be/connections/test",
                                                                        action="cancel"))
r.raise_for_status()
print("/events/new resource OK")

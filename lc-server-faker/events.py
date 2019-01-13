#!/usr/bin/python3

import tornado.web
import tornado.locks
import tornadose.handlers
import tornadose.stores
import dateutil
import datetime
import json
import signal
from constants import *


class BaseEventsHandler(object):
    def initialize(self, supported_agencies):
        self.supported_agencies = supported_agencies
        self.file = EVENTS_FILE
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

    def _fetch_events(self, last_sync_time):
        now_date = datetime.datetime.now().replace(tzinfo=None)
        target_date = last_sync_time.replace(tzinfo=None)
        if target_date > now_date:
            raise ValueError("lastSyncTime must be before now")

        events = {
            "lastSyncTime": target_date.replace(tzinfo=None).isoformat() + "Z",
            "@graph": []
        }

        # Read pseudorandom events JSON-LD file
        with open(self.file, "r") as json_file:
            json_data = json.load(json_file)

        # Ignore the date, only use the time
        target_date = target_date.replace(year=now_date.year,
                                          month=now_date.month,
                                          day=now_date.day)

        # Sort the events by timestamp and filter them based on the sync time
        json_data = sorted(json_data, key=lambda k: k["timestamp"])
        for c in json_data:
            current_date = dateutil.parser.parse(c["timestamp"]).replace(year=now_date.year,
                                                                         month=now_date.month,
                                                                         day=now_date.day,
                                                                         tzinfo=None)
            if target_date <= current_date <= now_date:
                events["@graph"].append(c)

        return events


class EventsHandlerHTTP(BaseEventsHandler, tornado.web.RequestHandler):
    def get(self, agency):
        # return HTTP if header is application/json, works fine
        # return SSE if header is text/event-stream, see https://gist.github.com/mivade/d474e0540036d873047f
        # return WS
        if agency in self.supported_agencies:
            try:
                last_sync_time = self.get_argument("lastSyncTime")
                last_sync_time = dateutil.parser.parse(last_sync_time)
                e = self._fetch_events(last_sync_time)
                print("Found {0} HTTP polling events".format(len(e["@graph"])))
                self.write(e)
            except ValueError:
                self.set_status(400)
                self.write(
                    {
                        "error": "Incorrect datetime format: {0}".format(self.get_argument("lastSyncTime")),
                        "status": 400
                    }
                )
        else:
            self.set_status(404)
            self.write(
                {
                    "error": "Unsupported agency: {0}".format(agency),
                    "status": 404
                }
            )


class EventsHandlerSSE(BaseEventsHandler, tornadose.handlers.EventSource):
    def initialize(self, supported_agencies):
        BaseEventsHandler.initialize(self, supported_agencies)
        tornadose.handlers.EventSource.initialize(self, tornadose.stores.QueueStore())

        # Start the event fetcher (1s) and stop it when shutting down
        self.callback = tornado.ioloop.PeriodicCallback(self._check_for_new_events, 1000)
        signal.signal(signal.SIGINT, self._shutdown)

    async def get(self, *args, **kwargs):
        # TO DO: Fetch here based on lastSyncTime parameter for each individual client
        print("Registering client, setting lastSyncTime")
        try:
            self.last_event_timestamp = dateutil.parser.parse(self.get_argument("lastSyncTime"))
            self.callback.start()
            await tornadose.handlers.EventSource.get(self, args, kwargs)
        except ValueError as e:
            print("Invalid datetime: {0}".format(e))
            self.set_status(400)

    def _check_for_new_events(self):
        e = self._fetch_events(self.last_event_timestamp)
        if len(e["@graph"]) > 0:
            print("Found {0} SSE events".format(len(e["@graph"])))
            self.store.submit(e)
            self.last_event_timestamp = datetime.datetime.now()
        else:
            print("No events yet")

    def _shutdown(self, sig, frame):
        self.callback.stop()


class EventsHandlerWS(BaseEventsHandler, tornado.websocket.WebSocketHandler):
    def initialize(self, supported_agencies):
        BaseEventsHandler.initialize(self, supported_agencies)
        self.store = tornadose.stores.QueueStore()

        # Start the event fetcher (1s) and stop it when shutting down
        self.callback = tornado.ioloop.PeriodicCallback(self._check_for_new_events, 1000)
        signal.signal(signal.SIGINT, self._shutdown)
        self.last_event_timestamp = datetime.datetime.utcnow()

    async def on_message(self, message):
        print("Message received: " + str(message))
        print("Registering client, setting lastSyncTime")
        try:
            self.last_event_timestamp = dateutil.parser.parse(message)
            self.callback.start()
        except ValueError as e:
            print("Invalid datetime: {0}".format(e))
            self._send(
                {
                    "error": "Invalid datetime: {0}".format(e),
                    "status": 400
                }
            )

    def on_closed(self):
        self._close()

    def _close(self):
        self.callback.stop()

    def check_origin(self, origin):
        # CORS header don't have any effect with WebSockets
        return True

    def _check_for_new_events(self):
        e = self._fetch_events(self.last_event_timestamp)
        if len(e["@graph"]) > 0:
            print("Found {0} WS events".format(len(e["@graph"])))
            self._send(e)
            self.last_event_timestamp = datetime.datetime.now()
        else:
            print("No events yet")

    def _shutdown(self, sig, frame):
        self._close()

    def _send(self, message):
        try:
            self.write_message(message)
        except tornado.websocket.WebSocketClosedError:
            print("WebSocket was already closed, cannot write data to it!")
            self._close()

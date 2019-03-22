#!/usr/bin/python3

import tornado.web
import tornado.locks
import tornadose.handlers
import tornadose.stores
import dateutil
import datetime
import json
import signal
import abc
from constants import *


class _BaseEventsHandler(object):
    __metaclass__ = abc.ABCMeta

    def initialize(self, supported_agencies):
        self.supported_agencies = supported_agencies
        self.file = EVENTS_FILE
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

    def _fetch_events(self, last_sync_time):
        now_date = datetime.datetime.utcnow().replace(tzinfo=None)
        try:
            target_date = last_sync_time.replace(tzinfo=None)
            if target_date > now_date:
                raise ValueError("lastSyncTime must be before now")
        except ValueError:
            self.set_status(400)
            return {
                "error": "Target date is further than now",
                "status": 400
            }

        events = {
            "@context": {
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "lc": "http://semweb.mmlab.be/ns/linkedconnections#",
            "hydra": "http://www.w3.org/ns/hydra/core#",
            "gtfs": "http://vocab.gtfs.org/terms#",
            "sosa": "http://www.w3.org/ns/sosa#",
            "Event": "sosa:Observation",
            "Connection": "lc:Connection",
            "CancelledConnection": "lc:CancelledConnection",
            "arrivalTime": {
                "@id": "lc:arrivalTime",
                "@type": "xsd:dateTime"
            },
            "departureTime": {
                "@id": "lc:departureTime",
                "@type": "xsd:dateTime"
            },
            "arrivalStop": {
                "@type": "@id",
                "@id": "lc:arrivalStop"
            },
            "departureStop": {
                "@type": "@id",
                "@id": "lc:departureStop"
            },
            "departureDelay": {
                "@id": "lc:departureDelay",
                "@type": "xsd:integer"
            },
            "arrivalDelay": {
                "@id": "lc:arrivalDelay",
                "@type": "xsd:integer"
            },
            "direction": {
                "@id": "gtfs:headsign",
                "@type": "xsd:string"
            },
            "gtfs:trip": {
                "@type": "@id"
            },
            "gtfs:route": {
                "@type": "@id"
            },
            "gtfs:pickupType": {
                "@type": "@id"
            },
            "gtfs:dropOffType": {
                "@type": "@id"
            },
            "gtfs:Regular": {
                "@type": "@id"
            },
            "gtfs:NotAvailable": {
                "@type": "@id"
            },
            "hydra:next": {
                "@type": "@id"
            },
            "hydra:previous": {
                "@type": "@id"
            },
            "hydra:property": {
                "@type": "@id"
            },
            "hydra:variableRepresentation": {
                    "@type": "@id"
                }
            },
            "@id": "http://localhost:8080/sncb/events?lastSyncTime=",
            "@type": "hydra:PartialCollectionView",
            "hydra:next": "http://localhost:8080/sncb/events?lastSyncTime=",
            "hydra:previous": "http://localhost:8080/sncb/events?lastSyncTime=",
            "hydra:search": {
                "@type": "hydra:IriTemplate",
                "hydra:template": "http://localhost:8080/sncb/events{?lastSyncTime}",
                "hydra:variableRepresentation": "hydra:BasicRepresentation",
                "hydra:mapping": {
                    "@type": "IriTemplateMapping",
                    "hydra:variable": "departureTime",
                    "hydra:required": True,
                    "hydra:property": "lc:departureTimeQuery"
                }
            },
            "@graph": []
        }

        # Read pseudorandom events JSON-LD file
        with open(self.file, "r") as json_file:
            json_data = json.load(json_file)

        # Ignore the date, only use the time
        target_date = target_date.replace(year=now_date.year,
                                          month=now_date.month,
                                          day=now_date.day)
        hydra_next_date = target_date + datetime.timedelta(minutes=10)
        hydra_previous_date = target_date - datetime.timedelta(minutes=10)
        events["hydra:next"] = events["hydra:next"] + hydra_next_date.isoformat() + ".000Z"
        events["hydra:previous"] = events["hydra:previous"] + hydra_previous_date.isoformat() + ".000Z"

        # Sort the events by timestamp and filter them based on the sync time
        json_data = sorted(json_data, key=lambda k: k["sosa:resultTime"])
        for c in json_data:
            current_date = dateutil.parser.parse(c["sosa:resultTime"]).replace(year=now_date.year,
                                                                         month=now_date.month,
                                                                         day=now_date.day,
                                                                         tzinfo=None)
            if target_date <= current_date <= now_date:
                events["@graph"].append(c)

        return events


class _PushHandler(_BaseEventsHandler):
    __metaclass__ = abc.ABCMeta

    def initialize(self, supported_agencies):
        _BaseEventsHandler.initialize(self, supported_agencies)
        # Start the event fetcher (1s) and stop it when shutting down
        self.callback = tornado.ioloop.PeriodicCallback(self._check_for_new_events, 1000)
        signal.signal(signal.SIGINT, self._shutdown)
        self.last_event_timestamp = datetime.datetime.utcnow()

    def _check_for_new_events(self):
        e = self._fetch_events(self.last_event_timestamp)
        if len(e["@graph"]) > 0:
            print("Found {0} events".format(len(e["@graph"])))
            self._send(e)
            self.last_event_timestamp = datetime.datetime.utcnow()
        else:
            print("No events yet")

    def _shutdown(self, sig, frame):
        self._close()

    @abc.abstractmethod
    def _send(self, message):
        raise NotImplementedError("You must implement the _send() method")

    def _close(self):
        print("Cleaning up")
        self.callback.stop()


class EventsHandlerStatic(_PushHandler):
    def initialize(self, supported_agencies):
        _PushHandler.initialize(self. supported_agencies)
        # Start the callback immediately
        self.callback.start()

    def _send(self, message):
        print("Received new connections, updating static")
        for c in message["@graph"]:
            # Search for the page and the next page

            # Update the connection if departureTime (including delay) < next page time

            # Move connection to the next page if departureTime (including delay) <= next page time

            pass


class EventsHandlerHTTP(_BaseEventsHandler, tornado.web.RequestHandler):
    def get(self, agency):
        # return HTTP if header is application/json, works fine
        # return SSE if header is text/event-stream, see https://gist.github.com/mivade/d474e0540036d873047f
        # return WS
        if agency in self.supported_agencies:
            try:
                last_sync_time = self.get_argument("lastSyncTime")
                last_sync_time = dateutil.parser.parse(last_sync_time)
                e = self._fetch_events(last_sync_time)
                if "@graph" in e:
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


class EventsHandlerSSE(_PushHandler, tornadose.handlers.EventSource):
    def initialize(self, supported_agencies):
        _PushHandler.initialize(self, supported_agencies)
        tornadose.handlers.EventSource.initialize(self, tornadose.stores.QueueStore())

    async def get(self, agency):
        if agency in self.supported_agencies:
            print("Registering client, setting lastSyncTime")
            try:
                self.last_event_timestamp = dateutil.parser.parse(self.get_argument("lastSyncTime"))
                self.callback.start()
                await tornadose.handlers.EventSource.get(self)
            except ValueError as e:
                print("Invalid datetime: {0}".format(e))
                self.set_status(400)
        else:
            self.set_status(404)
            self.store.submit(
                {
                    "error": "Unsupported agency: {0}".format(agency),
                    "status": 404
                }
            )

    def _shutdown(self, sig, frame):
        self._close()

    def _send(self, message):
        self.store.submit(message)


class EventsHandlerWS(_PushHandler, tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        # CORS header don't have any effect with WebSockets
        return True

    def on_message(self, message):
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

    def on_close(self):
        self._close()

    def _send(self, message):
        try:
            self.write_message(message)
        except tornado.websocket.WebSocketClosedError:
            print("WebSocket was already closed, cannot write data to it!")
            self._close()


class EventsHandlerNew(_BaseEventsHandler, tornado.web.RequestHandler):
    def post(self, agency):
        if agency in self.supported_agencies:
            print("POST event received")
            timestamp = self.get_argument("timestamp")
            connection_uri = self.get_argument("connectionURI")
            action = self.get_argument("action")
            print("TIMESTAMP=" + str(timestamp))
            print("CONNECTION URI=" + str(connection_uri))
            print("ACTION=" + str(action))
            self._add_event(timestamp, connection_uri, action)
            self.write({
                "status": 200
            })
        else:
            self.set_status(404)
            self.store.submit(
                {
                    "error": "Unsupported agency: {0}".format(agency),
                    "status": 404
                }
            )

    def _add_event(self, timestamp, connection_uri, action):
        print("Adding event")
        try:
            # Open the events file
            with open(EVENTS_FILE, "r") as json_file:
                events = json.load(json_file)

            # Create the event and add it to graph
            e = {
                "timestamp": timestamp,
                "connectionURI": connection_uri
            }
            events.append(e)
            events = sorted(events, key=lambda k: k["timestamp"])

            # Save all events to the events file
            with open(EVENTS_FILE, "w") as json_file:
                json.dump(events, json_file)
        except Exception as e:
            print("Adding event FAILED: {0}".format(e))

#!/usr/bin/python3

import tornado.web
import os
import datetime
import dateutil
import json


class ConnectionsHandler(tornado.web.RequestHandler):
    def initialize(self, supported_agencies):
        self.supported_agencies = supported_agencies
        self.files = []
        for f in os.listdir("connections"):
            path = os.path.join("connections", f)
            if os.path.isfile(path):
                self.files.append(path)
        self.files.sort()

    def get(self, agency):
        if agency in self.supported_agencies:
            departure_time = self.get_argument("departureTime")
            print("Got departureTime: " + departure_time)
            self.write(self._find_fragment(departure_time))
        else:
            self.set_status(404)
            self.write(
                {
                    "error": "Unsupported agency: {0}".format(agency),
                    "status": 404
                }
            )

    def _find_fragment(self, departure_time):
        target_date = dateutil.parser.parse(departure_time).replace(tzinfo=None)
        target_file = None

        for i in range(0, len(self.files) - 1):
            current_file = self.files[i]
            next_file = self.files[i + 1]
            current_date = dateutil.parser.parse(os.path.basename(os.path.splitext(current_file)[0])).replace(
                tzinfo=None)
            next_date = dateutil.parser.parse(os.path.basename(os.path.splitext(next_file)[0])).replace(tzinfo=None)

            # Ignore the date, only use the time
            if current_date <= target_date.replace(year=current_date.year, month=current_date.month,
                                                  day=current_date.day) < next_date:
                print("Target date: {0}, between files: {1} and {2}".format(departure_time, current_file, next_file))
                target_file = current_file
                break

        with open(target_file, "r") as json_file:
            json_data = json.load(json_file)

        # Return JSON data
        return json_data

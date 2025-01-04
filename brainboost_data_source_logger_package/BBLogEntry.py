# BBLogEntry.py

import csv
import io
import json

class BBLogEntry:
    def __init__(self, process, timestamp, log_type, message, processing_time, code_location,config=None):
        self.timestamp = timestamp
        self.log_type = log_type
        self.process = process
        self.code_location = code_location
        self.message = message
        self.processing_time = processing_time
        self.config = config

    def __str__(self):
        # Use csv module to handle proper escaping
        output = io.StringIO()
        writer = csv.writer(output, delimiter=BBConfig.get('log_delimiter'), quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writerow([
            self.timestamp,
            self.log_type,
            self.process,
            self.code_location,
            self.message,
            self.processing_time
        ])
        return output.getvalue().strip()


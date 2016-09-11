#!/usr/bin/env python
import logging
import re
import itertools
import datetime
import csv
from logentry import LogEntry


class ParseCsv:

    # Example config will look like this
    # Note indicator_<type> is ioc field, date is date and optional, desc_<int> are desc columns and optional
    # fieldnames, data_types, control are required fields
    # "config": {
    #     "fieldnames": ["date", "indicator_ipv4", "desc_1", "desc_2"],
    #     "data_types": ["ipv4"]
    #     "control": "inbound"
    #     "delimiter": ",",
    #     "doublequote": T|F,
    #     "escapechar": "",
    #     "quotechar": "",
    #     "skipinitialspace": T|F
    # }
    # data is a generator or a list of lines

    def __init__(self, config, event, data):

        self.fieldnames = config.get('fieldnames')
        self.data_types = config.get('data_types')
        self.control = config.get('control')
        self.event = event
        self.data = data
        self.dialect = {
            'delimiter': config.get('delimiter', ','),
            'doublequote': config.get('doublequote', True),
            'escapechar': config.get('escapechar', None),
            'quotechar': config.get('quotechar', '"'),
            'skipinitialspace': config.get('skipinitialspace', False)
        }

    def run(self):
        reader = csv.DictReader(
            self.data,
            fieldnames=self.fieldnames,
            **self.dialect
        )

        entries = []
        for row in reader:
            for data_type in self.data_types:
                desc_val = []
                ioc = row.get('indicator_%s' % data_type)
                if not ioc:
                    continue
                for i in xrange(1,10):
                    tmp = row.get('desc_%s' % i)
                    if tmp:
                        desc_val.append(tmp)
                entry = LogEntry(self.event, data_type, ioc, self.control, ';'.join(desc_val)).new()
                if 'date' in row:
                    entry['date'] = row['date']
                entries.append(entry)

        return entries


class ParseText:

    def __init__(self):
        pass



#!/usr/bin/env python
import logging
import re
import itertools
import datetime
import csv
from logentry import ResultsDict
from app import app


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
        count = 0
        app.logger.info("Processing ParseCsv")
        reader = csv.DictReader(
            self.data,
            fieldnames=self.fieldnames,
            **self.dialect
        )

        results = ResultsDict(self.event, self.control)
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
                log_date = row.get('date')
                results.new_ind(data_type=data_type,
                                indicator=ioc,
                                date=log_date,
                                description=';'.join(desc_val))
            count += 1
        app.logger.info("ParseCsv processed %s rows", count)
        return results


class ParseText:
    # Example config will look like this
    # Regex will need to have named capture groups the name are as follows:
    #   indicator_<type> is ioc field,
    #   date is date and optional,
    #   desc_<int> are desc columns and optional
    # data_types, control, and regex are required in json config
    # "config": {
    #     "data_types": ["ipv4"]
    #     "control": "inbound"
    #     "regex": "^(?P<date>[^,]+),(?P<indicator_ipv4>[^,]+),(?P<desc>[^,]+)"
    # }
    # data is a generator or a list of lines

    def __init__(self, config, event, data):
        self.data_types = config.get('data_types', [])
        self.control = config.get('control')
        self.regex = config.get('regex')
        self.event = event
        self.data = data

    def run(self):
        count = 0
        app.logger.info("Processing ParseText")
        rex = re.compile(self.regex)
        results = ResultsDict(self.event, self.control)
        for row in self.data:
            m = rex.search(row)
            if not m:
                app.logger.warn("Row did not match regex: %s", row)
                continue
            matches = m.groupdict()
            for data_type in self.data_types:
                desc_val = []
                desc = None
                ioc = matches.get('indicator_%s' % data_type)
                if not ioc:
                    app.logger.warn("no indicator found for: %s", data_type)
                    continue
                for i in xrange(1,10):
                    tmp = matches.get('desc_%s' % i)
                    if tmp:
                        desc_val.append(tmp)
                log_date = matches.get('date')
                if len(desc_val) > 0:
                    print 'val: %s' % desc_val
                    desc = ';'.join(desc_val)
                results.new_ind(data_type=data_type,
                                indicator=ioc,
                                date=log_date,
                                description=desc)
            count += 1
        app.logger.info("ParseText processed %s lines", count)
        return results




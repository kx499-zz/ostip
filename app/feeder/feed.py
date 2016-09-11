#!/usr/bin/env python
import json


FEED_CONFIG = 'feed.json'


def _dynamic_load(class_name):
    if '.' not in class_name:
        raise ValueError('invalid absolute classname %s' % class_name)

    modname, class_name = class_name.rsplit('.', 1)
    t = __import__(modname, globals(), locals(), [class_name])
    cls = getattr(t, class_name)
    return cls


class Feed:

    def __init__(self):
        try:
            with open(FEED_CONFIG) as F:
                json_data = F.read()
                self.configs = json.loads(json_data)
        except Exception, e:
            print 'Error Loading File'

    def process_all(self):
        logs = {}
        for config in self.configs:
            modules = config.get('modules')
            if not modules:
                print "bad json"
                continue

            if 'parse' in modules.keys() and 'collect' in modules.keys():
                try:
                    print modules['collect'].get('name')
                    coll_cls = _dynamic_load(modules['collect'].get('name'))
                    parse_cls = _dynamic_load(modules['parse'].get('name'))
                except Exception, e:
                    print 'error loading classes: %s' % e
                    continue

                collect_config = modules['collect'].get('config')
                parse_config = modules['parse'].get('config')
                if not collect_config and not parse_config:
                    print 'error loading configs'
                    continue

                collector = coll_cls(collect_config)
                data = collector.get()
                if not data:
                    print 'error loading data'
                    continue

                parser = parse_cls(parse_config, 1, data)
                logs[config['name']] = parser.run()

        return logs









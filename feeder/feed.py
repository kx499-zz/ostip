import json
import os
from app.utils import _add_indicators, _valid_json
from app import app
basedir = os.path.abspath(os.path.dirname(__file__))

FEED_CONFIG = app.config.get('FEED_CONFIG')


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
            print 'Error Loading File: %s' % e

    def process_all(self):
        results = {}
        fields = ['name', 'frequency', 'event_id', 'modules']
        for config in self.configs:
            if not _valid_json(fields, config):
                app.logger.warn('Bad config from feed.json')
                continue
            modules = config.get('modules')
            event_id = config.get('event_id')

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

                parser = parse_cls(parse_config, event_id, data)
                logs = parser.run()
                results[config.get('name','n/a')] = _add_indicators(logs)
            elif 'custom' in modules.keys():
                pass
            else:
                app.logger.warn('Bad config from feed.json in modules')
                continue

        return results












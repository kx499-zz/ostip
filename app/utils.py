from app import db
from app import app
from .models import Indicator, Control, Itype, Links
import re


def _load_related_data(data):
    ioc = {}
    items = Indicator.query.filter_by(event_id=data['event_id']).all()
    [ioc.update({item.ioc: item.id}) for item in items]
    control = Control.query.filter_by(name=data['control']).first()
    data_types = {}
    d_items = Itype.query.all()
    [data_types.update({d_item.name: [d_item, d_item.regex]}) for d_item in d_items]
    if 'data_type' in data.keys():
        data_type = data_types.get(data['data_type'][0])
        if not control and data_type:
            raise Exception("Data Type or Control not found")
        return ioc, control, data_type
    else:
        if not control:
            raise Exception("Data Type or Control not found")
        return ioc, control, data_types


def _correlate(indicator_list):
    # not yet implemented
    for ind_id, ev_id, val in indicator_list:
        for i in Indicator.query.filter_by(ioc=val).all():
            if i.id != ind_id:
                link = Links(ev_id, ind_id, i.event_id, i.id)
                link2 = Links(i.event_id, i.id, ev_id, ind_id)
                db.session.add(link)
                db.session.add(link2)
    db.session.commit()

def _enrich_data(data):
    results = None
    if data['pending']:
        #impliment
        return "Not Implemented Yet"

def _valid_json(fields, data_dict):
    if all(k in data_dict for k in fields):
        for field in fields:
            if re.search('_id$', field):
                return True

    return False


def _add_indicators(results, pending=False):
    inserted_indicators = []
    failed_indicators = []
    fields = ['event_id', 'control', 'indicators']
    if not _valid_json(fields, results):
        app.logger.warn('Bad json passed to _add_indicators')
        return {'success':len(inserted_indicators), 'failed':len(failed_indicators)}

    ioc_list, cont_obj, data_types = _load_related_data(results)
    for data_type, indicators in results['indicators'].iteritems():
        type_array = data_types.get(data_type)
        if not type_array:
            app.logger.log("Bulk Indicator: Non-existent data type: %s can't process" % data_type)
            continue
        regex = type_array[1]
        if regex:
            regex = re.compile(type_array[1])
        type_obj = type_array[0]
        for i in indicators:
            val = i['indicator']
            dt = i['date']
            desc = i['description']
            ind_id = ioc_list.get(val)
            if ind_id:
                ind = Indicator.query.get(ind_id)
                ind.last_seen = dt
            else:
                if (regex and regex.match(val)) or regex is None:
                    ind = Indicator(results['event_id'], val, desc, cont_obj, type_obj, pending, 'Not Processed')
                    db.session.add(ind)
                    db.session.flush()
                    ind_id = ind.id
                    inserted_indicators.append([ind_id, results['event_id'], val])
                else:
                    failed_indicators.append([0, results['event_id'], val])

    # commit and correlate
    try:
        db.session.commit()
        if not pending:
            _correlate(inserted_indicators)
    except Exception, e:
        db.session.rollback()
        app.logger.warn('Error committing indicators: %s' % e)
        failed_indicators += inserted_indicators
        inserted_indicators = []

    return {'success':len(inserted_indicators), 'failed':len(failed_indicators)}

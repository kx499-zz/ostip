from app import db
from app import app
from .models import Indicator, Control, Itype, Links
from feeder.logentry import ResultsDict
import re


def _load_related_data(data):
    ioc = {}
    items = Indicator.query.filter_by(event_id=data.event_id).all()
    [ioc.update({item.ioc: item.id}) for item in items]

    data_types = {}
    d_items = Itype.query.all()
    [data_types.update({d_item.name: [d_item, d_item.regex]}) for d_item in d_items]

    control = Control.query.filter_by(name=data.control).first()
    if not control:
        raise Exception("Control not found")

    for dt in data.data_types.keys():
        data_type = data_types.get(dt)
        if not data_type:
            raise Exception("Data Type not found")

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
    reasons = []
    inserted_indicators = []
    failed_indicators = []
    updated_indicators = []
    if not isinstance(results, ResultsDict):
        app.logger.warn('Bad object passed to _add_indicators')
        return {'success':len(inserted_indicators), 'failed':len(failed_indicators), 'reason':';'.join(reasons)}

    ioc_list, cont_obj, all_data_types = _load_related_data(results)
    for data_type in results.data_types.keys():
        type_array = all_data_types.get(data_type)
        if not type_array:
            app.logger.warn("Bulk Indicator: Non-existent data type: %s can't process" % data_type)
            reasons.append('Bad Data Type')
            failed_indicators.append([0, results.event_id, [i for i in results.data_types.get(data_type, {}).keys()]])
            continue
        regex = type_array[1]
        if regex:
            regex = re.compile(type_array[1])
        type_obj = type_array[0]
        indicators = results.data_types.get(data_type)
        for i in indicators.keys():
            print i
            val = i
            dt = indicators[i]['date']
            desc = indicators[i]['description']
            ind_id = ioc_list.get(val)
            if ind_id:
                ind = Indicator.query.get(ind_id)
                ind.last_seen = dt
                updated_indicators.append([ind_id, results.event_id, val])
            else:
                if (regex and regex.match(val)) or regex is None:
                    ind = Indicator(results.event_id, val, desc, cont_obj, type_obj, pending, 'Not Processed')
                    db.session.add(ind)
                    db.session.flush()
                    ind_id = ind.id
                    inserted_indicators.append([ind_id, results.event_id, val])
                else:
                    reasons.append('Validation Failed')
                    failed_indicators.append([0, results.event_id, val])

    # commit and correlate
    try:
        db.session.commit()
        if not pending:
            _correlate(inserted_indicators)
    except Exception, e:
        db.session.rollback()
        app.logger.warn('Error committing indicators: %s' % e)
        reasons.append('Commit Failed')
        failed_indicators += inserted_indicators
        inserted_indicators = []

    return {'success':len(inserted_indicators) + len(updated_indicators), 'failed':len(failed_indicators), 'reason':';'.join(reasons)}

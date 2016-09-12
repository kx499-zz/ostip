from app import db
from .models import Event, Indicator, Control, Itype, Links
import datetime


def _load_related_data(data):
    ioc = {}
    items = Indicator.query.filter_by(event_id=data['event_id']).all()
    [ioc.update({item.ioc: item.id}) for item in items]
    control = Control.query.filter_by(name=data['control']).first()
    if 'data_type' in data.keys():
        data_type = Itype.query.filter_by(name=data['data_type']).first()
        if not control and data_type:
            raise Exception("Data Type or Control not found")
        return ioc, control, data_type
    else:
        if not control:
            raise Exception("Data Type or Control not found")
        return ioc, control


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


def _add_indicators(results):
    ioc_list, cont_id = _load_related_data(results)

    inserted_indicators = []
    for data_type, indicators in results['indicators'].iteritems():
        type_id = Itype.query.filter_by(name=data_type).first()
        for i in indicators:
            val = i['indicator']
            dt = i['date']
            desc = i['description']
            ind_id = ioc_list.get(val)
            if ind_id:
                ind = Indicator.query.get(ind_id)
                ind.last_seen = dt
            else:
                ind = Indicator(results['event_id'], val, desc, cont_id, type_id, False, 'Not Processed')
                db.session.add(ind)
                db.session.flush()
                ind_id = ind.id
                inserted_indicators.append([ind_id, results['event_id'], val])

    # commit and correlate
    db.session.commit()
    _correlate(inserted_indicators)
    return inserted_indicators

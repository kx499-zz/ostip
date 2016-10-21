from flask import render_template, flash, redirect, request, jsonify, json, escape
from sqlalchemy.exc import IntegrityError
from app import app
from .forms import EventForm, IndicatorForm, NoteForm, ItypeForm, FeedConfigForm, IndicatorEditForm, MitigationForm
from feeder.logentry import  ResultsDict
from .models import Event, Indicator, Itype, Control, Level, Likelihood, Source, Status, Tlp, Note, Mitigation, db
from .utils import _valid_json, _add_indicators, _correlate, filter_query
from .my_datatables import ColumnDT, DataTables


def _count(chain):
    ret = chain.count()
    if ret:
        return ret
    else:
        return chain





@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/event/add', methods=['GET', 'POST'])
def event_add():
    form = EventForm()
    form.confidence.choices = [(i, '%s' % i) for i in xrange(0, 100, 5)]
    if form.validate_on_submit():
        ev = Event(form.name.data,
                   form.details.data,
                   form.source.data,
                   form.tlp.data,
                   form.impact.data,
                   form.likelihood.data,
                   form.confidence.data)
        db.session.add(ev)
        try:
            db.session.commit()
            flash('Event added')
        except IntegrityError:
            db.session.rollback()
            flash('Commit Error')
        return redirect('/index')
    print(form.errors)
    return render_template('event_add.html',
                           title='Add Event',
                           form=form)


@app.route('/event/view/<int:event_id>', methods=['GET', 'POST'])
def event_view(event_id):
    def _indicator_add(form):
        res_dict = ResultsDict(form.event_id.data,
                    form.control.data.name)
        res_dict.new_ind(data_type=form.itype.data.name,
                         indicator=form.ioc.data,
                         date=None,
                         description=form.comment.data)
        r = _add_indicators(res_dict, False, True)
        print r
        if r.get('success', 0) == 1:
            res = '"%s" indicator submitted' % form.ioc.data
        else:
            res = '"%s" indicator not submitted: %s' % (form.ioc.data, r.get('reason', 'N/A'))
        return res

    def _note_add(form):
        note = Note(form.event_id.data, form.details.data)
        db.session.add(note)
        try:
            db.session.commit()
            res = 'note submitted'
        except IntegrityError:
            db.session.rollback()
            res = 'note not submitted'
        return res

    def _event_edit(form, event):
        form.populate_obj(event)
        try:
            db.session.commit()
            res = '"%s" Event Updated' % event.id
        except IntegrityError:
            db.session.rollback()
            res = '"%s" Event Not Updated' % event.id
        return res

    ev = Event.query.get(event_id)
    ind_form = IndicatorForm()
    ind_form.event_id.data = event_id
    ev_form = EventForm(obj=ev)
    ev_form.confidence.choices = [(i, '%s' % i) for i in xrange(0, 100, 5)]
    nt_form = NoteForm()
    nt_form.event_id.data = event_id
    if ind_form.validate_on_submit():
        flash(_indicator_add(ind_form))
        return redirect('/event/view/%s' % event_id)
    elif ev_form.validate_on_submit():
        flash(_event_edit(ev_form, ev))
        return redirect('/event/view/%s' % event_id)
    elif nt_form.validate_on_submit():
        flash(_note_add(nt_form))
        return redirect('/event/view/%s' % event_id)
    return render_template('event_view.html',
                           title='View Event',
                           event=ev,
                           form=ind_form,
                           ev_form=ev_form,
                           nt_form=nt_form)


@app.route('/indicator/pending/view', methods=['GET', 'POST'])
def indicator_pending():
    if request.method == 'POST':
        update_list = [int(i) for i in request.form.getlist('selected')]
        del_list = [int(i) for i in request.form.getlist('not_selected')]

        upd_query = db.session.query(Indicator).filter(Indicator.id.in_(update_list))
        upd_query.update({'pending':False}, synchronize_session=False)
        del_query = db.session.query(Indicator).filter(Indicator.id.in_(del_list))
        del_query.delete(synchronize_session=False)
        try:
            db.session.commit()
            flash('Indicators updated')
        except IntegrityError:
            db.session.rollback()
            flash('Commit Error')
            return redirect('/indicator/pending/view')

        ioc_query = Indicator.query.with_entities(Indicator.id, Indicator.event_id, Indicator.ioc)
        ioc_list = ioc_query.filter(Indicator.id.in_(update_list)).all()
        _correlate(ioc_list)
        return redirect('/indicator/pending/view')


    return render_template('indicator_pending.html', title='Pending Indicators')


@app.route('/indicator/edit/<int:ind_id>/<action>', methods=['GET', 'POST'])
def indicator_edit(ind_id, action):
    i = Indicator.query.get(ind_id)
    form = IndicatorEditForm(obj=i)
    m_form = MitigationForm()
    m_form.ttl.choices = [(c, '%s' % c) for c in [0,7,30,90]]
    if request.method == 'POST' and action=='view' and form.validate_on_submit():
        if request.form['submit'] == 'edit':
            i.comment = form.comment.data
            i.control = form.control.data
            db.session.add(i)
        elif request.form['submit'] == 'delete':
            db.session.delete(i)
        try:
            db.session.commit()
            flash("Indicator updated successfully")
        except Exception, e:
            db.session.rollback()
            app.logger.warn("Error committing - rolled back %s" % e)
            flash("Error committing - rolled back")
        return redirect('/indicator/edit/%s/view' % ind_id)
    elif request.method == 'POST' and action.startswith('mitigation') and m_form.validate_on_submit():
        if action == 'mitigation_add':
            print m_form.destination.data.id, m_form.ttl.data, m_form.description.data
            mit = Mitigation(m_form.destination.data.id, m_form.ttl.data, m_form.description.data)
            i.mitigations.append(mit)
        elif action == 'mitigation_edit':
            mit = Mitigation.query.get(m_form.mit_id.data)
            if not mit:
                flash("Mitigation doesn't exist")
                return redirect('/indicator/edit/%s/view' % ind_id)
            mit.ttl = m_form.ttl.data
            mit.destination_id = m_form.destination.data.id
            mit.description = m_form.description.data
            db.session.add(mit)
        elif action == 'mitigation_del':
            print 'hit here'
            mit = Mitigation.query.get(m_form.mit_id.data)
            db.session.delete(mit)
        else:
            flash("Knock off the funny business....")
            return redirect('/indicator/edit/%s/view' % ind_id)

        try:
            db.session.commit()
            flash("Mitigation successfully updated/added")
        except Exception, e:
            db.session.rollback()
            app.logger.warn("Error committing mitigation - rolled back %s" % e)
            flash("Error committing - rolled back")
        return redirect('/indicator/edit/%s/view' % ind_id)
    print m_form.errors
    return render_template('indicator_edit.html', title='Edit Indicator', form=form, m_form=m_form, indicator=i)


@app.route('/indicator/search/view', methods=['GET', 'POST'])
def indicator_search():
    return render_template('indicator_search.html', title='Search Indicators')


@app.route('/admin/data_types/<action>', methods=['GET', 'POST'])
def admin_data_types(action):
    form = ItypeForm()
    print '%s' % request.form
    if action == 'view':
        data_types = Itype.query.all()
        return render_template('type_edit.html', title='View/Edit Fields', data_types=data_types, form=form)
    elif action == 'add':
        dt = Itype(request.form['field_name'], request.form['field_regex'])
        if dt.regex == 'None' or dt.regex == '':
            dt.regex = None
        db.session.add(dt)
    elif action == 'edit':
        dt = Itype.query.get(request.form['field_id'])
        dt.name = request.form['field_name']
        dt.regex = request.form['field_regex']
        if dt.regex == 'None' or dt.regex == '':
            dt.regex = None
        db.session.add(dt)
    elif action == 'delete':
        dt = Itype.query.get(request.form['field_id'])
        db.session.delete(dt)
    else:
        return redirect('/admin/data_types/view')
    try:
        db.session.commit()
        flash('Data Types Updated')
    except IntegrityError:
        db.session.rollback()
        flash('Commit Error')
    return redirect('/admin/data_types/view')


@app.route('/admin/table/view', methods=['GET', 'POST'])
def view_fields():
    fields = {'Impact': [Level.query.all(), 'impact'],
              'Likelihood': [Likelihood.query.all(), 'likelihood'],
              'Data Source': [Source.query.all(), 'source'],
              'Event Status': [Status.query.all(), 'status'],
              'TLP': [Tlp.query.all(), 'tlp'],
              'Controls': [Control.query.all(), 'control']
              }
    return render_template('table_view.html', title='View/Edit Fields', fields=fields)


@app.route('/admin/table/<table_name>/<action>', methods=['POST'])
def view_edit_table(table_name, action):
    objects = {'impact': Level(),
               'likelihood': Likelihood(),
               'source': Source(),
               'status': Status(),
               'tlp': Tlp(),
               'control': Control()}
    if table_name in objects.keys():
        base_obj = objects[table_name]
    else:
        return redirect('/fields/view')

    if action == 'add':
        base_obj.name = request.form['field_name']
        db.session.add(base_obj)
    elif action == 'edit':
        item = base_obj.query.get(request.form['field_id'])
        item.name = request.form['field_name']
        db.session.add(item)
    elif action == 'delete':
        item = base_obj.query.get(request.form['field_id'])
        db.session.delete(item)
    else:
        return redirect('/admin/table/view')
    try:
        db.session.commit()
        flash('Data Updated')
    except IntegrityError:
        db.session.rollback()
        flash('Commit Error')

    return redirect('/admin/table/view')


@app.route('/feeds/config/<action>', methods=['GET', 'POST'])
def feed_config(action):
    with open(app.config.get('FEED_CONFIG')) as F:
        data = F.read()
    data = json.loads(data.replace('\\', '\\\\'))
    if action == 'view':
        form_edit = FeedConfigForm()
        for d in data:
            e = Event.query.get(d['event_id'])
            if not e:
                pass
            d['event_name'] = Event.query.get(d['event_id']).name
            d['modules'] = json.dumps(d['modules'], indent=4, sort_keys=True).replace('\\\\', '\\')
        return render_template('feed_config.html', title='Feed Config', data=data, form_edit=form_edit)

    elif action == 'edit':
        try:
            idx = int(request.form['index_id'])
            evt_id = int(request.form['event'])
        except Exception:
            flash('Error converting IDs to integers')
            return redirect('/feeds/config/view')
        d = data[idx]
        d['name'] = request.form['name']
        d['frequency'] = request.form['frequency']
        d['event_id'] = evt_id
        modules = request.form['module']
        if modules:
            try:
                d['modules'] = json.loads(modules.replace('\\', '\\\\'))
            except Exception, e:
                flash('Invalid JSON for module config')
                return redirect('/feeds/config/view')

    elif action == 'add':
        try:
            evt_id = int(request.form['event'])
        except Exception:
            flash('Error converting ID to integer')
            return redirect('/feeds/config/view')
        d = dict()
        d['name'] = request.form['name']
        d['frequency'] = request.form['frequency']
        d['event_id'] = evt_id
        modules = request.form['module']
        if modules:
            try:
                d['modules'] = json.loads(modules.replace('\\', '\\\\'))
            except Exception, e:
                flash('Invalid JSON for module config')
                return redirect('/feeds/config/view')
        data.append(d)

    elif action == 'del':
        try:
            idx = int(request.form['index_id'])
        except Exception:
            flash('Error converting IDs to integers')
            return redirect('/feeds/config/view')
        data.pop(idx)

    try:
        json_data = json.dumps(data, indent=4, sort_keys=True)
        with open(app.config.get('FEED_CONFIG'), 'w') as F:
            F.write(json_data.replace('\\\\', '\\'))
    except Exception, e:
        flash('Error writing file: %s' % e)

    return redirect('/feeds/config/view')


###
# DataTables Ajax Endpoints
###
@app.route('/indicator/<status>/data/<int:event_id>')
def pending_data(status, event_id):
    """Return server side data."""
    # defining columns
    columns = []
    columns.append(ColumnDT('id'))
    columns.append(ColumnDT('ioc'))
    columns.append(ColumnDT('itype.name'))
    columns.append(ColumnDT('control.name'))
    columns.append(ColumnDT('comment'))
    columns.append(ColumnDT('enrich'))
    columns.append(ColumnDT('first_seen'))

    base_query = db.session.query(Indicator).join(Control).join(Itype)

    if status == 'pending':
        columns.append(ColumnDT('event_id'))
        columns.append(ColumnDT('event.name'))
        query = base_query.join(Event).filter(Indicator.pending == True)
    elif status == 'search':
        columns.append(ColumnDT('event_id'))
        columns.append(ColumnDT('event.name'))
        query = base_query.join(Event).filter(Indicator.pending == False)
    elif status == 'approved':
        columns.append(ColumnDT('last_seen'))
        columns.append(ColumnDT('rel_list'))
        query = base_query.filter(Indicator.event_id == event_id).filter(Indicator.pending == False )
    else:
        query = base_query.filter(Indicator.pending == True)

    rowTable = DataTables(request.args, Indicator, query, columns)

    #xss catch just to be safe
    res = rowTable.output_result()
    for item in res['data']:
        for k,v in item.iteritems():
            item[k] = escape(v)

    return jsonify(res)


@app.route('/event/<status>/data')
def event_data(status):
    """Return server side data."""
    # defining columns
    columns = []
    columns.append(ColumnDT('id'))
    columns.append(ColumnDT('name'))
    columns.append(ColumnDT('status.name'))
    columns.append(ColumnDT('source.name'))
    columns.append(ColumnDT('tlp.name'))
    columns.append(ColumnDT('confidence'))
    columns.append(ColumnDT('created'))
    columns.append(ColumnDT('indicator_count'))

    base_query = db.session.query(Event).join(Source).join(Tlp).join(Status)

    if status in ['New', 'Open', 'Resolved']:
        query = base_query.filter(Status.name == status)
    else:
        query = base_query

    rowTable = DataTables(request.args, Event, query, columns)

    #xss catch just to be safe
    res = rowTable.output_result()
    for item in res['data']:
        for k,v in item.iteritems():
            item[k] = escape(v)

    return jsonify(res)


###
# API Calls
###
@app.route('/api/event/add', methods=['POST'])
def api_event_add():
    req_keys = ('name', 'details', 'confidence', 'source', 'tlp', 'impact', 'likelihood')

    try:
        pld = request.get_json(silent=True)
    except Exception, e:
        return json.dumps({'results': 'error', 'data': '%s' % e})

    if _valid_json(req_keys, pld):
        impact = Level.query.filter(Level.name == pld['impact']).first()
        likelihood = Likelihood.query.filter(Likelihood.name == pld['likelihood']).first()
        source = Source.query.filter(Source.name == pld['source']).first()
        tlp = Tlp.query.filter(Tlp.name == pld['tlp']).first()
        if not (impact and likelihood and source and tlp):
            return json.dumps({'results': 'error', 'data': 'impact, likelihood, source, or tlp not found'})

        try:
            confidence = int(pld['confidence'])
            if confidence < 0 or  confidence > 100:
                raise Exception
        except Exception, e:
            return json.dumps({'results': 'error', 'data': 'confidence was not a number between 0 and 100'})

        ev = Event(pld['name'], pld['details'], source, tlp, impact, likelihood, confidence)
        db.session.add(ev)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return json.dumps({'results': 'error', 'data': 'Integrity error - Rolled back'})
        return json.dumps({'results':'success', 'data':{'event_id': ev.id}})
    else:
        return json.dumps({'results': 'error', 'data': 'bad json'})


@app.route('/api/indicator/bulk_add', methods=['POST'])
def indicator_bulk_add():
    req_keys = ('control', 'data_type', 'event_id', 'pending', 'data')

    try:
        pld = request.get_json(silent=True)
    except Exception, e:
        return json.dumps({'results': 'error', 'data': '%s' % e})

    if _valid_json(req_keys, pld):
        # load related stuff
        res_dict = ResultsDict(pld['event_id'], pld['control'])
        for val, desc in pld['data']:
            res_dict.new_ind(data_type=pld['data_type'],
                             indicator=val,
                             date=None,
                             description=desc)

        results = _add_indicators(res_dict, pld['pending'])
        return json.dumps({'results': 'success', 'data': results})
    else:
        return json.dumps({'results': 'error', 'data': 'bad json'})


@app.route('/api/indicator/get', methods=['POST'])
def api_indicator_get():
    req_keys = ('conditions',)
    req_keys2 = ('field', 'operator', 'val')
    try:
        pld = request.get_json(silent=True)
    except Exception, e:
        return json.dumps({'results': 'error', 'data': '%s' % e})

    if not _valid_json(req_keys, pld):
        return json.dumps({'results': 'error', 'data': 'Invalid json'})

    for item in pld.get('conditions'):
        if not _valid_json(req_keys2, item):
            return json.dumps({'results': 'error', 'data': 'Invalid json'})

    q = filter_query(Indicator.query.join(Event), pld.get('conditions'))



@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)


from app import views, models

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    #acces logs
    logger = logging.getLogger('werkzeug')
    handler = RotatingFileHandler('tmp/ostip_access.log', 'a', 1 * 1024 * 1024, 10)
    logger.addHandler(handler)

    #error/app info logs
    file_handler = RotatingFileHandler('tmp/ostip.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('OSTIP startup')

def create_celery_app(app):
    app = app
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    Taskbase = celery.Task

    class ContextTask(Taskbase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return Taskbase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery




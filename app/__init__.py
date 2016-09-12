from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)


from app import views, models

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




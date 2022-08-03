import os
from elasticapm.contrib.flask import ElasticAPM

apm = ElasticAPM(logging=True)


def init_app(app):
    if os.getenv("APM_SERVER_URL"):
        apm.init_app(app)

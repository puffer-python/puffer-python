FROM python:3.7

ADD requirements.txt /app/

RUN pip install -r requirements.txt

ADD . /app


CMD ["gunicorn", "main:app", "-k", "gevent", "--bind=0.0.0.0:8000", "--workers=2"]

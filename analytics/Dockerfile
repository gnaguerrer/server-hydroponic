FROM python:3.9.16

WORKDIR /app

RUN apt-get update
#RUN pip install aiohttp==3.8.3
RUN pip install influxdb-client==1.36
RUN pip install pika==1.3.1
RUN pip install -U scikit-learn
RUN pip install pandas
RUN pip install numpy
RUN pip install twilio

COPY analytics/main.py /app/main.py
COPY analytics/const.py /app/const.py
COPY analytics/utils.py /app/utils.py
COPY analytics/alert_sms.py /app/alert_sms.py

CMD [ "python", "/app/main.py" ]
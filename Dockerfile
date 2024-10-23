FROM python:3.11-slim
RUN apt-get update && apt-get -y install cron

COPY ./requirements.txt /app/requirements.txt
COPY ./cfdns.py /app/cfdns.py
COPY ./main.py /app/main.py
COPY ./clogger.py /app/clogger.py
COPY ./crontab /etc/cron.d/my-crontab

ARG CF_API_TOKEN
ARG CF_API_KEY
ARG CF_ZONE_ID
ARG CF_EMAIL
ARG RECORD_NAME
ARG RECORD_TYPE
ARG RECORD_PROXIED
ARG LOG_LEVEL


RUN echo "CF_API_TOKEN=$CF_API_TOKEN" >> /etc/environment 
RUN echo "CF_API_KEY=$CF_API_KEY" >> /etc/environment
RUN echo "CF_ZONE_ID=$CF_ZONE_ID" >> /etc/environment
RUN echo "CF_EMAIL=$CF_EMAIL" >> /etc/environment
RUN echo "RECORD_NAME=$RECORD_NAME" >> /etc/environment
RUN echo "RECORD_TYPE=$RECORD_TYPE" >> /etc/environment
RUN echo "RECORD_PROXIED=$RECORD_PROXIED" >> /etc/environment
RUN echo "LOG_LEVEL=$LOG_LEVEL" >> /etc/environment

RUN chmod 0644 /etc/cron.d/my-crontab
RUN touch /var/log/cron.log
RUN pip3 install -r /app/requirements.txt
RUN crontab /etc/cron.d/my-crontab
RUN echo "starting CFDNS" >> /var/log/cron.log
RUN echo "LOG LEVEL = $LOG_LEVEL" >> /var/log/cron.log
RUN echo "SUBDOMAIN = $RECORD_NAME" >> /var/log/cron.log
CMD cron && tail -f /var/log/cron.log

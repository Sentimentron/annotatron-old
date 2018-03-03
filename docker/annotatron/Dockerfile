FROM python:3.6.4-jessie
COPY files/requirements.txt /root/requirements.txt
RUN pip3 install -r /root/requirements.txt
RUN pip3 install gunicorn

WORKDIR /annotatron

CMD /entrypoint.sh


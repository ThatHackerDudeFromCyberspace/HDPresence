FROM alpine:latest

RUN mkdir /opt/hdpresence/
COPY ./main.py /opt/hdpresence/main.py
COPY ./requirements.txt /opt/hdpresence/requirements.txt
WORKDIR /opt/hdpresence
RUN apk update
RUN apk add python3 py3-pip
RUN pip install -r ./requirements.txt --break-system-packages --root-user-action=ignore
EXPOSE 8000
CMD python main.py
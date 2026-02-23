FROM alpine:latest

RUN mkdir /opt/hd_presence/
COPY ./main.py /opt/hd_presence/main.py
COPY ./requirements.txt /opt/hd_presence/requirements.txt
WORKDIR /opt/hd_presence
RUN apk update
RUN apk add python3 py3-pip
RUN pip install -r ./requirements.txt --break-system-packages --root-user-action=ignore
EXPOSE 8000
CMD python main.py
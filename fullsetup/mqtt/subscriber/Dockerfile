FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install nano python-pip -y
RUN pip install paho-mqtt pymongo
RUN mkdir /home/files

COPY subscriber.py /home/subscriber.py
#COPY defines.py /home/defines.py
COPY util.py /home/util.py


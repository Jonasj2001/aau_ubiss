FROM ubuntu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install nano python3-pip -y
RUN pip install paho-mqtt pymongo --break-system-packages
RUN mkdir /home/files

COPY subscriber.py /home/subscriber.py


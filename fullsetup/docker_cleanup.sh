#!/bin/bash
sudo docker container stop ubiss_mongo ubiss_subscriber ubiss_mongo_express ubiss_mosquitto ubiss_fileserver
sudo docker container rm ubiss_mongo ubiss_subscriber ubiss_mongo_express ubiss_mosquitto ubiss_fileserver
sudo rm -rf ./containers/mongo ./containers/mosquitto/data ./containers/mosquitto/log ./containers/mqtt
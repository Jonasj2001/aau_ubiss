First step is to go into the subscriber folder and run "./docker_build.sh". It will build the subscriber image.


Afterwards running "docker-compose up -d" will run the docker contianers in the background.

If the images do not autodownload you may have to run the following to download them

docker pull mongo
docker pull mongo-express
docker pull halverneus/static-file-server


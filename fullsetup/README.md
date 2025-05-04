# Setting up backend for AAU Ubiss

Make sure you have docker installed  

```bash
sudo apt update
sudo apt install docker-compose
```

Startup the containers by running  

```bash
sudo docker-compose up -d
```

## Issues

If the images do not autodownload you may have to run the following to download them  

```bash
docker pull mongo
docker pull mongo-express
docker pull halverneus/static-file-server
```

## Uninstall

To remove the docker instances and any generated data, make sure you are in the folder `fullsetup`  

Now you can run

```bash
sudo ./docker_cleanup.sh
```

This stops and removes the generated docker containers, as well as any generated files.

## Utility scripts

- `mongo_delete_ubiss.py` is used to delete the database of the default user `ubiss`
- `mongo_show_collections.py` is used to show all the user databases/collections created.
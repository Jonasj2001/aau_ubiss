export name="subscriber"
cp ../subscriber.py subscriber.py
cp ../util.py util.py
docker build --network=host -t $name .


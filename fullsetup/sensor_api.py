from datetime import datetime
import random
permitted_sensors=['light',"temp"]

light_test = 0
temp_test=0

def access_light_number():
    return light_test

def modify_light_number():
    global light_test
    light_test=light_test+1


def access_temp_number():
    return temp_test

def modify_temp_number():
    global temp_test
    temp_test=temp_test+1


def get_light_sample():
    #sample = access_light_number()
    #modify_light_number()
    sample = random.randrange(10, 100, 5)
    now=datetime.now()
    sample_ts=now.strftime("%d/%H:%M:%S")
    return sample, str(sample_ts)


def get_temperature_sample():
    sample =  random.randrange(-5, 30, 1)
    #modify_temp_number()
    now=datetime.now()
    sample_ts=now.strftime("%d/%H:%M:%S")
    return sample, sample_ts

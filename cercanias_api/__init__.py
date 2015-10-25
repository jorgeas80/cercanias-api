# -*- coding: utf-8 -*-
from rest_framework.exceptions import APIException
import os
import pymongo
from datetime import datetime
from pytz import timezone
import pytz

class RenfeServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Renfe service temporarily unavailable, try again later.'

class RenfeServiceChanged(APIException):
    status_code = 504
    default_detail = 'Renfe service taking too long to answer, try again later.'


def get_cities_cursor(q=None):
    # TODO: We should use a connection pool or something like that
    mongo_db_name = os.environ.get('MONGO_DBNAME')
    mongo_url = os.environ.get('MONGO_DBURI')
    mongo_collection = os.environ.get('MONGO_COLLECTION')

    # Connect with mongo
    mongo_client = pymongo.MongoClient(mongo_url)
    mongo_db = mongo_client[mongo_db_name]
    cities = mongo_db[mongo_collection]

    if q:
        try:
            return cities.find(filter=q,
                projection={'nucleo_id': True, 'nucleo_name': True,
                'nucleo_stations': True, '_id': False})
        except TypeError, e:
            # TODO: Do something with this error
            return None
    else:
        return cities.find(projection={'nucleo_id': True, 'nucleo_name': True,
        'nucleo_stations': True, '_id': False})

def time_to_hour(hour_string):
    """
        Calculates difference between now and the hour passed as argument
    """
    madrid_tz = timezone('Europe/Madrid')

    today_str = datetime.now().date().strftime("%Y-%m-%d") + ' ' + hour_string
    formatted_date = datetime.strptime(today_str, "%Y-%m-%d %H.%M")

    now = madrid_tz.localize(datetime.now())
    d = madrid_tz.localize(formatted_date)

    diff = d - now

    seconds = diff.total_seconds()
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return (hours, minutes)

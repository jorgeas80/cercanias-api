# -*- coding: utf-8 -*-
from django.contrib.auth.models import User


from cercanias_api.serializers import UserSerializer
from django.http import Http404, HttpResponseServerError, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import *
from rest_framework import status
import pymongo
from bson.json_util import dumps, loads
import os
from bs4 import BeautifulSoup as bs
from datetime import datetime
from . import RenfeServiceUnavailable, RenfeServiceChanged
import requests


class CityList(APIView):
    """
    List all cities with cercanias stations in Spain
    """
    def get(self, request, format=None):

        # TODO: We should use a connection pool or something like that
        mongo_db_name = os.environ.get('MONGO_DBNAME')
        mongo_url = os.environ.get('MONGO_DBURI')
        mongo_collection = os.environ.get('MONGO_COLLECTION')

        # Connect with mongo
        mongo_client = pymongo.MongoClient(mongo_url)
        mongo_db = mongo_client[mongo_db_name]
        cities = mongo_db[mongo_collection]

        # Get all cities as json array
        cursor = cities.find(projection={'nucleo_id': True, 'nucleo_name': True, 'nucleo_stations': True, '_id': False}).sort("nucleo_name", 1)

        # Get JSON string from cursor, containing all the elements
        dump_data = dumps(cursor)

        # Build JSON object and return it
        data = loads(dump_data)

        return Response(data, status=status.HTTP_200_OK)

class CityDetail(APIView):
    """
        Retrieve a city instance
    """
    def get(self, request, pk, format=None):
        # TODO: We should use a connection pool or something like that
        mongo_db_name = os.environ.get('MONGO_DBNAME')
        mongo_url = os.environ.get('MONGO_DBURI')
        mongo_collection = os.environ.get('MONGO_COLLECTION')

        # Connect with mongo
        mongo_client = pymongo.MongoClient(mongo_url)
        mongo_db = mongo_client[mongo_db_name]
        cities = mongo_db[mongo_collection]

        city_cursor = cities.find_one({'nucleo_id': pk},
            projection={'nucleo_id': True, 'nucleo_name': True,
            'nucleo_stations': True, '_id': False})

        if not city_cursor:
            raise Http404

        # Get JSON string from cursor, containing the city data
        dump_data = dumps(city_cursor)

        # Build JSON object and return it
        data = loads(dump_data)

        return Response(data, status=status.HTTP_200_OK)

class Schedule(APIView):
    """
        Retrieve the time table for a trip between two cities
    """
    def get(self, request, nucleo, orig, dst, format=None):
        # Today
        today_nospaces = datetime.now().date().strftime("%Y%m%d")

        # Send Renfe form
        r = None
        form_data = {
            "TXTInfo": "",
            "cp": "NO",
            "d": dst,
            "df": today_nospaces,
            "hd": "26",
            "ho": "00",
            "i": "s",
            "nucleo": nucleo,
            "o": orig
        }

        try:
            r = requests.post("http://horarios.renfe.com/cer/hjcer310.jsp",
                data=form_data)
        except requests.exceptions.Timeout:
            # TODO: Maybe set up for a retry, or continue in a retry loop
            raise RenfeServiceUnavailable()
        except requests.exceptions.TooManyRedirects:
            raise RenfeServiceChanged()
        except requests.exceptions.RequestException as e:
            return HttpResponseServerError(
                "Internal server error, please try again later.")

        if r:
            s = bs(r.content)

            return HttpResponse(s)

        else:
            return HttpResponseServerError(
                "Internal server error, please try again later.")



class UserList(APIView):
    """
    List all users, or create a new user.
    """
    def get(self, request, format=None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetail(APIView):
    """
    Retrieve, update or delete a user instance.
    """
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        user = UserSerializer(user)
        return Response(user.data)

    def put(self, request, pk, format=None):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

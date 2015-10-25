# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

from cercanias_api.serializers import UserSerializer
from django.http import Http404, HttpResponseServerError, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import *
from rest_framework import status
from bson.json_util import dumps, loads
from bs4 import BeautifulSoup as bs
from datetime import datetime
from . import *
import requests
import re


class CityList(APIView):
    """
    List all cities with cercanias stations in Spain
    """
    def get(self, request, format=None):
        # Get all cities. No filter
        cursor = get_cities_cursor()

        if cursor:
            # Get JSON string from cursor, containing all the elements
            dump_data = dumps(cursor)

            # Build JSON object and return it
            data = loads(dump_data)

            return Response(data, status=status.HTTP_200_OK)

        else:
            return HttpResponseServerError(
                "Internal server error, please try again later.")

class CityDetail(APIView):
    """
        Retrieve a city instance
    """
    def get(self, request, pk, format=None):
        # Get one specifc city
        cursor = get_cities_cursor(q={'nucleo_id': pk})

        if cursor and cursor.count() > 0:
            city_cursor = cursor.next()

            # Get JSON string from cursor, containing the city data
            dump_data = dumps(city_cursor)

            # Build JSON object and return it
            data = loads(dump_data)

            return Response(data, status=status.HTTP_200_OK)

        else:
            raise Http404("City not found")



class Schedule(APIView):
    """
        Retrieve the time table for a trip between two cities
    """
    def get(self, request, nucleo, orig, dst, format=None):
        # Today
        today_date = datetime.now().strftime("%Y%m%d")
        today_hour = datetime.now().strftime("%H")

        # Send Renfe form
        r = None
        form_data = {
            "TXTInfo": "",
            "cp": "NO",
            "d": dst,
            "df": today_date,
            "hd": "26",
            "ho": today_hour,
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
            try:
                s = bs(r.content, "html.parser")
                table = s.find('table')
                rows = table.find_all('tr')

                first_row_cols = rows[1].find_all("td")

                # no transfer. Init time is the column 1 of the row 2
                if len(first_row_cols) == 4:
                    hour = rows[2].find_all("td")[1].text.strip()

                # 1 transfer. Init time is the column 1 of the row 4
                elif len(first_row_cols) == 6:
                    hour = rows[4].find_all("td")[1].text.strip()

                # 2 transfers. Init time is the column 1 of the row 4
                elif len(first_row_cols) == 7:
                    hour = rows[4].find_all("td")[1].text.strip()
                else:
                    hour = u"00:00"

                data = str(time_to_hour(hour))

                """
                data = []
                for row in rows:
                    cols = row.find_all('td')
                    cols = [re.sub('[\r\n]', '', ele.text.strip()) for ele in cols]

                    for col in cols:
                        col = re.sub('[^\W\d_]', '', col)
                        if col:
                            data.append({"col": col})
                """


                return Response(data, status=status.HTTP_200_OK)
            except Exception, e:
                return HttpResponseServerError(
                    "Internal server error, please try again later.")
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

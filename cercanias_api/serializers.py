# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
import pymongo

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')

# -*- coding: utf-8 -*-
from rest_framework.exceptions import APIException

class RenfeServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Renfe service temporarily unavailable, try again later.'

class RenfeServiceChanged(APIException):
    status_code = 504
    default_detail = 'Renfe service taking too long to answer, try again later.'

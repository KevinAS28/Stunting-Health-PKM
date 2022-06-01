# from django.conf import settings
from django.db import models
from datetime import date, datetime, timedelta
from token_authentication.auth_util import TOKEN_AUTHENTICATION_CONFIG as CONFIG
# Create your models here.

# CONFIG = settings.TOKEN_AUTHENTICATION_CONFIG

MAX_TOKEN_LENGTH = CONFIG['MAX_TOKEN_LENGTH']

def expire(seconds=-1, minutes=-1, days=-1):
    duration = (seconds, minutes, days)
    if sum(duration)==(-1*len(duration)):
        seconds = CONFIG['EXPIRE_SECONDS']
        minutes = CONFIG['EXPIRE_MINUTES']
        days = CONFIG['EXPIRE_DAYS']
    return datetime.now() + timedelta(seconds=seconds, minutes=minutes, days=days)
    

class UserRole(models.Model):
    role_name = models.CharField(max_length=50)

class UserAuthentication(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    role = models.ForeignKey(UserRole, on_delete=models.DO_NOTHING)
    token = models.CharField(max_length=MAX_TOKEN_LENGTH, null=True)
    token_expired = models.DateTimeField(default=expire, null=True)


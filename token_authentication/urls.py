app_name = 'token_authentication'

from atexit import register
from django.urls import path
from .views import *


urlpatterns = [
    path('get_token', get_token),
    path('refresh_token', refresh_token),
    path('delete_token', delete_token),
    path('register_user', register_user),
    path('create_role', create_role),
    
]
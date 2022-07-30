from datetime import datetime
import json

from django.http import JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

import token_authentication.models as models
import token_authentication.auth_util as auth_util

def login(*args, **kwargs):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            request = args[0]
            if request.method == 'GET':
                username = request.GET['username']
                password = request.GET['password']
            elif request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                data = json.loads(request.body)
                username = data['username']
                password = data['password']   
            else:
                response = {'success': False, 'message': 'Invalid method'}
                return JsonResponse(response)

            user = models.UserAuthentication.objects.filter(username=username, password=password)
            if user.exists():
                result = fun(*args, **kwargs)
                auth_success = {'success': True, 'message': 'OK', 'user': model_to_dict(user[0])}
                response = {**({f'data{i}': json.loads(key) for i, key in enumerate(result)}), **auth_success}
                # print(
                # response = JsonResponse(response)
                # # print(
                return response

            else:
                # print(
                response = {'success': False, 'message': 'Invalid Authentication'}
                # print(
                return JsonResponse(response)
        return wrapper
    return decorator


def token_get(username, password):
    try:
        user = models.UserAuthentication.objects.get(username=username, password=password)
        # role = models.UserRole.objects.get(id=user.role)
        # print(
        token = (auth_util.token_hash((username+password+str(datetime.now())).encode('utf-8')))
        user.token = token
        user.token_expired = models.get_token_expire()
        user.save()
        return token
    except ObjectDoesNotExist:
        return False

def token_refresh(token):
    try:
        user = models.UserAuthentication.objects.get(token=token)
        username = user.username
        password = user.password
        token = (auth_util.token_hash((username+password+str(datetime.now())).encode('utf-8')))
        user.token = token
        user.token_expired = models.get_token_expire()
        user.save()        
        return token
    except ObjectDoesNotExist:
        return False

def token_delete(token):
        try:
            user = models.UserAuthentication.objects.get(token=token)
            username = user.username
            password = user.password
            token = (auth_util.token_hash((username+password+str(datetime.now())).encode('utf-8'))).hexdigest()
            user.token = token
            user.token_expired = datetime.now()
            user.save()        
            return user
        except ObjectDoesNotExist:
            return False

def token_auth_core(token, roles):
    try:
        if len(roles)==0:
            return None
        elif (len(roles)>0) and (roles[0]=='*'):
            user = models.UserAuthentication.objects.get(token=token)
        else:
            role_objects = [role.id for role in models.UserRole.objects.filter(role_name__in=roles)]
            user = models.UserAuthentication.objects.get(token=token, role__in=role_objects)
        if user.token_expired>=datetime.now(user.token_expired.tzinfo):
            return user
        else:
            return None
    except ObjectDoesNotExist:
        return None

def token_auth(roles=['*'], get_user=False, response_info=False):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            request: WSGIRequest = args[0]

            try:
                token = request.headers['token']
            except:
                response = {'success': False, 'message': 'Invalid Authentication'}
                return JsonResponse(response, status=401)

            if token is None:
                response = {'success': False, 'message': 'Invalid method'}
                return JsonResponse(response, status=401)

            user = token_auth_core(token, roles)
            if user:
                if get_user:
                    result = fun(user, *args, **kwargs)
                else:
                    result = fun(*args, **kwargs)
                
                if response_info:
                    auth_success = {'success': True, 'message': 'OK'}
                    response = {'data': result, 'auth': auth_success}
                    response = JsonResponse(response)
                else:
                    response = result
                return response

            else:
                response = {'success': False, 'message': 'Invalid Authentication'}
                return JsonResponse(response, status=401)
        return wrapper
    return decorator

def is_user_role(user: models.UserAuthentication, role_names: list):
    roles = models.UserRole.objects.filter(role_name__in=role_names)
    if user.role in roles:
        return True
    return False
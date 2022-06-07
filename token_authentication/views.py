import json, traceback

from django.forms import model_to_dict
from django.http import JsonResponse
from django.core.handlers.wsgi import WSGIRequest

import token_authentication.models as models
import token_authentication.auth_core as auth_core


def get_token(request):
    data = json.loads(request.body)
    username = data['username']
    password = data['password']
    token = auth_core.token_get(username, password)
    if token:
        response_data = {
            'status': 0,
            'token': token
        }
    else:
        response_data = {
            'error_brief': '',
            'error_long': '',
            'status': 1,
            'status_str': 'Failed Get Token'
        }

    return JsonResponse(response_data)

def refresh_token(request: WSGIRequest):
    old_token = request.headers['token']
    new_token = auth_core.token_refresh(old_token)
    if new_token:
        return JsonResponse({'token': new_token})
    return JsonResponse({'token': ''})

def delete_token(request):
    token = request.headers['token']
    result = auth_core.token_delete(token)
    if result:
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def register_user(request):
    try:
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        if 'role_id' in data:
            role = models.UserRole.objects.get(id=data['role_id']) 
        elif 'role_name' in data:
            role = models.UserRole.objects.get(role_name=data['role_name']) 
        else:
            return JsonResponse({'success': False, 'error': 'Please provide role_name or role_name'})

        userauth = models.UserAuthentication(
            username=username,
            password=password,
            role=role
        )
        userauth.save()
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False, 'error': traceback.format_exc()})

def create_role(request):
    data = json.loads(request.body)
    role_name = data['role_name']
    role = models.UserRole(role_name=role_name)
    role.save()
    return JsonResponse({'success': True, 'role': model_to_dict(role)})

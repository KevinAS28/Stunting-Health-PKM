import json, datetime, requests

from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest
from stunting_backend import secret_settings 

from token_authentication import models as ta_models
from token_authentication.auth_core import token_auth
from apiv1 import models, utils

# Create your views here.

@token_auth(roles=['user'], get_user=True)
def test(user: ta_models.UserAuthentication, request: WSGIRequest):
    return JsonResponse({'User': model_to_dict(user)})

@token_auth(roles=['user'], get_user=True)
def user_profile(user: ta_models.UserAuthentication, request: WSGIRequest):
    if request.method=='GET':
        profile = models.UserProfile.objects.get(authentication=user)
        get_necessary_profile = lambda profile: {'name': profile.name, 'b64_profile_img': utils.read_base64(profile.profile_file)}
        return JsonResponse({'profile': get_necessary_profile(profile), 'user': model_to_dict(user)})
    elif request.method=='POST':
        data = json.loads(request.body)
        profile_file = f'{utils.valid_filename(data["name"])}.jpg'
        profile = models.UserProfile(authentication=user, name=data['name'], profile_file=profile_file)
        utils.write_base64(profile_file, data['b64_profile_img'])
        profile.save()
        return JsonResponse({'profile': model_to_dict(profile), 'user': model_to_dict(user)})
    return HttpResponseNotFound()

@token_auth(roles=['user'], get_user=True)
def stunt_reminder(user: ta_models.UserAuthentication, request: WSGIRequest):
    profile = models.UserProfile.objects.get(authentication=user)
    if request.method=='POST':
        data = json.loads(request.body)
        stunt_reminder = models.StuntReminder(
            user=profile,
            clock=datetime.datetime.strptime(data['hour_minute'], '%H:%M').time(),
            repeat_each=json.dumps(data['repeat_each']),
            on=data['on']
        )
        stunt_reminder.save()
        return JsonResponse({'reminder_saved': model_to_dict(stunt_reminder)})
    elif request.method=='GET':
        return JsonResponse({'all_user_reminders': [model_to_dict(i) for i in models.StuntReminder.objects.filter(user=profile)]})
    elif request.method=='DELETE':
        data = json.loads(request.body)
        deleted_reminders = [i.delete() for i in models.StuntReminder.objects.filter(id__in=data['to_delete_ids'])]
        return JsonResponse({'deleted': deleted_reminders})
            
    return HttpResponseNotFound()

@token_auth(roles=['user'], get_user=True)
def stunting_trace(user: ta_models.UserAuthentication, request: WSGIRequest):
    profile = models.UserProfile.objects.get(authentication=user)
    if request.method=='GET':
        return JsonResponse({'all_traces': [model_to_dict(i) for i in models.StuntingTrace.objects.filter(user=profile)]})
    elif request.method=='POST':
        data = json.loads(request.body)
        saved_traces = []
        for trace in data['all_traces']:
            trace_object = models.StuntingTrace(user=profile, week=trace['week'], height=trace['height'], weight=trace['weight'])
            trace_object.save()
            saved_traces.append(model_to_dict(trace_object))
        return JsonResponse({'saved_traces': saved_traces})
    elif request.method=='PATCH':
        data = json.loads(request.body)
        saved_traces = []
        for trace in data['all_traces']:
            trace_object = models.StuntingTrace.objects.filter(user=profile, week=trace['week'])
            trace_object.height=trace['height']
            trace_object.weight=trace['weight']
            trace_object.save()
            saved_traces.append(model_to_dict(trace_object))
    return HttpResponseNotFound()

@token_auth(roles=['user'])
def stunt_maps(request: WSGIRequest):
    data = json.loads(request.body)
    NEARBY_PLACE_API = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    nearby_place_parameters = {
        'key': secret_settings.MAP_API_KEY,
        'location': data['location'], #format: lat,long
        'keyword': data['keyword'],
        'radius': data['radius'] if 'radius' in data else 50000,
        'types': '|'.join('doctor pharmacy hospital health'.split())
    }
    return JsonResponse({'places': json.loads(requests.get(NEARBY_PLACE_API, params=nearby_place_parameters).text)}, json_dumps_params={'indent':4, 'sort_keys': True})

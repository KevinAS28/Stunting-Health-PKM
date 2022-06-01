import json, datetime, requests, re, os

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
        get_necessary_profile = lambda profile: {'name': profile.name, 'b64_profile_img': utils.read_b64_file(os.path.join('img', profile.profile_file))}
        return JsonResponse({'profile': get_necessary_profile(profile), 'user': model_to_dict(user)})
    elif request.method=='POST':
        data = json.loads(request.body)
        profile_file = f'{utils.valid_filename(data["name"])}.jpg'
        profile = models.UserProfile(authentication=user, name=data['name'], profile_file=profile_file)
        utils.write_b64_file(os.path.join('img', profile_file), data['b64_profile_img'])
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
            trace_object = models.StuntingTrace.objects.get(user=profile, week=trace['week'])
            trace_object.height=trace['height']
            trace_object.weight=trace['weight']
            trace_object.save()
            saved_traces.append(model_to_dict(trace_object))
        return JsonResponse({'updated': saved_traces})
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

@token_auth(roles=['user'])
def article(request: WSGIRequest):
    data = json.loads(request.body)

    def _article(article: models.Article):
        article_file_content = utils.read_file(article.article_file).decode('utf-8')
        model_dict = model_to_dict(article)
        model_dict['article_file_content'] = article_file_content
        return model_dict

    if request.method=='GET':
        get_articles = data['get_articles']
        if get_articles=='all':
            return JsonResponse({'all_articles': [_article(i) for i in models.Article.objects.all()]})
        elif get_articles=='filter_articles':
            field_names_default = {
                'title': '.*',
                'article_types': '.*',
                'article_tags': '.*'
            }
            field_names_filter = dict()

            for field, default in field_names_default.items():
                if field in data:
                    field_names_filter[field+'__contains'] = data[field]
                else:
                    field_names_filter[field+'__regex'] = default

            return JsonResponse({'articles': [model_to_dict(i) for i in models.Article.objects.filter(**field_names_filter)]})
        



    elif request.method=='POST':
        title = data['title']
        pattern = re.compile(r'({([a-z|A-Z|0-9|_|-]+)})')
        tags_urls = dict()
        for i, m in enumerate(pattern.finditer(data['article_content'])):
            full_match, match = m.groups()
            match, m_type = match.split('_')
            extension = data['article_items'][match]['extension']
            file_name = utils.valid_filename(f'{title}_{match}_{i}.{extension}')
            file_path = f"{m_type}/{file_name}"
            print('write:', utils.write_b64_file(file_path, data['article_items'][match]['content']))
            url = f'http://{request.get_host()}/static/{file_path}'
            tags_urls[full_match] = url

        article_parsed = utils.multiple_replace(data['article_content'], tags_urls, regex=False)
        article_parsed_path = os.path.join('articles', utils.valid_filename(f'{title}_{data["date"]}.html', '_'))
        utils.write_file(article_parsed_path, article_parsed.encode('utf-8'))
        article = models.Article(
            article_file=article_parsed_path,
            date=datetime.datetime.strptime(data['date'], "%d/%m/%Y").date(),
            title=title,
            article_types=data['article_types'],
            article_tags=data['article_tags']
        )
        article.save()
        return JsonResponse({'status': 'OK', 'items': tags_urls, 'article_parsed': article_parsed, 'article_parsed_path': f'article_parsed_path', 'saved': model_to_dict(article)})
        
    elif request.method=='DELETE':
        to_delete = models.Article.objects.filter(id__in=data['to_delete_ids']) 
        deleteds = []
        for article in to_delete:
            article.delete()
            deleteds.append(model_to_dict(article))
        return JsonResponse({'deteleds': deleteds})
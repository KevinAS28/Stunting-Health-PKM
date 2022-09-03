import json, datetime, requests, re, os, base64
from pty import CHILD

from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Sum, Max

import apiv1.stuntech_core as stcore
from stunting_backend import secret_settings

from token_authentication import models as ta_models
from token_authentication.auth_core import token_auth, token_auth_core, is_user_role
from apiv1 import models, utils

from geopy import distance


# Create your views here.
@token_auth(roles=['user'], get_user=True)
def test(user: ta_models.UserAuthentication, request: WSGIRequest):
    return JsonResponse({'User': model_to_dict(user)})

@token_auth(roles=['admin'])
def profile_admin(request: WSGIRequest):
    data = json.loads(request.body)
    if request.method=='GET':
        if data['get_type']=='all':
            return JsonResponse({'all_users': [model_to_dict(i) for i in models.UserProfile.objects.all()]})    
        elif data['get_type']=='filter':
            return JsonResponse({'all_users': [model_to_dict(i) for i in models.UserProfile.objects.filter(name__contains=data['name'])]})    
        return HttpResponseNotFound()

def user(request: WSGIRequest):
    if request.method=='GET':
        user: ta_models.UserAuthentication = token_auth_core(request.headers['token'], ['*'])
        if not (user is None):
            profile = models.UserProfile.objects.get(authentication=user)
            get_necessary_profile = lambda profile: {'name': profile.name, 'b64_profile_img': utils.read_b64_file(os.path.join('img', profile.profile_file))}
            return JsonResponse({'success': True, 'profile': get_necessary_profile(profile), 'user': model_to_dict(user)})
        return JsonResponse({'success': False, 'error': 'Invalid authentication'})
    elif request.method=='POST':
        data = json.loads(request.body)
        username = data['username']
        password = data['password']
        if 'role_id' in data:
            role = ta_models.UserRole.objects.get(id=data['role_id']) 
        elif 'role_name' in data:
            role = ta_models.UserRole.objects.get(role_name=data['role_name']) 
        else:
            return JsonResponse({'success': False, 'error': 'Please provide role_name or role_name'})

        userauth = ta_models.UserAuthentication(
            username=username,
            password=password,
            role=role
        )
        userauth.save()

        profile_file = f'{utils.valid_filename(data["name"])}.jpg'
        profile = models.UserProfile(authentication=userauth, name=data['name'], email=data['email'], profile_file=profile_file)
        utils.write_b64_file(os.path.join('img', profile_file), data['b64_profile_img'])

        profile.save()
        return JsonResponse({'profile': model_to_dict(profile)})

    elif request.method=='PATCH':
        data = json.loads(request.body)
        user: ta_models.UserAuthentication = token_auth_core(request.headers['token'], ['*'])
        profile = models.UserProfile.objects.get(authentication=user)
        role = None
        if 'role_id' in data:
            role = ta_models.UserRole.objects.get(id=data['role_id']) 
        elif 'role_name' in data:
            role = ta_models.UserRole.objects.get(role_name=data['role_name']) 
        else:
            return JsonResponse({'success': False, 'error': 'Please provide role_name or role_name'})
        user.username = data['username']
        user.password = data['password']
        user.role = role
        
        profile.name = data['name']
        profile.email = data['email']
        profile_file = f'{utils.valid_filename(data["name"])}.jpg'
        utils.write_b64_file(os.path.join('img', profile_file), data['b64_profile_img'])
        user.save()
        profile.save()

        return JsonResponse({'profile': model_to_dict(profile), 'user': model_to_dict(user)})
    elif request.method=='DELETE':
        data = json.loads(request.body)
        user: ta_models.UserAuthentication = token_auth_core(request.headers['token'], ['*'])
        profile: models.UserProfile = models.UserProfile.objects.get(authentication=user)
        user.delete()
        profile.delete()

        return JsonResponse({'profile': model_to_dict(profile), 'user': model_to_dict(user)})
    else:
        return HttpResponseNotFound()


@token_auth(roles=['user', 'admin'], get_user=True)
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
        def del_get(i): i.delete(); return i
        deleted_reminders = [del_get(i) for i in models.StuntReminder.objects.filter(id__in=data['to_delete_ids'])]
        return JsonResponse({'deleted': deleted_reminders})  
    return HttpResponseNotFound()

@token_auth(roles=['user', 'admin'], get_user=True)
def stunting_trace(user: ta_models.UserAuthentication, request: WSGIRequest):
    if request.method=='GET':
        profile = models.UserProfile.objects.get(authentication=user)
        child = models.Children.objects.get(id=int(request.GET['child_id']))
        return JsonResponse({'all_traces': [model_to_dict(i) for i in models.StuntingTrace.objects.filter(user=profile, children=child)]})
    elif request.method=='POST':
        data = json.loads(request.body)
        saved_traces = []
        for trace in data['all_traces']:
            profile = models.UserProfile.objects.get(authentication=user)
        
            children = models.Children.objects.get(id=data['child_id'])
            age_month = round(trace['week']/4)
            growth_level, z_score = stcore.stunting_classification(children.gender, age_month, float(trace['height']))

            trace_object = models.StuntingTrace(
                user=profile,
                week=trace['week'],
                height=trace['height'],
                weight=trace['weight'],
                age_day=trace['age_day'],
                exclusive_asi=trace['exclusive_asi'],
                disease_history=trace['disease_history'],
                immunization_history=trace['immunization_history'],
                children=children,
                z_score=z_score,
                growth_level=growth_level
                )
            trace_object.save()
            saved_traces.append(model_to_dict(trace_object))
        return JsonResponse({'saved_traces': saved_traces})
        
    elif request.method=='PATCH':
        profile = models.UserProfile.objects.get(authentication=user)
        data = json.loads(request.body)
        saved_traces = []
        for trace in data['all_traces']:
            children = models.Children.objects.get(id=data['child_id'])
            age_month = round(trace['week']/4)
            growth_level, z_score = stcore.stunting_classification(children.gender, age_month, float(trace['height']))

            trace_object = models.StuntingTrace.objects.get(user=profile, week=trace['week'], children=models.Children.objects.get(id=data['child_id']))
            trace_object.height=trace['height']
            trace_object.weight=trace['weight']
            trace_object.age_day=trace['age_day']
            trace_object.exclusive_asi=trace['exclusive_asi']
            trace_object.disease_history=trace['disease_history']
            trace_object.immunization_history=trace['immunization_history']
            trace_object.children=children
            trace_object.growth_level=growth_level
            trace_object.z_score=z_score
            trace_object.save()
            saved_traces.append(model_to_dict(trace_object))
        return JsonResponse({'updated': saved_traces})
    elif request.method=='DELETE':
        data = json.loads(request.body)
        deleted_traces = []
        for trace_id in data['to_delete_ids']:
            trace = models.StuntingTrace.objects.filter(id=trace_id)
            if len(trace)==0:
                continue
            trace = trace[0]
            trace.delete()
            deleted_traces.append(model_to_dict(trace))
        return JsonResponse({'deleted': deleted_traces})
    return HttpResponseNotFound()

@token_auth(roles=['admin'])
def stunt_maps_admin(request: WSGIRequest):
    if request.method=='GET':
        data = json.loads(request.GET['json_body'])
        get_type = data['get_type']
        if get_type=='unregistered':
            SEARCH_PLACE_API = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
            PHOTO_PLACE_API = 'https://maps.googleapis.com/maps/api/place/photo'
            search_place_parameters = {
                'key': secret_settings.MAP_API_KEY,
                'query': data['place_query']
            }
            request_response = requests.get(SEARCH_PLACE_API, params=search_place_parameters).text
            print(request_response)

            # Filter for already registered places
            all_places = json.loads(request_response)['results']
            all_place_ids = [i['place_id'] for i in all_places]
            existing_place_ids = [i.gmap_place_id for i in models.StuntPlace.objects.filter(gmap_place_id__in=all_place_ids)]
            all_places = [i for i in all_places if not (i['place_id'] in existing_place_ids)]

            for i, place in enumerate(all_places):
                #process the photo
                if 'photos' in place:
                    if len(place['photos'])>0:
                        photo_params = {
                            'key': secret_settings.MAP_API_KEY,
                            'photo_reference': place['photos'][0]['photo_reference'],
                            'maxheight': 1000,
                            'maxwidth': 1000                            
                        }
                        photo_resp = requests.get(PHOTO_PLACE_API, params=photo_params)
                        file_path = os.path.join('img', utils.valid_filename(f'{place["name"]}_{place["place_id"]}_first.png'))
                        utils.write_b64_file(file_path, base64.b64encode(photo_resp.content))
                        place['static_img'] = f'http://{request.get_host()}/static/{file_path}'
                    
                all_places[i] = place

            return JsonResponse({'all_places': all_places})
        elif get_type=='registered_all':
            return JsonResponse({'registered_places': [model_to_dict(i) for i in models.StuntPlace.objects.all()]})
        elif get_type=='registered_filter_names':
            return JsonResponse({'registered_places': [model_to_dict(i) for i in models.StuntPlace.objects.filter(place_name__contains=data['place_names'])]})
        else:
            return HttpResponseNotFound()

    elif request.method=='POST':
        data = json.loads(request.body)
        saved_places = []
        for place in data['all_places']:
            place_obj = models.StuntPlace(
                location_lat=place['location_lat'],
                location_lng=place['location_lng'],
                place_name=place['name'],
                gmap_place_id=place['gmap_place_id'],
                img_url=place['img_url'],   
                avg_rating=place['avg_rating']
            )
            place_obj.save()
            saved_places.append(place)
        return JsonResponse({'saved': saved_places})

    elif request.method=='DELETE':
        data = json.loads(request.body)
        if 'to_delete_ids' in data:
            deleted_places = []
            for place_id in data['to_delete_ids']:
                place = models.StuntPlace.objects.filter(id=place_id)
                if len(place)==0:
                    continue
                place = place[0]
                place.delete()
                deleted_places.append(model_to_dict(place))
            return JsonResponse({'deleted': deleted_places})
        else:
            deleted_places = []
            for place_id in data['gmap_place_ids']:
                place = models.StuntPlace.objects.filter(gmap_place_id=place_id)
                if len(place)==0:
                    continue
                place = place[0]
                place.delete()
                deleted_places.append(model_to_dict(place))
            return JsonResponse({'deleted': deleted_places})
    else:
        return HttpResponseNotFound()

@token_auth(roles=['user', 'admin'])
def stunt_maps(request: WSGIRequest):
    if request.method=='GET':
        # data = request.POST
        data = json.loads(request.GET['json_body'])
        get_type = data['get_type']
        # NEARBY_PLACE_API = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        # nearby_place_parameters = {
        #     'key': secret_settings.MAP_API_KEY,
        #     'location': data['location'], #format: lat,long
        #     'keyword': data['keyword'],
        #     'radius': data['radius'] if 'radius' in data else 5000,
        #     'types': '|'.join('doctor pharmacy hospital health'.split())
        # }
        # print('Requesting GMAP API...', end='')
        # all_places = json.loads(requests.get(NEARBY_PLACE_API, params=nearby_place_parameters).text)
        # print('Done')
        # print(all_places)
        # all_places = all_places['results']
        # all_place_ids = [i['place_id'] for i in all_places]
        # print(all_places)
        # print(len(all_place_ids), all_place_ids)
        # valid_places = [model_to_dict(i) for i in models.StuntPlace.objects.filter(gmap_place_id__in=all_place_ids)]
        # print(len(valid_places))
        def __merge_with_db(data:json):
            data['db_data'] = model_to_dict(models.StuntPlace.objects.filter(gmap_place_id=data['place_detail']['place_id'])[0])
            return data

        if get_type=='registered_filter_ids':
            return JsonResponse({'registered_places': [model_to_dict(i) for i in models.StuntPlace.objects.filter(id__in=data['place_ids'])]})

        elif get_type=='registered_filter_users':
            if data['location']=='' and data['keyword']=='':
                all_places = models.StuntPlace.objects.all()
                all_details = [__merge_with_db(utils.get_place_detail_photos(i.gmap_place_id, secret_settings.MAP_API_KEY, request.get_host(), 0)) for i in all_places]
                return JsonResponse({'places': all_details}, json_dumps_params={'indent':4, 'sort_keys': True})
            else:
                name_filter = models.StuntPlace.objects.filter(place_name__icontains=data['keyword'])
                dev_loc = tuple(map(float, data['location'].split(',')))
                radius = data['radius'] if 'radius' in data else 5000
                radius_filter = [__merge_with_db(utils.get_place_detail_photos(i.gmap_place_id, secret_settings.MAP_API_KEY, request.get_host())) for i in name_filter if abs(distance.distance(dev_loc, (i.location_lat, i.location_lng)).meters) <= radius]
                return JsonResponse({'places': radius_filter}, json_dumps_params={'indent':4, 'sort_keys': True})
                
    return HttpResponseNotFound()

def _article(article: models.Article):
    article_file_content = utils.read_file(article.article_file)
    model_dict = model_to_dict(article)
    if article_file_content==-1:
        model_dict['article_file_content'] = f'ERROR: FILE NOT FOUND {article.article_file}'    
    else:
        model_dict['article_file_content'] = article_file_content.decode('utf-8')
    return model_dict

@token_auth(roles=['user', 'admin'])
def article_users(request: WSGIRequest):
    data = json.loads(request.body)
    # data = request.POST
    get_articles = data['get_articles']
    if get_articles=='all':
        return JsonResponse({'all_articles': [_article(i) for i in models.Article.objects.all()]})
    elif get_articles=='filter_articles':
        field_names_default = {
            'title': '.*',
            'article_type': '.*',
            'article_sub_type': '.*',
            'article_tags': '.*'
        }
        field_names_filter = dict()
        for field, default in field_names_default.items():
            
            if field in data:
                # handle special field filters
                if field=='article_tags':
                    notor_pattern = r'([\|]*)'
                    
                    at_pattern = ''.join([f'({notor_pattern}{item}{notor_pattern})' for item in data[field]])

                    field_names_filter['article_tags__regex'] = at_pattern
                    
                else:
                    field_names_filter[field+'__contains'] = data[field]
            else:
                field_names_filter[field+'__regex'] = default
        return JsonResponse({'articles': [model_to_dict(i) for i in models.Article.objects.filter(**field_names_filter)]})    
    elif get_articles=='get_by_id':
        return JsonResponse({'article': model_to_dict(models.Article.objects.get(id=data['id']))})


@token_auth(roles=['admin'])
def article_admin(request: WSGIRequest):
    data = json.loads(request.body)
    if request.method=='POST':
        article_parsed_path, title, cover_path, tags_urls, article_parsed = utils.process_article(request)
        
        article = models.Article(
            article_file=article_parsed_path,
            date=datetime.datetime.strptime(data['date'], "%d/%m/%Y").date(),
            title=title,
            article_type=data['article_type'],
            article_sub_type=data['article_sub_type'],
            article_tags=data['article_tags'],
            article_cover_file=cover_path
        )
        article.save()
        return JsonResponse({'status': 'OK', 'items': tags_urls, 'article_parsed': article_parsed, 'article_parsed_path': f'article_parsed_path', 'saved': model_to_dict(article)})
    
    elif request.method=='PATCH':
        article_toedit = models.Article.objects.get(id=data['id'])
        article_parsed_path, title, cover_path, tags_urls, article_parsed = utils.process_article(request)
        article_toedit.article_file=article_parsed_path
        article_toedit.date=datetime.datetime.strptime(data['date'], "%d/%m/%Y").date()
        article_toedit.title=title
        article_toedit.article_type=data['article_type']
        article_toedit.article_sub_type=data['article_sub_type']
        article_toedit.article_tags=data['article_tags']
        article_toedit.article_cover_file=cover_path
        article_toedit.save()
        return JsonResponse({'status': 'OK', 'items': tags_urls, 'article_parsed': article_parsed, 'article_parsed_path': f'article_parsed_path', 'saved': model_to_dict(article_toedit)})

    elif request.method=='DELETE':
        to_delete = models.Article.objects.filter(id__in=data['to_delete_ids']) 
        deleteds = []
        for article in to_delete:
            article.delete()
            deleteds.append(model_to_dict(article))
        return JsonResponse({'deleteds': deleteds})
    
    else:
        return HttpResponseNotFound()

def article(request: WSGIRequest):
    if request.method=='POST':
        data = json.loads(request.body)
        if 'get_articles' in data:
            return article_users(request)
    
    return article_admin(request)

def update_avg_stuntplace_rating(stuntplace):
    queryset = models.StuntPlaceReview.objects.filter(stunt_place=stuntplace)
    rating_counts = queryset.count()
    if rating_counts==0:
        return 0, 0, 0

    rating_sum = queryset.aggregate(Sum('rating'))
    rating_avg = rating_sum['rating__sum']/rating_counts
    stuntplace.avg_rating = rating_avg
    stuntplace.save()
    return rating_avg, rating_sum, rating_counts

@token_auth(roles=['user', 'admin'], get_user=True)
def review(auth: ta_models.UserAuthentication, request: WSGIRequest):
    def _merge_with_user(review):
        user = models.UserProfile.objects.get(id=review['user'])
        review['user'] = user.name
        return review

    if request.method=='POST':
        if is_user_role(auth, ['user', 'admin']):
            data = json.loads(request.body)
            target_stuntplace = models.StuntPlace.objects.get(id=data['stuntmap_id'])
            user = models.UserProfile.objects.get(authentication=auth)
            stunt_review = models.StuntPlaceReview.objects.filter(stunt_place=target_stuntplace, user=user)
            # if len(stunt_review)>0:
            #     return JsonResponse({'success': False, 'error': f'Review has already defined'})
            review = models.StuntPlaceReview(stunt_place=target_stuntplace, user=user, rating=data['rating'], desc=data['desc'])
            review.save()
            rating_avg, rating_sum, ratings_count = update_avg_stuntplace_rating(target_stuntplace)
            return JsonResponse({'success': True, 'review': model_to_dict(review), 'new_avg_rating': rating_avg, 'rating_sum': rating_sum, 'rating_count': ratings_count})
        else:
            return JsonResponse({'success': False, 'error': 'Permission Denied'})
        
    elif request.method=='GET':
        data = json.loads(request.GET['json_body'])
        if (data['filter']['stuntplace_id']==None) and (data['filter']['user_email']==None):
            # Get all reviews
            return JsonResponse({'reviews': [model_to_dict(i) for i in models.StuntPlaceReview.objects.all()]})
        else:
            if data['filter']['user_email']==None:
                stuntplace = models.StuntPlace.objects.get(id=data['filter']['stuntplace_id'])
                queryset = models.StuntPlaceReview.objects.filter(stunt_place=stuntplace)
                filtered_reviews = [_merge_with_user(model_to_dict(i)) for i in queryset]  
                review_count = len(queryset)
                count_per_rating = dict()
                for rating in range(1, 6):
                    count_per_rating[rating] = len(queryset.filter(rating=rating))

            else:
                user = models.UserProfile.objects.get(email=data['filter']['user_email'])
                stuntplace = models.StuntPlace.objects.get(id=data['filter']['stuntplace_id'])
                queryset = models.StuntPlaceReview.objects.filter(stunt_place=stuntplace, user=user)
                filtered_reviews = [_merge_with_user(model_to_dict(i)) for i in queryset]
                review_count = len(queryset)
                count_per_rating = dict()
                for rating in range(1, 6):
                    count_per_rating[rating] = len(queryset.filter(rating=rating))                
            
            return JsonResponse({'reviews': filtered_reviews, 'review_count': review_count, 'count_per_rating': count_per_rating})
    
    elif request.method=='DELETE':
        data = json.loads(request.body)
        delete_type = data['delete_type']
        if delete_type=='email_place':
            if not is_user_role(auth, ['admin']):
                return JsonResponse({'succcess': False, 'error': 'Permission Denied'})
            data = json.loads(request.body)
            stunt_place = models.StuntPlace.objects.get(id=data['stuntmap_id'])
            user = models.UserProfile.objects.get(email=data['email'])
            review = models.StuntPlaceReview.objects.get(stunt_place=stunt_place, user=user)
            review.delete()
            avg_rating, rating_sum, ratings_count = update_avg_stuntplace_rating(stuntplace=stunt_place)
            return JsonResponse({'deleted_review': model_to_dict(review), 'new_avg_rating': avg_rating, 'rating_sum': rating_sum, 'rating_count': ratings_count})
        elif delete_type=='id':
            review = models.StuntPlaceReview.objects.get(id=data['stuntreview_id'])
            review.delete()
            return JsonResponse({'deleted_review': model_to_dict(review)})

    elif request.method=='PATCH':
        data = json.loads(request.body)
        stuntplace = models.StuntPlace.objects.get(id=2)
        rating_sum = models.StuntPlaceReview.objects.filter(stunt_place=stuntplace).aggregate(Sum('rating'))
        rating_counts = models.StuntPlaceReview.objects.all().count()
        rating_avg = rating_sum['rating__sum']/rating_counts
        stuntplace.avg_rating = rating_avg
        stuntplace.save()
        return JsonResponse({'stuntplace': model_to_dict(stuntplace), 'all_reviews': [model_to_dict(i) for i in models.StuntPlaceReview.objects.all()]})
    else:
        return HttpResponseNotFound()

# @token_auth(roles=['admin', 'user'])
# def fun_stunt_user(request: WSGIRequest):
#     if request

@token_auth(roles=['admin'], get_user=True)
def fun_stunt_admin(auth: ta_models.UserAuthentication, request: WSGIRequest):

    if request.method=='POST':
        data = json.loads(request.body)
        if not is_user_role(auth, ['admin']):
            return JsonResponse({'succcess': False, 'error': 'Permission Denied'})

        last_question_index = models.GeneralConfig.objects.get(key='last_question_index')
        title = utils.valid_filename(f'question_{last_question_index.value}')
        qa_parsed, qa_parsed_path, tags_urls = utils.process_content_items('fun_stunt_questions', title, data['question_content'], data['question_items'], request.get_host())
        last_question_index.value = str(int(last_question_index.value)+1)
        last_question_index.save()
        answer_file_path = os.path.join('fun_stunt_answers', title+'.json')
        utils.write_file(answer_file_path, json.dumps(data['answers_content']).encode('utf-8'))
        qa = models.FunStuntQA(question_file=qa_parsed_path, answers_file=answer_file_path, level=data['level'], correct_answer=data['correct_answer'])
        qa.save()
        return JsonResponse({'qa_parsed': qa_parsed, 'qa_model': model_to_dict(qa)})
        # elif data['submit_type']=='submit_answer':


    elif request.method=='DELETE':
        if not is_user_role(auth, ['admin']):
            return JsonResponse({'succcess': False, 'error': 'Permission Denied'})

        data = json.loads(request.body)
        to_delete_qa = models.FunStuntQA.objects.get(id=data['qa_id'])
        to_delete_qa.delete()
        utils.delete_file(to_delete_qa.question_file)
        utils.delete_file(to_delete_qa.answers_file)
        return JsonResponse({'qa_deleted': model_to_dict(to_delete_qa)})
    
    return HttpResponseNotFound()

@token_auth(roles=['admin', 'user'], get_user=True)
def fun_stunt_user(auth: ta_models.UserAuthentication, request: WSGIRequest):
    def _merge_qa_content(qa: dict):
        question_content = utils.read_file(qa['question_file']).decode('utf-8')
        answers_content = utils.read_file(qa['answers_file']).decode('utf-8')
        qa['question_content'] = question_content
        qa['answers_content'] = answers_content
        return qa
        
    user = models.UserProfile.objects.get(authentication=auth)

    if  request.method=='POST':
        data = json.loads(request.body)

        qa = models.FunStuntQA.objects.get(id=data['qa_id'])
        old_user_answer = models.FunStuntUserAnswer.objects.filter(user=user, question=qa)
        
        answer_is_correct = None
        if qa.correct_answer==data['submitted_answer']:
            answer_is_correct = True
        else:
            answer_is_correct = False

        user_answer_attributes = dict(user=user, question=qa, answer=data['submitted_answer'], answer_is_correct=answer_is_correct)
        if len(old_user_answer)==0:
            user_answer = models.FunStuntUserAnswer(**user_answer_attributes)
        else:
            user_answer = utils.auto_set_obj_attrs(old_user_answer[0], user_answer_attributes)
        user_answer.save()
        return JsonResponse({'answer': model_to_dict(user_answer)})

    elif request.method=='GET':
        data = json.loads(request.GET['json_body'])
        get_type = data['get_type']
        if get_type=='qas':
            if data['filter_type']=='all':
                qas = models.FunStuntQA.objects.all()
            elif data['filter_type']=='by_levels':
                qas = models.FunStuntQA.objects.filter(level__in=data['levels'])
            elif data['filter_type']=='id':
                qas = models.FunStuntQA.objects.filter(id=data['qa_ids'])
            return JsonResponse({'qas': [_merge_qa_content(model_to_dict(i)) for i in qas]})
        elif get_type=='user_answers':
            queryset = models.FunStuntUserAnswer.objects.filter(user=user)
            user_score_per_level = []
            max_level = models.FunStuntQA.objects.aggregate(Max('level'))['level__max']
            for level in range(1, max_level+1):
                questions_count_level = len(models.FunStuntQA.objects.filter(level=level))
                correct_answers_count = sum([1 for i in models.FunStuntUserAnswer.objects.filter(question__level=level, user=user) if i.answer_is_correct])
                user_score_per_level.append({'question_count_level': questions_count_level, 'correct_answers_count': correct_answers_count, 'level': level})
            return JsonResponse({'user_answers': [model_to_dict(i) for i in queryset], 'user_score_per_level': user_score_per_level})
        elif get_type=='levels_has_question':
            return JsonResponse({'levels': [i['level'] for i in models.FunStuntQA.objects.all().values("level").distinct()]})

            
@token_auth(roles=['admin', 'user'], get_user=True)
def children_management(auth: ta_models.UserAuthentication, request: WSGIRequest):
    user = models.UserProfile.objects.get(authentication=auth)
    if request.method == 'GET':
        get_type = request.GET['get_type']
        
        if get_type=='all':
            all_childrens = user.children_set.all()
        else:
            all_childrens = user.children_set.filter(id=int(request.GET['child_id']))

        childrens_traces = []
        for child in all_childrens:
            last_child_trace = models.StuntingTrace.objects.filter(children=child).order_by('-week')
            if len(last_child_trace)==0:
                last_child_trace = None
            else:
                last_child_trace = model_to_dict(last_child_trace[0])
            childrens_traces.append({'last_child_trace': last_child_trace, 'children': model_to_dict(child)})
        return JsonResponse({'all_childrens': childrens_traces})
    elif request.method == 'POST':
        data = json.loads(request.body)
        # data['child_info']['name'] = str(data['child_info']['name']).capitalize
        child_info = {
            'parent': user,
            **data['child_info']
        }
        child_info['born_date'] = datetime.date(**child_info['born_date'])
        
        child = models.Children(**child_info)
        child.save()
        return JsonResponse({'saved_child': model_to_dict(child)})
    elif request.method == 'PATCH':
        data = json.loads(request.body)
        existing_child = models.Children.objects.get(id=data['child_id'])
        child_info = {
            'parent': user,
            **data['child_info']
        }
        child_info['born_date'] = datetime.date(**child_info['born_date'])        
        child = utils.auto_set_obj_attrs(existing_child, child_info)
        child.save()
        return JsonResponse({'updated_child': model_to_dict(child)})
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        todelete_child = models.Children.objects.get(id=data['child_id'])
        todelete_child.delete()
        return JsonResponse({'deleted_child': model_to_dict(todelete_child)})
    return HttpResponseNotFound()

        
def data_stats(request: WSGIRequest):
    #get all final trace from child
    all_childs = models.Children.objects.all()
    childs_trace = dict()
    availble_trace = 0
    for child in all_childs:
        the_traces = models.StuntingTrace.objects.filter(children=child).order_by('-week')
        child = child.id
        if len(the_traces)==0:
            childs_trace[child] = None
            continue
        availble_trace += 1
        childs_trace[child] = model_to_dict(the_traces[0])
        trace_updated_date:datetime.date = the_traces[0].updated_at.date()
        childs_trace[child]['updated_at'] = {'year': trace_updated_date.year, 'month': trace_updated_date.month, 'day': trace_updated_date.day}
    
    # stunting bar, percentage, trends
    growth_agemonth_stunting = dict()
    growth_group_count = dict()
    growth_date_trends = dict()

    for child_id, trace in childs_trace.items():
        if trace is None:
            continue
        child = all_childs.filter(id=child_id)
        age_in_month = trace['week']%4
        growth_level = trace['growth_level']

        # Percentage / pie
        if not (growth_level in growth_group_count):
            growth_group_count[growth_level] = 1
        else:
            growth_group_count[growth_level] += 1
        
        # stunting bar
        if not (growth_level in growth_agemonth_stunting):
            growth_agemonth_stunting[growth_level] = dict()
        if not age_in_month in growth_agemonth_stunting[growth_level]:
            growth_agemonth_stunting[growth_level][age_in_month] = 1
        else:
            growth_agemonth_stunting[growth_level][age_in_month] += 1

        # trends
        trace_updated_at = datetime.date(**trace['updated_at'])
        if not (growth_level in growth_date_trends):
            growth_date_trends[growth_level] = dict()

        if not (trace_updated_at in growth_date_trends[growth_level]):
            growth_date_trends[growth_level][trace_updated_at] = 1
        else:
            growth_date_trends[growth_level][trace_updated_at] += 1
        
    growth_date_trends = {key1:{f'{key.year}-{key.month}-{key.day}':growth_date_trends[key1][key] for key in sorted(growth_date_trends[key1].keys())} for key1 in growth_date_trends}
    growth_agemonth_stunting = {key1:{f'{key.year}-{key.month}-{key.day}':growth_agemonth_stunting[key1][key] for key in sorted(growth_agemonth_stunting[key1].keys())} for key1 in growth_agemonth_stunting}
    

    return JsonResponse({'child_traces': childs_trace, 'growth_agemonth_stunting': growth_agemonth_stunting, 'availble_trace': availble_trace, 'growth_group_count': growth_group_count, 'growth_group_total': sum(growth_group_count.values()), 'growth_date_trends': growth_date_trends})

    

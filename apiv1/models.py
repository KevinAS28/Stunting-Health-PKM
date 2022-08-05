from django.db import models
from token_authentication import models as ta_models
# Create your models here.

class GeneralConfig(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)

class UserProfile(models.Model):
    authentication = models.OneToOneField(ta_models.UserAuthentication, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=30)
    email = models.CharField(max_length=30, default='', blank=True, null=True)
    profile_file = models.CharField(max_length=40)

class Children(models.Model):
    name = models.CharField(max_length=50)
    born_date = models.DateField()
    gender = models.IntegerField()
    active = models.BooleanField(default=True)
    parent = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    

class StuntReminder(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    clock = models.TimeField()
    repeat_each = models.TextField(max_length=50)
    on = models.BooleanField(default=True)

class StuntingTrace(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    week = models.IntegerField()
    height = models.FloatField()
    weight = models.FloatField()
    age_day = models.IntegerField(default=0)
    exclusive_asi = models.BooleanField(default=True)
    disease_history = models.BooleanField(default=True)
    immunization_history = models.CharField(max_length=60)
    children = models.ForeignKey(Children, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = (('user', 'week', 'children'),)    

class Article(models.Model):
    article_file = models.CharField(max_length=50)
    article_cover_file = models.CharField(max_length=50, default='')
    title = models.CharField(max_length=30)
    date = models.DateField()
    article_type = models.CharField(max_length=20) # exmaple: stunting_info, nutrition_info
    article_sub_type = models.CharField(max_length=20, default='') # exmaple: breakfast, lunch
    article_tags = models.CharField(max_length=63, default='') # exmaple: protein|karbo|etc..

class StuntPlace(models.Model):
    location_lat = models.FloatField()
    location_lng = models.FloatField()
    place_name = models.CharField(max_length=50)
    gmap_place_id = models.CharField(max_length=50)
    img_url = models.CharField(max_length=150, default='')
    phone = models.CharField(max_length=15, default='')
    desc = models.CharField(max_length=100, default='')
    avg_rating = models.FloatField()

class StuntPlaceReview(models.Model):
    stunt_place = models.ForeignKey(StuntPlace, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField()
    desc = models.CharField(max_length=200)

class HealthWorker(models.Model):
    name = models.CharField(max_length=50)
    work_place = models.ForeignKey(StuntPlace, on_delete=models.SET_NULL, null=True, blank=True)
    specialization = models.CharField(max_length=25)
    desc = models.CharField(max_length=150, default='')

class FunStuntQA(models.Model):
    question_file = models.CharField(max_length=50)
    answers_file = models.CharField(max_length=50)
    level = models.IntegerField()
    correct_answer = models.IntegerField()

class FunStuntUserAnswer(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.ForeignKey(FunStuntQA, on_delete=models.SET_NULL, null=True, blank=True)
    answer = models.IntegerField()
    answer_is_correct = models.BooleanField()
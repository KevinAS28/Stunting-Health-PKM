from django.db import models
from token_authentication import models as ta_models
# Create your models here.

class UserProfile(models.Model):
    authentication = models.OneToOneField(ta_models.UserAuthentication, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=30)
    email = models.CharField(max_length=30, default='', blank=True, null=True)
    profile_file = models.CharField(max_length=40)

class StuntReminder(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    clock = models.TimeField()
    repeat_each = models.TextField(max_length=50)
    on = models.BooleanField(default=True)

class StuntingTrace(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    week = models.IntegerField()
    height = models.FloatField()
    weight = models.FloatField()
    age_day = models.IntegerField(default=0)
    exclusive_asi = models.BooleanField(default=True)
    disease_history = models.BooleanField(default=True)
    immunization_history = models.CharField(max_length=60)

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
   
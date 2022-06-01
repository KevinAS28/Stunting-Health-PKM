from django.urls import path
import apiv1.views as views

app_name='apiv1'

urlpatterns = [
    path('test', views.test),
    path('profile', views.user_profile),
    path('reminder', views.stunt_reminder),
    path('trace', views.stunting_trace),
    path('maps', views.stunt_maps)
]
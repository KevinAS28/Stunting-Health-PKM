from django.urls import path
import apiv1.views as views

app_name='apiv1'

urlpatterns = [
    path('test', views.test),
    path('user', views.user),
    path('reminder', views.stunt_reminder),
    path('trace', views.stunting_trace),
    path('maps', views.stunt_maps),
    path('maps_admin', views.stunt_maps_admin),
    path('article', views.article),
    path('profile_admin', views.profile_admin),
    path('review', views.review),
    path('fun_stunt_admin', views.fun_stunt_admin),
    path('fun_stunt_user', views.fun_stunt_user),
    path('children_management', views.children_management),
    path('data_stats', views.data_stats),
    path('download_excel', views.download_excel)
]
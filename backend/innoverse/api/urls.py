from django.urls import path, include
from . import views
from rest_framework import routers
import participant.urls


router = routers.DefaultRouter()



urlpatterns = [

    path('', include(router.urls)),
    
    path('recordentry/<str:id>/', 
     views.RecordEntryViewSet.as_view({
         'get': 'list',
         'post': 'create',
         'delete': 'destroy'
     }), 
     name="record-entry"),

    
    path('gifts/<str:id>/', 
         views.GiftsStatusViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }), 
         name="gifts-operations"),
   
    
    path('info/<str:id>/', 
         views.ParticipantTeamInfoViewSet.as_view({'get': 'list'}), name="user-info"),


    path('check/<str:page>/<str:event>/<str:id>/', views.CheckViewSet.as_view({'get': 'list'}), name="check-allowance"),
   

    
]

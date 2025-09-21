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

    
    
    

    
]
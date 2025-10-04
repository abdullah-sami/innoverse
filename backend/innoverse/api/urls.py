from django.urls import path, include
from . import views
from rest_framework import routers
import participant.urls

router = routers.DefaultRouter()
router.register(r'participant', views.ParticipantViewSet, basename='participant')
router.register(r'team', views.TeamListViewSet, basename='team')
router.register(r'segment', views.SegmentViewSet, basename='segment')
router.register(r'competition', views.CompetitionViewSet, basename='competition')
router.register(r'team-competition', views.TeamCompetitionViewSet, basename='team-competition')


urlpatterns = [
    path('', include(router.urls)),
    
    path('register/', 
         views.RegisterViewSet.as_view({
             'get': 'list',
             'post': 'create'
         }), 
         name="register"),


     path('payment/verify/', views.PaymentVerificationViewSet.as_view({'post': 'create'}), name='payment-verify'),

     

     




    
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
         views.ParticipantTeamInfoViewSet.as_view({'get': 'list'}), 
         name="user-info"),
    
    path('check/<str:page>/<str:event>/<str:id>/', 
         views.CheckViewSet.as_view({'get': 'list'}), 
         name="check-allowance"),
]
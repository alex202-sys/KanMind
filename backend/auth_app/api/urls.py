#api/urls.py
from django.urls import path
from .views import UserProfileList, RegistrationView, UserLoginView, UserProfileDetail
#UserProfileDetail, CustomLoginView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # path('',),
    path('profiles/', UserProfileList.as_view(), name='userprofile-list'),
    path('profiles/<int:pk>/', UserProfileDetail.as_view(), name='userprofile-detail'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', UserLoginView.as_view(), name='login'),
    #path('login/', obtain_auth_token, name='login'),

]
from django.urls import include, path
from .views import UserProfileList, RegistrationView, UserLoginView, UserProfileDetail

urlpatterns = [
    path("profiles/", UserProfileList.as_view(), name="userprofile-list"),
    path("profiles/<int:pk>/", UserProfileDetail.as_view(), name="userprofile-detail"),
    path("registration/", RegistrationView.as_view(), name="api-registration"),
    path("login/", UserLoginView.as_view(), name="api-login"),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]

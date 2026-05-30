from django.contrib.auth.models import User
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from auth_app.models import UserProfile
from .serializers import RegistrationSerializer, UserProfileSerializer


class UserProfileList(generics.ListCreateAPIView):
    """_summary_

    Args:
        generics (_type_): _description_

    Returns:
        _type_: _description_
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    """_summary_

    Args:
        generics (_type_): _description_

    Returns:
        _type_: _description_
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]

        return [permissions.IsAuthenticatedOrReadOnly()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)

        if not request.user.is_staff and obj.user != request.user:
            self.permission_denied(
                request, message="Only the owner or an admin may modify this profile.."
            )


class RegistrationView(generics.CreateAPIView):
    """_summary_

    Args:
        generics (_type_): _description_

    Returns:
        _type_: _description_
    """

    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            try:
                saved_account = serializer.save()
                token, created = Token.objects.get_or_create(user=saved_account)
                data = {
                    "token": token.key,
                    "fullname": f"{saved_account.first_name} {saved_account.last_name}".strip()
                    or saved_account.username,
                    "email": saved_account.email,
                    "user_id": saved_account.pk,
                }
                return Response(data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(ObtainAuthToken):
    """_summary_

    Args:
        ObtainAuthToken (_type_): _description_
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        if email and not request.data.get("username"):
            try:
                user_obj = User.objects.get(email=email)
                request.data["username"] = user_obj.username
            except User.DoesNotExist:
                return Response(
                    {"error", "User with same email dosnt match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            data = {
                "token": token.key,
                "fullname": f"{user.first_name} {user.last_name}".strip()
                or user.username,
                "email": user.email,
                "user_id": user.id,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

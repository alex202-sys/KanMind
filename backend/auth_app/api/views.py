#api/views.py
from rest_framework import generics, status, permissions
from auth_app.models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import RegistrationSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
#from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR



class UserProfileList(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    #permission_class = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        return [permissions.IsAdminUser()]



class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    #permission_class = [AllowAny]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        
        # 2. Für Änderungen (PATCH, PUT, DELETE): Nur Admins oder eingeloggte User
        return [permissions.IsAuthenticatedOrReadOnly()]  #IsAdminUser IsAuthenticated

    def check_object_permissions(self, request, obj):
        # Führt die Standard-Checks aus (z.B. für IsAdminUser)
        super().check_object_permissions(request, obj)
        
        # 3. Besitz-Prüfung für PATCH, PUT und DELETE
        #if request.method not in permissions.SAFE_METHODS:
            # Wenn der User kein Admin ist, MUSS er der Besitzer des Profils sein
        if not request.user.is_staff and obj.user != request.user:
            self.permission_denied(
                request, 
                message="Only the owner or an admin may modify this profile.."
            )

class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
             serializer = RegistrationSerializer(data=request.data)
             data={}
             if serializer.is_valid():
                # Alles andere (Profil erstellen, Namen splitten) passiert automatisch im Serializer oben.
                try:
                    saved_account = serializer.save()
                    token, created = Token.objects.get_or_create(user=saved_account)
                    data = {'token': token.key,
                            'fullname': f"{saved_account.first_name} {saved_account.last_name}".strip() or saved_account.username,
                            'email': saved_account.email,
                            'user_id': saved_account.pk # .pk oder .id gibt die ID zurück
                            # 'message': "User and Profile created successfully.",
                            }
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
                    data = serializer.errors   

class UserLoginView(ObtainAuthToken):
        #permission_classes=[AllowAny]
        # serializer_class = RegistrationSerializer
        def post(self, request, *args, **kwargs):
             email = request.data.get('email')
             if email and not request.data.get('username'):
                try:
                  user_obj = User.objects.get(email=email)
                  request.data['username'] = user_obj.username
                except User.DoesNotExist:
                  return Response({"error","User with same email dosnt match"}, status=status.HTTP_400_BAD_REQUEST ) 

             serializer = self.serializer_class(data=request.data)
             print("request.data:", request.data)
             print("serializer: ", serializer)

             if serializer.is_valid():
                user=serializer.validated_data['user']
                token, created = Token.objects.get_or_create(user=user)
                data = {'token': token.key,
                        #'username': username,
                        'fullname': f"{user.first_name} {user.last_name}".strip() or user.username,
                        'email': user.email,
                        'user_id': user.id,
                        }
                return Response(data, status=status.HTTP_200_OK)
            #  else:
            #     data = serializer.errors   
             return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)

   
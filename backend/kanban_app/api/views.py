from .serializers import BoardsSerializer, TaskSerializer
from kanban_app.models import Board, Task
from rest_framework import permissions, generics
#from .permissions import isOwnerOrMitglied


class BoardListView(generics.ListCreateAPIView,
                    ):
    queryset = Board.objects.all()
    serializer_class = BoardsSerializer
    #permission_class = [isOwnerOrMitglied]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        return [permissions.IsAdminUser()] # IsAdminUser
    
    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(member=user)).distinct() 
    
    
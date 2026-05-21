from .serializers import BoardsSerializer, TaskSerializer
from kanban_app.models import Board
from rest_framework import permissions, generics, mixins, viewsets
#from .permissions import isOwnerOrMitglied
from django.db.models import Q


#class BoardListView(generics.ListCreateAPIView):
class BoardListView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    
    queryset = Board.objects.all()
    serializer_class = BoardsSerializer
    #permission_class = [isOwnerOrMitglied]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        return [permissions.IsAdminUser()] # IsAdminUser
    
    def get_queryset(self):
        user = self.request.user

        for board in Board.objects.all():
            print(f"Board: {board.title} | Owner: {board.owner} | Members: {list(board.member.all())}")
        # print(f"Aktuell angemeldeter User {user} im Request with id: {user.id}")
        # print("Filter: ", Board.objects.filter(owner='2'))

        return Board.objects.filter(
            Q(owner=user) | Q(member=user)
        ).distinct()
    
    #anzahl = Employee.objects.filter(salary__gte=5000).count()
		# print(anzahl) 
        
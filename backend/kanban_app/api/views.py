from .serializers import BoardsSerializer, TaskSerializer
from kanban_app.models import Board, Task
from rest_framework import permissions, generics, mixins, viewsets
#from .permissions import isOwnerOrMitglied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q


#class BoardListView(generics.ListCreateAPIView):
class BoardListView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
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
        print("Ob user staff ist", user, "  ", user.is_staff)
        if  not user.is_staff:
            return Board.objects.filter(
                Q(owner=user) | Q(member=user)
            ).distinct()
        else:
            return Board.objects.all()
    
    #anzahl = Employee.objects.filter(salary__gte=5000).count()
		# print(anzahl) 
        

class TasksView(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                mixins.UpdateModelMixin,
                mixins.RetrieveModelMixin,
                mixins.DestroyModelMixin,
                viewsets.GenericViewSet
                ):
    """
    API-Endpunkt für die Verwaltung von Tasks.
    
    DELETE /api/tasks/{id}/
    Achtung: Die Löschung einer Task ist dauerhaft und kann nicht rückgängig gemacht werden!
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    #permission_classes = [IsAuthenticatedOrReadOnly]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """
        Returns all tasks for which the currently
        logged-in user is listed as 'assigned'.
        """
        # Filtert die Tasks nach dem aktuellen User (request.user)
        user_tasks = Task.objects.filter(assignee=request.user)
        
        # Nutzen des bestehenden Serializers (inklusive Pagination, falls aktiv)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing_to_me(self, request):
        """
        Returns all tasks for which the currently
        logged-in user is listed as 'reviewing'.
        """
        user_tasks = Task.objects.filter(reviewer=request.user)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_responser(serializer.data)
        
        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)
    
    # @action(detail=False, methods=['post'], url_path='assigned-to-me')
    # def assigned_to_me(self, request):

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(
            Q(board_member=user) | Q(board_owner=user)
        ).distinct()
    
    def destroy(self, request, *args, **kwargs):
        # Holt die Task (wirft automatisch 404, wenn sie laut get_queryset nicht existiert)
        instance = self.get_object()
        user = request.user

        # Superuser darf immer löschen
        if user.is_superuser:
            return super().destroy(request, *args, **kwargs)

        # Prüfen, ob der User der Ersteller der Task ODER der Besitzer des Boards ist
        # HINWEIS: Passen Sie 'creator' an das exakte Feld in Ihrem Task-Model an (z.B. 'created_by')
        is_task_creator = getattr(instance, 'creator', None) == user
        is_board_owner = instance.board.owner == user

        if not (is_task_creator or is_board_owner):
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller der Task oder der Eigentümer des Boards kann eine Task löschen."
            )

        # Führt die dauerhafte Löschung aus (gibt HTTP 204 No Content zurück)
        return super().destroy(request, *args, **kwargs)
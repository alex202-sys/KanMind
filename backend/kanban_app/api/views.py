from .serializers import BoardsSerializer, TaskSerializer, UserNestedSerializer, TaskCommentSerializer
from kanban_app.models import Board, Task, Comment
from rest_framework import permissions, generics, mixins, viewsets
#from .permissions import isOwnerOrMitglied
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED


#class BoardListView(generics.ListCreateAPIView):
class BoardListView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    
    queryset = Board.objects.all()
    serializer_class = BoardsSerializer

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_superuser and 'owner' in self.request.data:
            new_owner_id = self.request.data.get('owner')
            serializer.save(owner_id=new_owner_id)
        else:
            serializer.save()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()] # oder IsAuthenticated(),AllowAny  falls eingeloggt Pflicht ist
        return [permissions.IsAdminUser()] # IsAdminUser
    
    def get_queryset(self):
        user = self.request.user

        if  not user.is_superuser:
            return Board.objects.filter(
                Q(owner=user) | Q(member=user)
            ).distinct()
        else:
            return Board.objects.all()

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
    
    def perform_create(self, serializer):
        # Speichert die neue Task und setzt automatisch den angemeldeten User als Creator
        serializer.save(creator=self.request.user)


    @action(detail=True, methods=['delete'], url_path=r'comments/(?P<comment_id>[^/.]+)', permission_classes=[AllowAny]) 
    def delete_comments(self, request,  pk=None, comment_id=None):
        """
        DELETE /api/tasks/{task_id}/comments/{comment_id}/
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("404: Kommentar oder Task nicht gefunden.")

        try:
            comment = Comment.objects.get(pk=comment_id, task=task)
            print('comment', comment)
        except Comment.DoesNotExist:
            raise NotFound("404: Kommentar oder Task nicht gefunden.")

        if comment.author != request.user: 
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller des Kommentars darf ihn löschen."
            )

        comment.delete()
        return Response("204: Der Kommentar wurde erfolgreich gelöscht.", status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get','post'], url_path='comments', permission_classes=[AllowAny]) 
    def comments(self, request,  pk=None):
        """
        GET /api/tasks/{task_id}/comments/  -> Liste abrufen
        POST /api/tasks/{task_id}/comments/ -> Neuen Kommentar hinzufügen
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("404: Task nicht gefunden. Die angegebene Task-ID existiert nicht.")
            #Response ()

        board = task.board
        allowed_users = set(board.member.all())
        if request.user not in allowed_users and not request.user.is_superuser:
            raise PermissionDenied(
                "403: Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
            )
        
        if request.method == 'GET':
            comments = task.comments.all().order_by('created_at')
            serialiser = TaskCommentSerializer(comments, many=True)
            return Response(serialiser.data, status=status.HTTP_200_OK)

        if request.method == 'POST':
            content = request.data.get('content')
            if not content or str(content).strip() == "":
                return Responser (
                    {"detail": "400: Bad Request. Der Inhalt des Kommentars darf nicht leer sein."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if request.user and request.user.is_authenticated:
                author = request.user
            else:
                return Response(
                    {"detail":"401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                    status=status.HTTP_401_UNAUTHORIZED
                    )

            new_comment = Comment.objects.create(
                task=task,
                author=author,
                content=content
            )
            serialiser = TaskCommentSerializer(new_comment)
            return Response(serialiser.data, status=status.HTTP_201_CREATED)
        
        
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
            Q(board__member=user) | Q(board__owner=user)
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
        #is_task_creator = instance.created == user
        is_board_owner = instance.board.owner == user

        if not (is_task_creator or is_board_owner):
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller der Task oder der Eigentümer des Boards kann eine Task löschen."
            )

        # Führt die dauerhafte Löschung aus (gibt HTTP 204 No Content zurück)
        return super().destroy(request, *args, **kwargs)
    
# class EmailCheck(mixins.ListModelMixin,
#                 viewsets.GenericViewSet
#                 ):
#     queryset = User.objects.all()
#     serializer_class = UserNestedSerializer

class EmailCheckView(mixins.ListModelMixin,
                viewsets.GenericViewSet
                ):
        queryset = User.objects.all()
        serializer_class = UserNestedSerializer
        #permission_classes = [IsAuthenticated]

        def list(self, request, *args, **kwargs):
            email = request.query_params.get('email')

            if not request or not request.user.is_authenticated:
                print('not request:', request,' or request.user: ', request.user)
                return Response(
                    {"error": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not email:
                return Response(
                    {"error": "400: Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_obj = User.objects.get(email=email)
                print('user_obj :', user_obj)
                serializer = self.get_serializer(user_obj)
                return Response(serializer.data, status=status.HTTP_200_OK) 
        
            except User.DoesNotExist:
                return Response({"error":"404: Email nicht gefunden. Die Email exestiert nicht."}, status=status.HTTP_404_NOT_FOUND ) 
            
# class CommentsOfTaskView(mixins.ListModelMixin,
#                 viewsets.GenericViewSet
#                 ):
#         queryset = Comment.objects.all()
#         serializer_class = TaskCommentSerializer
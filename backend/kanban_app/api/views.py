from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
import logging
from rest_framework.views import exception_handler
from .serializers import BoardsSerializer, TaskSerializer, UserNestedSerializer, TaskCommentSerializer
from kanban_app.models import Board, Task, Comment

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        logger.error(f"Unerwarteter Serverfehler: {exc}", exc_info=True)
        
        return Response(
            {"detail": "500: Interner Serverfehler."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response

class BoardListView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    
    queryset = Board.objects.all()
    serializer_class = BoardsSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        
        if not request.user or not request.user.is_authenticated:
            from rest_framework.exceptions import NotAuthenticated
            raise NotAuthenticated("401: Nicht autorisiert. Der Benutzer muss eingeloggt sein.")

    def perform_create(self, serializer):
        members = self.request.data.get('members', [])
        if members:
            unique_members = list(set(members))
            valid_members = User.objects.filter(id__in=unique_members)
            if valid_members.count() != len(unique_members):
                raise ValidationError("400: Ungültige Anfragedaten. Möglicherweise sind einige Benutzer-Email-Adressen ungültig.")

            instance = serializer.save(owner=self.request.user)
            instance.member.set(valid_members)  
        else:
            instance = serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user

        request_data = self.request.data
        members_data = request_data.get('members', None)
        if members_data is not None:
            if not isinstance(members_data, list):
                raise ValidationError("400: Ungültige Anfragedaten. Möglicherweise sind einige Benutzer ungültig.")
            
            unique_members = list(set(members_data))

            valid_members = User.objects.filter(id__in=unique_members)
            if valid_members.count() != len(unique_members):
                raise ValidationError("400: Ungültige Anfragedaten. Möglicherweise sind einige Benutzer ungültig")
            
            board_instance = serializer.save()
            board_instance.member.set(valid_members)



        if user.is_superuser and 'owner' in self.request.data:
            new_owner_id = self.request.data.get('owner')
            serializer.save(owner_id=new_owner_id)
        else:
            serializer.save()
    
    def get_queryset(self):
        user = self.request.user

        if  not user.is_superuser:
            return Board.objects.filter(
                Q(owner=user) | Q(member=user)
            ).distinct()
        else:
            return Board.objects.all()
        
    def retrieve(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        pk = kwargs.get('pk')
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            raise NotFound("404: Board nicht gefunden. Die angegebene Board-ID existiert nicht.")

        if not request.user.is_superuser:
            is_owner = (board.owner == request.user)
            is_member = board.member.filter(id=request.user.id).exists()
            
            if not is_owner and not is_member:
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss entweder Mitglied des Boards oder der Eigentümer des Boards sein."
                )

        serializer = self.get_serializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)
  

class TasksView(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                mixins.UpdateModelMixin,
                mixins.RetrieveModelMixin,
                mixins.DestroyModelMixin,
                viewsets.GenericViewSet
                ):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        return super().perform_update(serializer)

    @action(detail=True, methods=['delete'], url_path=r'comments/(?P<comment_id>[^/.]+)', permission_classes=[AllowAny]) 
    def delete_comments(self, request,  pk=None, comment_id=None):

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
                return Response (
                    {"detail": "400: Ungültige Anfragedaten. Möglicherweise ist der `content`-Wert leer."},
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

            return Response(
            {"detail": "201: Der Kommentar wurde erfolgreich erstellt."},
            status=status.HTTP_201_CREATED
        )
        
    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        user_tasks = Task.objects.filter(assignee=request.user)
        
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing_to_me(self, request):
        user_tasks = Task.objects.filter(reviewer=request.user)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(
            Q(board__member=user) | Q(board__owner=user)
        ).distinct()
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception:
            raise NotFound("404: Task nicht gefunden. Die angegebene Task-ID existiert nicht.")

        user = request.user
        if user.is_superuser:
            return super().destroy(request, *args, **kwargs)

        is_task_creator = getattr(instance, 'creator', None) == user
        is_board_owner = instance.board.owner == user
        if not (is_task_creator or is_board_owner):
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller der Task oder der Eigentümer des Boards kann eine Task löschen."
            )
        instance.delete()
        return Response(
            {"detail": "204: Die Task wurde erfolgreich gelöscht."},
            status=status.HTTP_204_NO_CONTENT
        )

    

class EmailCheckView(mixins.ListModelMixin,
                viewsets.GenericViewSet
                ):
        queryset = User.objects.all()
        serializer_class = UserNestedSerializer

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
           

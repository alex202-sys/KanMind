from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    ValidationError,
)
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_404_NOT_FOUND,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.views import exception_handler
from .serializers import (
    BoardsSerializer,
    TaskSerializer,
    UserNestedSerializer,
    TaskCommentSerializer,
)
from kanban_app.models import Board, Task, Comment
from .permissions import isBoardOwnerOrMemberBoardOrAllPost
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """_summary_

    Args:
        exc (_type_): _description_
        context (_type_): _description_

    Returns:
        _type_: _description_
    """
    response = exception_handler(exc, context)
    if response is None:
        logger.error(f"Unerwarteter Serverfehler: {exc}", exc_info=True)

        return Response(
            {"detail": "500: Interner Serverfehler."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


class BoardListView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """_summary_

    Args:
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        viewsets (_type_): _description_

    Raises:
        NotAuthenticated: _description_
        ValidationError: _description_
        PermissionDenied: _description_
        PermissionDenied: _description_
        ValidationError: _description_
        ValidationError: _description_
        ValidationError: _description_
        NotFound: _description_
        PermissionDenied: _description_

    Returns:
        _type_: _description_
    """

    queryset = Board.objects.all()
    serializer_class = BoardsSerializer
    permission_classes = [isBoardOwnerOrMemberBoardOrAllPost]

    def initial(self, request, *args, **kwargs):
        """_summary_

        Args:
            request (_type_): _description_

        Raises:
            NotAuthenticated: _description_
        """
        super().initial(request, *args, **kwargs)
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(
                "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."
            )

    def get_queryset(self):
        """
        - superusers have access to all boards.
        - GET/PUT/PATCH/DELETE: owner or Member.
        - DELETE: if not owner then permissiondenied in permissions.py.

        Returns:
            _type_: _description_
        """

        user = self.request.user
        if user.is_superuser:
            return Board.objects.all()

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return Board.objects.all()
        # all other methods except retrieve, update, partial_update, destroy: POST, GET (list), HEAD, OPTIONS
        return Board.objects.filter(Q(owner=user) | Q(member=user)).distinct()

    def perform_create(self, serializer):
        """set current user as owner of the board
           POST: all authenticated users may create a board.
           validate members is in validate BoardsSerializer,
           because we need to check if all members exist in
           the database before creating the board and adding members to it.
        Args:
            serializer (_type_): _description_
        """
        members_liste = serializer.validated_data.get("member", [])
        print("validated_data in perform_create:", serializer.validated_data)
        # members_liste = validated_data.pop("members", [])
        print("members_liste in perform_create:", members_liste)
        instance = serializer.save(owner=self.request.user)

        if members_liste:
            instance.member.set(members_liste)

    def perform_update(self, serializer):
        """Update the title and members if they were transmitted from the frontend,
        and the owner to the actual user if it was previously empty.
        Only the owner of the board or member can update the board,
        otherwise permission denied in permissions.py.
        """
        validate_members = serializer.validated_data.get("member", [])
        validate_title = serializer.validated_data.get("title", "")
        # if members or title in request data, then update the board,
        #  otherwise only update the title and do not change the members of the board
        if validate_members or validate_title:
            board_instance = serializer.save()
            board_instance.member.set(validate_members)

        # if no owner, set current user as owner of the board
        user = self.request.user
        aktuelles_board = serializer.instance
        aktueller_owner = aktuelles_board.owner
        if aktueller_owner is None:
            serializer.save(owner_id=user.id)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        """_summary_

        Args:
            instance (_type_): _description_
        """
        user = self.request.user
        if not user.is_superuser:
            is_owner = instance.owner == user
            if not is_owner:
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss der Eigentümer des Boards sein, um es zu löschen."
                )
        instance.delete()
        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )

    def retrieve(self, request, *args, **kwargs):
        """_summary_

        Args:
            request (_type_): _description_

        Raises:
            NotFound: _description_
            PermissionDenied: _description_

        Returns:
            _type_: _description_
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "detail": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        pk = kwargs.get("pk")
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            raise NotFound(
                "404: Board nicht gefunden. Die angegebene Board-ID existiert nicht."
            )

        if not request.user.is_superuser:
            is_owner = board.owner == request.user
            is_member = board.member.filter(id=request.user.id).exists()
            if not is_owner and not is_member:
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss entweder der Eigentümer oder ein Mitglied des Boards sein."
                )

        serializer = self.get_serializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TasksView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """_summary_

    Args:
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        mixins (_type_): _description_
        viewsets (_type_): _description_

    Raises:
        PermissionDenied: _description_
        NotFound: _description_
        PermissionDenied: _description_
        NotFound: _description_
        NotFound: _description_
        PermissionDenied: _description_
        NotFound: _description_
        PermissionDenied: _description_

    Returns:
        _type_: _description_
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return Task.objects.all()
        return Task.objects.filter(
            Q(board__member=user) | Q(board__owner=user)
        ).distinct()

    def perform_create(self, serializer):
        """_summary_

        Args:
            serializer (_type_): _description_
        """
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        """_summary_

        Args:
            serializer (_type_): _description_
        """
        user = self.request.user
        task_instance = serializer.instance
        board = task_instance.board
        if not user.is_superuser and board:
            is_member = board.member.filter(id=user.id).exists()
            if not is_member:
                raise PermissionDenied(
                    "403: Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
                )

        serializer.save()
        return super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        """_summary_

        Args:
            request (_type_): _description_

        Raises:
            NotFound: _description_
            PermissionDenied: _description_

        Returns:
            _type_: _description_
        """
        try:
            instance = self.get_object()
        except Exception:
            raise NotFound(
                "404: Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            )

        user = request.user
        is_task_creator = getattr(instance, "creator", None) == user
        is_board_owner = instance.board.owner == user if instance.board else False
        if not (is_task_creator or is_board_owner or user.is_superuser):
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller der Task oder der Eigentümer des Boards kann eine Task löschen."
            )
        instance.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        user_tasks = Task.objects.filter(assignee=request.user)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reviewing")
    def reviewing_to_me(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        user_tasks = Task.objects.filter(reviewer=request.user)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"comments/(?P<comment_id>[^/.]+)",
        permission_classes=[IsAuthenticated],
    )
    def delete_comments(self, request, pk=None, comment_id=None):
        """_summary_

        Args:
            request (_type_): _description_
            pk (_type_, optional): _description_. Defaults to None.
            comment_id (_type_, optional): _description_. Defaults to None.

        Raises:
            NotFound: _description_
            NotFound: _description_
            PermissionDenied: _description_

        Returns:
            _type_: _description_
        """
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "detail": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("404: Kommentar oder Task nicht gefunden.")

        try:
            comment = Comment.objects.get(pk=comment_id, task=task)
        except Comment.DoesNotExist:
            raise NotFound("404: Kommentar oder Task nicht gefunden.")

        if comment.author != request.user:
            raise PermissionDenied(
                "403: Verboten. Nur der Ersteller des Kommentars darf ihn löschen."
            )

        comment.delete()
        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
    )
    def comments(self, request, pk=None):
        """_summary_

        Args:
            request (_type_): _description_
            pk (_type_, optional): _description_. Defaults to None.

        Raises:
            NotFound: _description_
            PermissionDenied: _description_

        Returns:
            _type_: _description_
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound(
                "404: Task nicht gefunden. Die angegebene Task-ID existiert nicht."
            )

        board = task.board
        allowed_users = set(board.member.all())
        if request.user not in allowed_users and not request.user.is_superuser:
            raise PermissionDenied(
                "403: Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört."
            )

        if request.method == "GET":
            comments = task.comments.all().order_by("created_at")
            serialiser = TaskCommentSerializer(comments, many=True)
            return Response(serialiser.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            content = request.data.get("content")
            if not content or str(content).strip() == "":
                return Response(
                    {
                        "detail": "400: Ungültige Anfragedaten. Möglicherweise ist der `content`-Wert leer."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            author = request.user
            new_comment = Comment.objects.create(
                task=task, author=author, content=content
            )
            serialiser = TaskCommentSerializer(new_comment)

            return Response(serialiser.data, status=status.HTTP_201_CREATED)


class EmailCheckView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """_summary_

    Args:
        mixins (_type_): _description_
        viewsets (_type_): _description_

    Returns:
        _type_: _description_
    """

    queryset = User.objects.all()
    serializer_class = UserNestedSerializer

    def list(self, request, *args, **kwargs):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        email = request.query_params.get("email")

        if not request or not request.user.is_authenticated:
            return Response(
                {"error": "401: Nicht autorisiert. Der Benutzer muss eingeloggt sein."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not email:
            return Response(
                {
                    "error": "400: Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_obj = User.objects.get(email=email)
            serializer = self.get_serializer(user_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"error": "404: Email nicht gefunden. Die Email exestiert nicht."},
                status=status.HTTP_404_NOT_FOUND,
            )

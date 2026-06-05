from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
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
from .permissions import (
    IsMemberOwnerBoardOrCreatorTask,
    isBoardOwnerOrMemberBoardOrAllPost,
    isCreatorCommentOrSuperuser,
    isMemberOfBoardsOrSuperuser,
)
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler that logs unexpected server errors
    and returns a generic error message for 500 Internal Server Errors.
    It uses the default DRF exception handler for known exceptions and
    only logs and modifies the response for unhandled exceptions."""
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
    """ViewSet for managing Board instances with custom permissions and behaviors.
    - GET: List all boards where the user is the owner or a member, or all boards for superusers.
    - POST: Create a new board (all authenticated users can create).
    """

    queryset = Board.objects.all()
    serializer_class = BoardsSerializer
    permission_classes = [isBoardOwnerOrMemberBoardOrAllPost]

    def get_queryset(self):
        """
        - superusers have access to all boards.
        - GET/PUT/PATCH/DELETE: owner or Member.
        - DELETE: if not owner then permissiondenied in permissions.py.
        """
        user = self.request.user
        if user.is_superuser:
            return Board.objects.all()
        # for permissionsdeneid check in permissions-> all objects
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return Board.objects.all()
        # all other methods except retrieve, update, partial_update, destroy: POST, GET (list), HEAD, OPTIONS
        return Board.objects.filter(Q(owner=user) | Q(member=user)).distinct()

    def perform_create(self, serializer):
        """set current user as owner of the board
        POST: all authenticated users may create a board.
        """
        serializer.save(owner=self.request.user)


class TasksView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing Task instances with custom permissions and behaviors.
    - GET: List all tasks where the user is the creator, or the user is assignee
      or reviewer, or the user is a member of the board to which the task belongs,
      or all tasks for superusers.
    - POST: Create a new task (only for members of the board to which the task belongs
      or superusers can create tasks). The creator of the task is set to the current user.
    - PUT/PATCH: Update a task (only for members of the board to which the task belongs
      or superusers can update tasks).
    - DELETE: Delete a task (only the creator of the task, the owner of the board
      to which the task belongs, or superusers can delete tasks).
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsMemberOwnerBoardOrCreatorTask]

    def get_queryset(self):
        """
        - superusers have access to all tasks.
        - GET: assignee, reviewer
        - PUT/PATCH: member of the board
        - DELETE: check if task exist
        """
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()

        # check if task exist, otherwise not found in destroy method
        if self.action in ["destroy", "comments"]:
            try:
                obj_delete = Task.objects.get(pk=self.kwargs.get("pk"))
                return Task.objects.all()
            except Task.DoesNotExist:
                raise NotFound(
                    "404: Task not found. The specified task ID does not exist."
                )

        # retrieve, update, partial_update, post, # , "create", "post",
        if self.action in ["update", "partial_update"]:
            return Task.objects.filter(board__member=user).distinct()

        # GET, retrieve for assignee, reviewer in tasks
        return Task.objects.filter(Q(assignee=user) | Q(reviewer=user)).distinct()

    def perform_create(self, serializer):
        """Set the creator of the task to the current user when creating a new task.
        Only members of the board to which the task belongs or superusers can create tasks.
        """
        serializer.save(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Only the creator of the task or the owner of the board to which the task belongs,
        or superusers can delete tasks. if owner is None ignore it.
        """
        instance = self.get_object()
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        """List all tasks where the user is the assignee."""

        user_tasks = Task.objects.filter(assignee=request.user)
        page = self.paginate_queryset(user_tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(user_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reviewing")
    def reviewing_to_me(self, request):
        """List all tasks where the user is the reviewer."""
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
        permission_classes=[isCreatorCommentOrSuperuser],
    )
    def delete_comments(self, request, pk=None, comment_id=None):
        """Delete a comment from a task. Only the author of the comment can delete it."""
        task = self.get_object()

        try:
            comment = task.comments.get(id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound("404: comment not found.")

        task.comments.filter(id=comment_id).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="comments",
        permission_classes=[isMemberOfBoardsOrSuperuser],
    )
    def comments(self, request, pk=None):
        """Handle GET and POST requests for comments related to a specific task.
        Only members of the board to which the task belongs can access this endpoint.
        """

        try:
            task = self.get_object()
        except Task.DoesNotExist:
            raise NotFound("404: Task not found. The specified task ID does not exist.")

        if request.method == "GET":
            comments = task.comments.all().order_by("created_at")
            serialiser = TaskCommentSerializer(comments, many=True)
            return Response(serialiser.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            content = request.data.get("content")
            if not content or str(content).strip() == "":
                return Response(
                    {
                        "detail": "400: Invalid request data. The `content` value might be empty."
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
    """ViewSet for checking if a user with a given email exists.
    It allows authenticated users to check if an email is already associated
    with an existing user account."""

    queryset = User.objects.all()
    serializer_class = UserNestedSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """Check if a user with the given email exists and return their details.
        Only authenticated users can access this endpoint."""
        email = request.query_params.get("email")

        if not email:
            return Response(
                {
                    "error": "400: Invalid request. The email address is missing or has an incorrect format."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_obj = User.objects.get(email=email)
            serializer = self.get_serializer(user_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "404: Email not found. The email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
from .permissions import (
    IsMemberOwnerBoardOrCreatorTask,
    isBoardOwnerOrMemberBoardOrAllPost,
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
        """Only the owner of the board can delete the board, otherwise
        permission denied in permissions.py. Superusers can delete any board.
        If the user is authorized to delete the board,
        it is deleted and a 204 No Content response is returned.
        """
        instance.delete()
        return Response(
            None,
            status=status.HTTP_204_NO_CONTENT,
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a board instance. Only the owner of the board
        or member can retrieve the board, otherwise permission denied
        in permissions.py. Superusers can retrieve any board.
        """
        pk = kwargs.get("pk")
        try:
            board = Board.objects.get(pk=pk)
        except Board.DoesNotExist:
            raise NotFound(
                "404: Board not found. The specified Board ID does not exist."
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

        # delete
        if self.action == "destroy":
            try:
                obj_delete = Task.objects.get(pk=self.kwargs.get("pk"))
                return Task.objects.all()
            except Task.DoesNotExist:
                raise NotFound(
                    "404: Task not found. The specified task ID does not exist."
                )

        # retrieve, update, partial_update, post
        if self.action in ["update", "partial_update", "create", "post"]:
            return Task.objects.filter(board__member=user).distinct()

        # GET, retrieve for assignee, reviewer in tasks
        return Task.objects.filter(Q(assignee=user) | Q(reviewer=user)).distinct()

    def perform_create(self, serializer):
        """Set the creator of the task to the current user when creating a new task.
        Only members of the board to which the task belongs or superusers can create tasks.
        """
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        """Only members of the board to which the task belongs or superusers can update tasks.
        If the user is not authorized to update the task, a PermissionDenied exception is raised.
        """
        # user = self.request.user
        # task_instance = serializer.instance
        # board = task_instance.board
        # if not user.is_superuser and board:
        #     is_member = board.member.filter(id=user.id).exists()
        #     if not is_member:
        #         raise PermissionDenied(
        #             "403: Forbidden. The user must be a member of the board to which the task belongs."
        #         )

        serializer.save()
        return super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        """Only the creator of the task, the owner of the board to which the task belongs,
        or superusers can delete tasks. If the user is not authorized to delete the task,
        a PermissionDenied exception is raised. If the task does not exist,
        a NotFound exception is raised. If the user is authorized to delete the task,
        it is deleted and a 204 No Content response is returned.
        """

        instance = self.get_object()
        print("Task to delete:", instance)
        self.perform_destroy(instance)
        # user = request.user
        # is_task_creator = getattr(instance, "creator", None) == user
        # is_board_owner = instance.board.owner == user if instance.board else False
        # if not (is_task_creator or is_board_owner or user.is_superuser):
        #     raise PermissionDenied(
        #         "403: Forbidden. Only the creator of the task or the owner of the board can delete a task."
        #     )
        # instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        """List all tasks where the user is the assignee.
        Only members of the board to which the task belongs or superusers can access this endpoint.
        If the user is not authenticated, a 401 Unauthorized response is returned.
        If the user is authenticated, a list of tasks assigned to the user is returned,
          with pagination if applicable.
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
        """List all tasks where the user is the reviewer.
        Only members of the board to which the task belongs or superusers
        can access this endpoint. If the user is not authenticated,
        a 401 Unauthorized response is returned. If the user is authenticated,
        a list of tasks reviewing the user is returned, with pagination if applicable.
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
        """Delete a comment from a task. Only the author of the comment can delete it.
        If the user is not authenticated, a 401 Unauthorized response is returned.
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
        """Handle GET and POST requests for comments related to a specific task.
        For GET requests, it retrieves all comments for the specified task and
        returns them in the response. For POST requests, it creates a new comment
        for the specified task with the content provided in the request data and
        the author set to the current user. Only members of
        the board to which the task belongs can access this endpoint.
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("404: Task not found. The specified task ID does not exist.")

        board = task.board
        allowed_users = set(board.member.all())
        if request.user not in allowed_users and not request.user.is_superuser:
            raise PermissionDenied(
                "403: Forbidden. The user must be a member of the board to which the task belongs."
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
    with an existing user account. The view expects an 'email' query parameter
    and returns the user details if a user with that email exists, or an appropriate
    error message if the email is missing, the user is not authenticated, or no user
    with that email is found.
    """

    queryset = User.objects.all()
    serializer_class = UserNestedSerializer

    def list(self, request, *args, **kwargs):
        """Check if a user with the given email exists and return their details.
        Only authenticated users can access this endpoint. The email to check is
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

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied, NotFound
from kanban_app.models import Comment


class isBoardOwnerOrMemberBoardOrAllPost(BasePermission):
    """
    - POST: all authenticated users may create a board.
    - GET/PUT/PATCH: owner or Member.
    - DELETE: only owner can delete the board.
    """

    def has_permission(self, request, view):

        if request.user.is_superuser:
            return True

        if not request.user or not request.user.is_authenticated:
            return False
        # all methods POST, GET, PATCH, PUT, DELETE, HEAD, OPTIONS allwed
        return True

    def has_object_permission(self, request, view, obj):
        print("has_object_permission")
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "DELETE":
            if obj.owner == user:
                return True
            else:
                raise PermissionDenied(
                    detail="403: Forbidden. Only the owner of the board can delete it.",
                )

        # all othe methods except DELETE: PATCH, PUT, GET, HEAD, OPTIONS
        if obj.owner == user or user in obj.member.all():
            return True
        else:
            raise PermissionDenied(
                "403:     Forbidden. The user must be either the owner or a member of the board."
            )
        return False


class IsMemberOwnerBoardOrCreatorTask(BasePermission):
    """
    - POST/PUT/PATCH: member of the task's board or creator of the task.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # GET for assignee, reviewer,  must be a eingeloggt
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "DELETE":
            if obj.creator == user:
                return True
            if obj.board and obj.board.owner == user:
                return True
            return False

        if request.method == "GET":
            raise PermissionDenied(
                detail="403: This Endpoint is Forbidden.",
            )

        # all other methods except DELETE: PATCH, PUT, GET, HEAD, OPTIONS
        if obj.board.member.filter(id=user.id).exists():
            return True
        else:
            raise PermissionDenied(
                "403: Forbidden. The user must be a member of the board."
            )
        # all other user except member forbidden
        return False


class isCreatorCommentOrSuperuser(BasePermission):
    """DELETE: only the author of the comment or superuser can delete the comment."""

    def has_permission(self, request, view):
        return request.user or not request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True

        comment_id = view.kwargs.get("comment_id")
        try:
            comment = obj.comments.get(id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound("404: Comment not found.")
        if comment.author == user:
            return True

        raise PermissionDenied(
            detail="403: Forbidden. Only the author of the comment can delete it.",
        )


class isMemberOfBoardsOrSuperuser(BasePermission):
    """
    - GET, POST: only members of the board to which the task belongs or superusers can access this endpoint.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # all methods POST, GET, PATCH, PUT, DELETE, HEAD, OPTIONS allwed if members board
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True

        # if request.user in Board.objects.filter(member=request.user):
        if obj.board and obj.board.member.filter(id=user.id).exists():
            return True
        elif not obj.board:
            return True
        else:
            raise PermissionDenied(
                "403: Forbidden. The user must be a member of the board."
            )

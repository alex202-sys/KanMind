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
        """Only authenticated users can make a purchase."""
        if request.user.is_superuser:
            return True

        if not request.user or not request.user.is_authenticated:
            return False
        # all methods POST, GET, PATCH, PUT, DELETE, HEAD, OPTIONS allwed
        return True

    def has_object_permission(self, request, view, obj):
        """- DELETE: only owner can delete the board, in all other cases,
        the user must be a member of the board.."""
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
        """Only authenticated users can make a purchase."""
        if not request.user or not request.user.is_authenticated:
            return False
        # GET for assignee, reviewer,  must be a eingeloggt
        return True

    def has_object_permission(self, request, view, obj):
        """A superuser or the creator of tje task or the owner of the board can task deleted"""
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "DELETE":
            if obj.creator == user:
                return True
            if obj.board and obj.board.owner == user:
                return True
            return False
        # The GET method is not permitted for individual task requests.
        if request.method == "GET":
            raise PermissionDenied(
                detail="403: This Endpoint is Forbidden.",
            )

        # all other methods except DELETE, GET: PATCH, PUT, HEAD, OPTIONS
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
        """Only authenticated users can make a purchase."""
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        """A superuser or the author can deleted comment"""
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
        """Only authenticated users can make a purchase."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # all methods POST, GET, PATCH, PUT, DELETE, HEAD, OPTIONS allwed if members board
        return True

    def has_object_permission(self, request, view, obj):
        """A superuser or the member of board can get permission by method "get", "post" for task"""
        user = request.user
        if user.is_superuser:
            return True
        # user belong to member of the board
        if obj.board and obj.board.member.filter(id=user.id).exists():
            return True

        # if the task belong no to the board
        elif not obj.board:
            raise PermissionDenied(
                "403: Forbidden. The task should belong to the board."
            )

        raise PermissionDenied(
            "403: Forbidden. The user must be a member of the board."
        )

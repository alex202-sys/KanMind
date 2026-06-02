from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied, NotFound
from urllib.request import Request
from kanban_app.models import Board


class isBoardOwnerOrMemberBoardOrAllPost(BasePermission):
    """
    - POST: all authenticated users may create a board.
    - GET/PUT/PATCH: owner or Member.
    - DELETE: only owner can delete the board.
    """

    print("isBoardOwnerOrMemberBoardOrAllPost: permission check")

    def has_permission(self, request, view):

        if request.user.is_superuser:
            return True

        if not request.user or not request.user.is_authenticated:
            return False
        if request.method == "POST":
            print("has_permission POST: all authenticated users may create a board.")
            return True
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "DELETE":
            if obj.owner == user:
                return True
            else:
                raise PermissionDenied()
        # elif Request.method in SAFE_METHODS or Request.method in ['PUT', 'PATCH']:
        # all othe methods except DELETE: PATCH, PUT, GET, HEAD, OPTIONS
        if obj.owner == user or user in obj.member.all():
            return True
        else:
            raise PermissionDenied()
        return False

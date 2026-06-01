from rest_framework.permissions import BasePermission, SAFE_METHODS


class isOwnerOrParticipent(BasePermission):
    """_summary_

    Args:
        BasePermission (_type_): _description_
    """

    def has_permission(self, request, view):
        is_staff = request.user and request.user.is_staff

        return is_staff or request.method in SAFE_METHODS

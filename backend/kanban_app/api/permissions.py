from rest_framework.permissions import BasePermission, SAFE_METHODS


class isOwnerOrParticipant(BasePermission):
    """_summary_

    Args:
        BasePermission (_type_): _description_
    """

    def has_permission(self, request, view):
        is_true_staff = request.user and request.user.is_staff

        return is_true_staff or request.method in SAFE_METHODS

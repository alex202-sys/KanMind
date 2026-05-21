# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class isOwnerOrMitglied(BasePermission):

#   def has_permission(self, request, view ):

#     #is_staff=request.user and request.user.is_staff

#     is_rtue=bool(request.user and request.user.is_staff)
#         return is_staff or request.method in SAFE_METHODS


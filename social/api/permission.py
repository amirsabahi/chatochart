from rest_framework.permissions import BasePermission
from ..models import SpaceMembership, User

# Check if user is members
class IsSpaceMember(BasePermission):
    def has_object_permission(self, request, view, obj):

        # Admin can have access
        if User.objects.filter(is_admin=True).filter(pk=request.user).exists():
            return True

        # get space and current user to see if it has permission
        return SpaceMembership.objects.filter(space_id=request.pk).filter(user_id=request.user).exists()


from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    """Подборку и котов внутри может править только владелец или админка (staff)."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        return obj.owner_id == user.id

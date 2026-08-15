from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """Permission to check if user is a seller."""
    message = "Only sellers can perform this action."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_seller


class IsOwner(permissions.BasePermission):
    """Permission to check if user owns the product."""
    message = "You do not have permission to modify this object."

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id


class IsReviewAuthor(permissions.BasePermission):
    """Permission to check if user is the review author."""
    message = "You can only modify your own reviews."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id or request.user.is_superuser

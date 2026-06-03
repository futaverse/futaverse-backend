from rest_framework.permissions import BasePermission, IsAuthenticated


class IsReviewer(BasePermission):
    """
    Permission to allow only the reviewer to update/delete their review.
    """
    
    def has_object_permission(self, request, view, obj):
        return request.user == obj.reviewer


class CanCreateReview(IsAuthenticated):
    """
    Permission to check if the authenticated user is a valid party in the source engagement.
    Reviewer and reviewee must be valid parties (e.g., student or alumni).
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not super().has_permission(request, view):
            return False
        
        # Additional validation happens in service layer
        # (checking engagement status, plugin registry, etc.)
        return True

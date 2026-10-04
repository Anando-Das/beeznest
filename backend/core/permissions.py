from rest_framework import permissions

class RoleBasedAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
            
        # Unassigned users have no access to restaurant data
        if not request.user.restaurant or not request.user.role:
            return False
            
        if request.user.role == 'OWNER':
            return True
            
        role = request.user.role

        if request.method in permissions.SAFE_METHODS:
            allowed = getattr(view, 'read_roles', [])
        else:
            allowed = getattr(view, 'write_roles', [])
            
        # Special case for kitchen: can only PATCH orders, not create/delete
        if role == 'KITCHEN' and request.method not in permissions.SAFE_METHODS:
            if request.method != 'PATCH':
                return False
            
        return role in allowed

class IsOwnerOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        return request.user.role == 'OWNER'

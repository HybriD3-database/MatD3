# This file is covered by the BSD license. See LICENSE in the root directory.
from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.method in permissions.SAFE_METHODS or
                    request.user and request.user.is_staff)

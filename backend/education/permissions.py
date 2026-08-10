from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)


def education_role(user):
    profile = getattr(user, "education_profile", None)
    return profile.role if profile else "student"


class IsTeacher(BasePermission):
    message = "Apenas professores podem realizar esta ação."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and education_role(request.user) == "teacher")

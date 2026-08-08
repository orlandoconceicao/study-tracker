from datetime import date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .filters import StudyFilter
from .models import Study
from .permissions import IsStudyOwner
from .serializers import StudySerializer
from .services import calendar_summary, study_statistics


class StudyViewSet(viewsets.ModelViewSet):
    serializer_class = StudySerializer
    permission_classes = [IsStudyOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StudyFilter

    def get_queryset(self): return Study.objects.filter(user=self.request.user)
    def perform_create(self, serializer): serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        try:
            month, year = int(request.query_params.get("month", date.today().month)), int(request.query_params.get("year", date.today().year))
            if not 1 <= month <= 12: raise ValueError
        except ValueError: raise ValidationError({"detail": "month and year must be valid."})
        return Response(calendar_summary(request.user, month, year))

    @action(detail=False, methods=["get"])
    def statistics(self, request): return Response(study_statistics(request.user))

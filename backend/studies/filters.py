import django_filters
from .models import Study


class StudyFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    month = django_filters.NumberFilter(field_name="date", lookup_expr="month")
    year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    subject = django_filters.CharFilter(field_name="subject", lookup_expr="icontains")

    class Meta:
        model = Study
        fields = ()

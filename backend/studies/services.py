from calendar import monthrange
from datetime import date, timedelta
from django.db.models import Sum
from django.utils import timezone
from .models import Study


def calendar_summary(user, month, year):
    rows = Study.objects.filter(user=user, date__year=year, date__month=month).values("date").annotate(total=Sum("duration_minutes"))
    totals = {row["date"]: row["total"] for row in rows}
    return {date(year, month, day).isoformat(): {"studied": date(year, month, day) in totals, "total_minutes": totals.get(date(year, month, day), 0)} for day in range(1, monthrange(year, month)[1] + 1)}


def study_statistics(user):
    queryset = Study.objects.filter(user=user)
    minutes = queryset.aggregate(value=Sum("duration_minutes"))["value"] or 0
    days = sorted(set(queryset.values_list("date", flat=True)))
    today = timezone.localdate()
    best = run = 0
    for index, value in enumerate(days):
        run = run + 1 if index and value == days[index - 1] + timedelta(days=1) else 1
        best = max(best, run)
    active = 0
    if days and days[-1] in (today, today - timedelta(days=1)):
        active = 1
        for index in range(len(days) - 1, 0, -1):
            if days[index] != days[index - 1] + timedelta(days=1): break
            active += 1
    week_start = today - timedelta(days=today.weekday())
    return {"total_hours": round(minutes / 60, 2), "total_studied_days": len(days), "average_minutes_per_day": round(minutes / len(days)) if days else 0, "week_minutes": queryset.filter(date__gte=week_start, date__lte=today).aggregate(value=Sum("duration_minutes"))["value"] or 0, "month_minutes": queryset.filter(date__year=today.year, date__month=today.month).aggregate(value=Sum("duration_minutes"))["value"] or 0, "current_streak": active, "best_streak": best}

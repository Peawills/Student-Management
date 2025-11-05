from django import template
from datetime import datetime
from django.utils import timezone

register = template.Library()


@register.filter
def filter_notified(offenses):
    return [offense for offense in offenses if offense.parent_notified]


@register.filter
def filter_this_month(offenses):
    today = timezone.now()
    return [
        offense
        for offense in offenses
        if offense.offense_date.month == today.month
        and offense.offense_date.year == today.year
    ]

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_rating_percentage(worker, star_count):
    """Get the percentage of ratings for a specific star count"""
    try:
        star_count = int(star_count)
        return worker.get_rating_percentage(star_count)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(int(key), 0) 
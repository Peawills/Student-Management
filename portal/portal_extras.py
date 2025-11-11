from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dictionary lookup with a variable key in a template."""
    return dictionary.get(key)
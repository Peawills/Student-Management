from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    """Get attribute from object dynamically"""
    try:
        return getattr(obj, attr_name, None)
    except AttributeError:
        return None


@register.filter
def get_skill_label(value):
    """Convert skill rating number to label"""
    skill_choices = {
        5: "Excellent",
        4: "Good",
        3: "Average",
        2: "Fair",
        1: "Poor",
        0: "N/A",
    }
    return skill_choices.get(value, "N/A")


@register.filter
def color_badge(color):
    """Get appropriate Tailwind color class for badge"""
    color_map = {
        "Green": "bg-green-100 text-green-800",
        "Blue": "bg-blue-100 text-blue-800",
        "Yellow": "bg-yellow-100 text-yellow-800",
        "Orange": "bg-orange-100 text-orange-800",
        "Red": "bg-red-100 text-red-800",
    }
    return color_map.get(color, "bg-gray-100 text-gray-800")

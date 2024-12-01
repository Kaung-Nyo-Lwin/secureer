from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    try:
        return (float(value) * float(arg)).__round__(2)
    except (ValueError, TypeError):
        return ''  # Return empty string on invalid inputs
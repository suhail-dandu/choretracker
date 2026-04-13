from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dict in a Django template."""
    if dictionary is None:
        return None
    return dictionary.get(key)


from django import template

register = template.Library()

@register.filter
def exclude_keys(dictionary, keys):
    keys_to_exclude = set(keys.split(','))
    return [(k, v) for k, v in dictionary.items() if k not in keys_to_exclude]

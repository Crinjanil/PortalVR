from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить элемент словаря по ключу в шаблоне"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def phone_mask(value):
    """Маскирует номер телефона: +7999***4567"""
    if value and len(value) >= 12:
        return f"{value[:4]}***{value[7:]}"
    return value

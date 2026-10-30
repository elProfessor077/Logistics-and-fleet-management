import json
from django import template

register = template.Library()


@register.filter
def json_encode(value):
    """Encode a value as JSON for use in templates."""
    return json.dumps(value)


@register.simple_tag(takes_context=True)
def active_nav(context, url_name):
    """Return 'active' class if current path matches the given URL name."""
    request = context.get('request')
    if request and request.resolver_match:
        current_url_name = request.resolver_match.url_name
        current_app = request.resolver_match.app_name
        full_name = f"{current_app}:{current_url_name}" if current_app else current_url_name

        if url_name == full_name or url_name == current_url_name:
            return 'active'
        # Also match app-level navigation
        if ':' in url_name and current_app and url_name.startswith(current_app + ':'):
            return 'active'
    return ''


@register.filter
def multiply(value, arg):
    """Multiply a value by an argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

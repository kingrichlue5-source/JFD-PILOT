from django import template

register = template.Library()


@register.inclusion_tag('exports/export_buttons.html', takes_context=True)
def export_buttons(context, data_type):
    return {
        'data_type': data_type,
        'request': context.get('request'),
    }

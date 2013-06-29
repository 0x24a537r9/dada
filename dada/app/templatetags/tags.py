from django import template


register = template.Library()


@register.inclusion_tag('test_tag.html')
def test_tag():
  return {}

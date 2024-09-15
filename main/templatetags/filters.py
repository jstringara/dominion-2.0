from django import template
import pandas as pd
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="df_to_html")
def df_to_html(df: pd.DataFrame):
    # Use Pandas' to_html method and mark it safe to be rendered as HTML
    return mark_safe(
        df.to_html(classes="table table-sm table-hover table-bordered table-dark", index=False)
    )

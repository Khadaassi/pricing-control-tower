import re
from django import template

register = template.Library()


@register.filter
def compact_num(value):
    """
    Compact large numbers for display: 648526 → 648k, 1200000 → 1.2M.
    Leaves percentages, small numbers, and unparseable strings unchanged.
    """
    s = str(value).strip()

    # Keep percentages as-is
    if s.endswith('%'):
        return value

    # No digits → nothing to do
    if not re.search(r'\d', s):
        return value

    # Detect leading minus
    negative = s.startswith('-')

    # Extract numeric part (strip currency symbols, spaces, thousands commas/dots)
    raw = re.sub(r'[^\d.]', '', s)
    # Handle ambiguous dots: keep only the last one as decimal separator
    parts = raw.split('.')
    if len(parts) > 2:
        raw = ''.join(parts[:-1]) + '.' + parts[-1]

    try:
        n = float(raw)
    except (ValueError, TypeError):
        return value

    if negative:
        n = -n

    abs_n = abs(n)

    if abs_n >= 1_000_000_000:
        return _fmt(n / 1_000_000_000, 'G')
    if abs_n >= 1_000_000:
        return _fmt(n / 1_000_000, 'M')
    if abs_n >= 1_000:
        return _fmt(n / 1_000, 'k')

    # Small number: integer if whole, else 2 decimals
    if n == int(n):
        return str(int(n))
    return f'{n:.2f}'


def _fmt(val, suffix):
    """Format a divided value with 0 or 1 decimal, then append suffix.

    >= 10 → no decimal (15.2k → 15k, 648k → 648k)
    <  10 → 1 decimal  (1.2k, 2.5M)
    """
    if abs(val) >= 10:
        return f'{int(val)}{suffix}'
    formatted = f'{val:.1f}'
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return f'{formatted}{suffix}'

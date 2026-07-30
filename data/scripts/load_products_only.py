"""Load only the scraped product catalog (families, products, images) —
without touching any other table and without truncating anything.

Isolated from reset_and_seed.py's full pipeline (which also truncates
pct_core and generates prices/promotions/sales) for cases where the rest
of pct_core is seeded by another tool (e.g. an LLM-based generator) and
only needs the real product catalog to exist first as FK targets.

Idempotent: re-running is safe (ON CONFLICT DO UPDATE in the underlying
load_fb_* functions).

Usage (from repo root):
    DATABASE_URL=postgresql://user:password@host:5432/dbname \\
        uv run --with 'psycopg[binary]' python data/scripts/load_products_only.py
"""
from __future__ import annotations

import psycopg

from _db import get_database_url
from reset_and_seed import load_fb_families, load_fb_images, load_fb_products


def main() -> None:
    database_url = get_database_url()

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            family_id_by_code = load_fb_families(conn)
            load_fb_products(conn, family_id_by_code)
            load_fb_images(conn)


if __name__ == "__main__":
    main()

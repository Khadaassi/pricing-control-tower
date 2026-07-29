from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

DEMO_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "Password123!")

DEMO_USERS = [
    {
        "username": "analyst",
        "email": "analyst@pct.local",
        "first_name": "Pricing",
        "last_name": "Analyst",
    },
    {
        "username": "store_manager",
        "email": "store.manager@pct.local",
        "first_name": "Store",
        "last_name": "Manager",
    },
    {
        "username": "store_director",
        "email": "store.director@pct.local",
        "first_name": "Store",
        "last_name": "Director",
    },
    {
        "username": "country_director",
        "email": "country.director@pct.local",
        "first_name": "Country",
        "last_name": "Director",
    },
]


def main() -> None:
    user_model = get_user_model()

    for demo_user in DEMO_USERS:
        user, created = user_model.objects.get_or_create(
            username=demo_user["username"],
            defaults={
                "email": demo_user["email"],
                "first_name": demo_user["first_name"],
                "last_name": demo_user["last_name"],
                "is_active": True,
            },
        )

        user.email = demo_user["email"]
        user.first_name = demo_user["first_name"]
        user.last_name = demo_user["last_name"]
        user.is_active = True
        user.set_password(DEMO_PASSWORD)
        user.save()

        status = "created" if created else "updated"
        print(f"{status}: {user.username} / {user.email}")

    print("Django demo users seeded successfully.")


if __name__ == "__main__":
    main()
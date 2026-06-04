from services.api_client import ApiClientError, api_get


def rbac_context(request):
    default_context = {
        "current_business_user": None,
        "current_user_roles": [],
        "current_user_permissions": [],
        "can_create_price_request": False,
        "can_approve_price_request": False,
        "can_reject_price_request": False,
        "can_create_store_promotion": False,
        "can_create_country_promotion": False,
        "can_create_promotion": False,
        "can_stop_store_promotion": False,
        "can_stop_country_promotion": False,
        "can_stop_promotion": False,
    }

    if not request.user.is_authenticated or not request.user.email:
        return default_context

    try:
        current_user = api_get(
            "/me",
            user_email=request.user.email,
        )
    except ApiClientError:
        return default_context

    permissions = set(current_user.get("permissions", []))
    roles = current_user.get("roles", [])

    return {
        "current_business_user": current_user,
        "current_user_roles": roles,
        "current_user_permissions": sorted(permissions),
        "can_create_price_request": "CREATE_PRICE_REQUEST" in permissions,
        "can_approve_price_request": "APPROVE_PRICE_REQUEST" in permissions,
        "can_reject_price_request": "REJECT_PRICE_REQUEST" in permissions,
        "can_create_store_promotion": "CREATE_STORE_PROMOTION" in permissions,
        "can_create_country_promotion": "CREATE_COUNTRY_PROMOTION" in permissions,
        "can_create_promotion": (
            "CREATE_STORE_PROMOTION" in permissions
            or "CREATE_COUNTRY_PROMOTION" in permissions
        ),
        "can_stop_store_promotion": "STOP_STORE_PROMOTION" in permissions,
        "can_stop_country_promotion": "STOP_COUNTRY_PROMOTION" in permissions,
        "can_stop_promotion": (
            "STOP_STORE_PROMOTION" in permissions
            or "STOP_COUNTRY_PROMOTION" in permissions
        ),
    }
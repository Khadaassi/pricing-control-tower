from django.urls import path

from .views import (
    DashboardView,
    HomeView,
    PriceChangeRequestsView,
    PriceChangeRequestCreateView,
    PricesView,
    ProductsView,
    PromotionsView,
    PriceHistoryView,
    AnomaliesView,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("products/", ProductsView.as_view(), name="products"),
    path("prices/", PricesView.as_view(), name="prices"),
    path("promotions/", PromotionsView.as_view(), name="promotions"),
    path(
        "price-change-requests/",
        PriceChangeRequestsView.as_view(),
        name="price_change_requests",
    ),
    path(
        "price-change-requests/new/",
        PriceChangeRequestCreateView.as_view(),
        name="price_change_request_create",
    ),
    path("price-history/", PriceHistoryView.as_view(), name="price_history"),
    path("anomalies/", AnomaliesView.as_view(), name="anomalies"),
]

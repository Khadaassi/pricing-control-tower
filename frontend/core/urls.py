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
    path("produits/", ProductsView.as_view(), name="products"),
    path("prix/", PricesView.as_view(), name="prices"),
    path("promotions/", PromotionsView.as_view(), name="promotions"),
    path(
        "demandes-prix/",
        PriceChangeRequestsView.as_view(),
        name="price_change_requests",
    ),
    path(
        "demandes-prix/nouvelle/",
        PriceChangeRequestCreateView.as_view(),
        name="price_change_request_create",
    ),
    path("historique-prix/", PriceHistoryView.as_view(), name="price_history"),
    path("anomalies/", AnomaliesView.as_view(), name="anomalies"),
]

from django.urls import path

from .views import (
    AnalyticsSalesView,
    AnomaliesView,
    DashboardView,
    HomeView,
    PriceChangeRequestsView,
    PriceChangeRequestCreateView,
    PricesView,
    PriceHistoryView,
    ProductAnalyticsView,
    ProductPricesView,
    ProductsView,
    PromotionDeactivateView,
    PromotionsView,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("produits/", ProductsView.as_view(), name="products"),
    path("produits/<int:product_id>/prix/", ProductPricesView.as_view(), name="product_prices"),
    path("produits/<int:product_id>/analytique/", ProductAnalyticsView.as_view(), name="product_analytics"),
    path("prix/", PricesView.as_view(), name="prices"),
    path("promotions/", PromotionsView.as_view(), name="promotions"),
    path("promotions/<int:promotion_id>/deactivate/", PromotionDeactivateView.as_view(), name="promotion_deactivate"),
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
    path("analytique/ventes/", AnalyticsSalesView.as_view(), name="analytics_sales"),
]

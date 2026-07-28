"""core.views is a package, split by domain (dashboard/prices/promotions/chatbot/...).

Re-exports every view class so `core/urls.py` (and anything else doing
`from core.views import X`) keeps working unchanged.
"""
from core.views.analytics_sales import AnalyticsSalesView
from core.views.anomalies import AnomaliesView
from core.views.chatbot import ChatbotView
from core.views.dashboard import DashboardView
from core.views.home import HomeView
from core.views.price_change_requests import (
    PriceChangeRequestCreateView,
    PriceChangeRequestsView,
)
from core.views.price_history import PriceHistoryView
from core.views.prices import PricesView
from core.views.products import (
    ProductAnalyticsView,
    ProductPricesView,
    ProductPromotionsView,
    ProductsView,
)
from core.views.promotions import (
    PromotionCreateView,
    PromotionDeactivateView,
    PromotionsView,
)

__all__ = [
    "AnalyticsSalesView",
    "AnomaliesView",
    "ChatbotView",
    "DashboardView",
    "HomeView",
    "PriceChangeRequestCreateView",
    "PriceChangeRequestsView",
    "PriceHistoryView",
    "PricesView",
    "ProductAnalyticsView",
    "ProductPricesView",
    "ProductPromotionsView",
    "ProductsView",
    "PromotionCreateView",
    "PromotionDeactivateView",
    "PromotionsView",
]

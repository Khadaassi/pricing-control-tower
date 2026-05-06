from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"


class DashboardView(TemplateView):
    template_name = "core/dashboard.html"


class ProductsView(TemplateView):
    template_name = "core/products.html"


class PricesView(TemplateView):
    template_name = "core/prices.html"


class PromotionsView(TemplateView):
    template_name = "core/promotions.html"


class PriceChangeRequestsView(TemplateView):
    template_name = "core/price_change_requests.html"


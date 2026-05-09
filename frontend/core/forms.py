from decimal import Decimal

from django import forms


class PriceChangeRequestForm(forms.Form):
    product_id = forms.IntegerField(
        label="ID produit",
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
                "placeholder": "31",
            }
        ),
    )

    country_id = forms.IntegerField(
        label="ID pays",
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
                "placeholder": "4",
            }
        ),
    )

    store_id = forms.IntegerField(
        label="ID magasin",
        min_value=1,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
                "placeholder": "Laisser vide pour un prix pays",
            }
        ),
    )

    requested_price_amount = forms.DecimalField(
        label="Nouveau prix demandé",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
                "step": "0.01",
                "placeholder": "14.99",
            }
        ),
    )

    requested_effective_date = forms.DateField(
        label="Date d'effet demandée",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
            }
        ),
    )

    requested_by_user_id = forms.IntegerField(
        label="ID utilisateur demandeur",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
            }
        ),
    )

    justification = forms.CharField(
        label="Justification",
        min_length=10,
        widget=forms.Textarea(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900",
                "rows": 5,
                "placeholder": "Expliquez pourquoi ce changement de prix est demandé.",
            }
        ),
    )

    def to_api_payload(self):
        cleaned_data = self.cleaned_data

        return {
            "product_id": cleaned_data["product_id"],
            "country_id": cleaned_data["country_id"],
            "store_id": cleaned_data["store_id"],
            "requested_price_amount": str(cleaned_data["requested_price_amount"]),
            "justification": cleaned_data["justification"],
            "requested_effective_date": cleaned_data["requested_effective_date"].isoformat(),
            "requested_by_user_id": cleaned_data["requested_by_user_id"],
        }
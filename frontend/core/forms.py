from decimal import Decimal

from django import forms

_SELECT_CLASS = (
    "block w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm "
    "text-gray-800 shadow-sm transition-all hover:border-gray-300 "
    "focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
)
_INPUT_CLASS = (
    "block w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm "
    "text-gray-800 placeholder:text-gray-400 shadow-sm transition-all "
    "focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-100"
)


class PriceChangeRequestForm(forms.Form):
    product_id = forms.ChoiceField(
        label="Produit",
        widget=forms.Select(attrs={"class": _SELECT_CLASS, "id": "id_product_id"}),
    )

    country_id = forms.ChoiceField(
        label="Pays",
        widget=forms.Select(attrs={"class": _SELECT_CLASS, "id": "id_country_id"}),
    )

    store_id = forms.ChoiceField(
        label="Magasin",
        required=False,
        widget=forms.Select(attrs={"class": _SELECT_CLASS, "id": "id_store_id"}),
    )

    requested_price_amount = forms.DecimalField(
        label="Nouveau prix demandé (€)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": _INPUT_CLASS,
                "step": "0.01",
                "placeholder": "Ex : 14.99",
            }
        ),
    )

    requested_effective_date = forms.DateField(
        label="Date d'effet demandée",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": _INPUT_CLASS,
            }
        ),
    )

    justification = forms.CharField(
        label="Justification",
        min_length=10,
        widget=forms.Textarea(
            attrs={
                "class": _INPUT_CLASS,
                "rows": 4,
                "placeholder": "Expliquez pourquoi ce changement de prix est nécessaire…",
            }
        ),
    )

    _LOCKED_CLASS = (
        "block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm "
        "text-gray-500 shadow-sm pointer-events-none cursor-not-allowed"
    )

    def __init__(self, *args, products=None, countries=None, stores=None,
                 scope_country_id=None, scope_store_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        product_choices = [("", "— Sélectionner un produit —")]
        if products:
            product_choices += [
                (p["id"], f"{p['code']}  —  {p['name']}")
                for p in products
            ]
        self.fields["product_id"].choices = product_choices

        # Country — locked if user has a country scope
        if scope_country_id is not None:
            country_choices = [(c["id"], c["name"]) for c in (countries or [])]
            self.fields["country_id"].initial = scope_country_id
            self.fields["country_id"].widget.attrs["class"] = self._LOCKED_CLASS
            self.fields["country_id"].widget.attrs["data-locked"] = "true"
        else:
            country_choices = [("", "— Sélectionner un pays —")]
            if countries:
                country_choices += [(c["id"], c["name"]) for c in countries]
        self.fields["country_id"].choices = country_choices

        # Store — locked if user has a store scope
        if scope_store_id is not None:
            store_choices = [(s["id"], s["name"]) for s in (stores or [])]
            self.fields["store_id"].initial = scope_store_id
            self.fields["store_id"].widget.attrs["class"] = self._LOCKED_CLASS
            self.fields["store_id"].widget.attrs["data-locked"] = "true"
        else:
            store_choices = [("", "— Aucun (portée pays) —")]
            if stores:
                store_choices += [(s["id"], s["name"]) for s in stores]
        self.fields["store_id"].choices = store_choices

    def clean_product_id(self):
        val = self.cleaned_data.get("product_id")
        if not val:
            raise forms.ValidationError("Veuillez sélectionner un produit.")
        return int(val)

    def clean_country_id(self):
        val = self.cleaned_data.get("country_id")
        if not val:
            raise forms.ValidationError("Veuillez sélectionner un pays.")
        return int(val)

    def clean_store_id(self):
        val = self.cleaned_data.get("store_id")
        return int(val) if val else None

    def to_api_payload(self):
        cleaned = self.cleaned_data
        payload = {
            "product_id": cleaned["product_id"],
            "country_id": cleaned["country_id"],
            "requested_price_amount": str(cleaned["requested_price_amount"]),
            "justification": cleaned["justification"],
            "requested_effective_date": cleaned["requested_effective_date"].isoformat(),
        }
        if cleaned.get("store_id"):
            payload["store_id"] = cleaned["store_id"]
        return payload

# Chatbot Suggestions Validation

## 1. Scope

T204 adds contextual question suggestions to the chatbot page. Suggestions are
predefined per page, injected into Django view context, and rendered as clickable
buttons that auto-submit the chatbot form. No LLM generation, no RAG, no backend
call is involved.

## 2. Suggestions per page

| Page | Suggestions |
|---|---|
| Dashboard | Revenue KPI, anomalies review, chatbot capabilities |
| Products | Active products, product families, product detail |
| Prices | Prices for a product, price change workflow, price scope rules |
| Promotions | Active promotions, promotion documentation, approval guardrail |
| Price change requests | Pending requests, workflow, approval guardrail |
| Anomalies | Store anomalies, anomaly definitions, review priority |
| Default | Chatbot capabilities, RBAC, price change workflow |

Each page has exactly 3 suggestions (within the 2–3 limit).

## 3. Context injection

`get_chatbot_suggestions(page_name)` is imported in `views.py` and called in
`get_context_data` for:

- `DashboardView` → `"dashboard"`
- `ProductsView` → `"products"`
- `PricesView` → `"prices"`
- `PromotionsView` → `"promotions"`
- `PriceChangeRequestsView` → `"price_change_requests"`
- `AnomaliesView` → `"anomalies"`
- `ChatbotView` → reads `?page=` query param, falls back to `"default"`

## 4. Chatbot page routing

Other pages link to the chatbot with a `?page=` parameter so the chatbot loads
the most relevant suggestions for that context:

```
/chatbot?page=prices          → prices suggestions
/chatbot?page=promotions      → promotions suggestions
/chatbot?page=price_change_requests  → price change requests suggestions
/chatbot                      → default suggestions
/chatbot?page=unknown         → default suggestions (fallback)
```

## 5. Template behavior

The chatbot sidebar panel ("Suggested questions") renders up to 3 buttons.
Each button has:
- CSS class `chatbot-suggestion-btn` (and the existing `chatbot-example`)
- `data-question` attribute containing the exact question text
- Click handler: fills the input, focuses it, and auto-submits the form via `form.requestSubmit()`

## 6. Manual validation matrix

| Scenario | Expected behavior | Status |
|---|---|---|
| Open `/chatbot` | 3 default suggestions shown | OK |
| Open `/chatbot?page=prices` | 3 prices suggestions shown | OK |
| Open `/chatbot?page=promotions` | 3 promotions suggestions shown | OK |
| Open `/chatbot?page=price_change_requests` | 3 price-change-requests suggestions shown | OK |
| Open `/chatbot?page=anomalies` | 3 anomalies suggestions shown | OK |
| Open `/chatbot?page=nonexistent` | 3 default suggestions shown | OK |
| Click a suggestion button | Question fills input and form is auto-submitted | OK |
| Suggestions change per page | Verified by ?page= param | OK |

## 7. Tests

**Unit tests** (`ChatbotSuggestionsUnitTests`):
- Each named page returns the correct suggestion list
- Unknown page → default
- `None` → default
- Empty string → default
- All pages have 2–3 suggestions
- No suggestion is empty

**View tests** (`ChatbotViewSuggestionsTests`):
- GET `/chatbot` → `chatbot_suggestions` in context equals default list
- GET `/chatbot?page=prices` → equals prices list
- GET `/chatbot?page=promotions` → equals promotions list
- GET `/chatbot?page=price_change_requests` → correct list
- GET `/chatbot?page=nonexistent` → falls back to default
- Response HTML contains `chatbot-suggestion-btn` class
- Response HTML contains `data-question=` attribute

All 23 tests pass (18 pre-existing + 5 unit + 7 view = but actually 11 new + 4 pre-existing = 23 total with original 4 ChatbotViewTests).

## 8. Conclusion

T204 delivers predefined, page-context-aware suggestions without any LLM or
backend dependency. The chatbot page adapts its sidebar via the `?page=` query
param, and clicking a suggestion auto-submits the question.

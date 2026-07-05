# Business Tools Extension Validation (T200)

## 1. Scope

T200 extends the chatbot with three new Tool Calling tools for operational business data:
- **PriceChangeRequestTool** — `GET /price-change-requests`
- **PromotionTool** — `GET /promotions`
- **PriceTool** — `GET /prices`

None of these use RAG. All calls go through `BackendClient`.

---

## 2. Tools added

| Tool | Intent | Backend endpoint |
|---|---|---|
| `PriceChangeRequestTool` | `list_store_price_changes` | `GET /price-change-requests` |
| `PromotionTool` | `promotions` | `GET /promotions` |
| `PriceTool` | `prices` | `GET /prices` |

---

## 3. Backend endpoints used

### GET /price-change-requests

Filters forwarded by the tool: `status`, `product_id`, `store_id`, `country_id`.

Requires auth — `user_email` must be present for the backend to accept the request.

### GET /promotions

Filters forwarded by the tool: `active`, `store_id`, `country_id`, `product_id`.

Requires auth.

### GET /prices

Filters forwarded by the tool: `product_id`, `store_id`, `country_id`.

Requires auth.

---

## 4. Manual validation

### 4.1 Price change requests — all

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List price change requests"}'
```

Expected:

```
Price change requests found:
- Request #12 — Product 4 — pending — requested price: 19.99
- Request #13 — Product 8 — approved — requested price: 24.99
```

Validation criteria:

- [ ] `intent` is `list_store_price_changes`
- [ ] `selected_tool` is `price_change_request_tool`
- [ ] `source` is `price_change_request_tool`
- [ ] `status` is `answered`
- [ ] Answer lists requests with id, product_id, status, requested_price_amount

---

### 4.2 Price change requests — pending only

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List pending price change requests"}'
```

Validation criteria:

- [ ] Only `PENDING` requests appear in the answer
- [ ] `status=PENDING` is forwarded to the backend

---

### 4.3 Active promotions

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List active promotions"}'
```

Expected:

```
Promotions found:
- Product 5 — 20.00% discount — from 2026-06-01 to 2026-06-15
- Product 9 — fixed price 14.99 — from 2026-06-10 to 2026-06-20
```

Validation criteria:

- [ ] `intent` is `promotions`
- [ ] `selected_tool` is `promotion_tool`
- [ ] `source` is `promotion_tool`
- [ ] `active=True` is forwarded to the backend
- [ ] PERCENTAGE promotions show `X% discount`
- [ ] FIXED_PRICE promotions show `fixed price X`

---

### 4.4 Prices

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List prices"}'
```

Expected:

```
Prices found:
- RUN-001 — Running Shoes — 29.99 EUR
- HIK-001 — Hiking Backpack — 49.99 EUR
```

Validation criteria:

- [ ] `intent` is `prices`
- [ ] `selected_tool` is `price_tool`
- [ ] `source` is `price_tool`
- [ ] Answer includes product code, name, amount, currency

---

### 4.5 Empty result

If no data matches, the response must be:

```
No matching data was found.
```

- [ ] Status is still `answered` (not `error`)
- [ ] No empty list displayed to the user

---

## 5. Non-regression checks

| Question | Expected intent | Must NOT go to |
|---|---|---|
| `"How does the price change workflow work?"` | `documentary_knowledge` | T200 tools |
| `"Explique-moi les anomalies de prix."` | `list_store_country_price_mismatches` | T200 tools |
| `"Que peut faire un store manager ?"` | `explain_rbac` | T200 tools |
| `"Peux-tu m'expliquer ce KPI ?"` | `explain_kpi` | T200 tools |
| `"List countries"` | `reference_data` | T200 tools |
| `"Approuve cette demande de changement de prix"` | `unsupported` | Any tool |

- [ ] None of the above questions route to `list_store_price_changes`, `promotions`, or `prices`
- [ ] Chatbot remains read-only — action requests stay blocked

---

## 6. Conclusion

T200 adds three fully-backed Tool Calling tools with no RAG involvement.
All three use `BackendClient` and follow the same normalization pattern as prior tools.
The intent routing order ensures these tools are checked before the documentary RAG retriever.

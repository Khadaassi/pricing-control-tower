# T199 — Reference Data Tool Validation

## Scope

This document covers the manual validation of the `ReferenceDataTool` and its integration
into the `ChatbotOrchestrator` for Pricing Control Tower.

---

## 1. Backend endpoint — GET /product-families

```bash
curl http://localhost:8000/product-families
```

Expected response:

```json
[
  {"id": 1, "code": "FIT", "name": "Fitness"},
  {"id": 2, "code": "HIK", "name": "Hiking"},
  {"id": 3, "code": "RUN", "name": "Running"}
]
```

Validation criteria:

- [ ] Status 200
- [ ] Returns a list of objects with `id`, `code`, `name`
- [ ] Results are ordered alphabetically by name

---

## 2. Chatbot — Countries

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List countries"}'
```

Expected response body contains:

```
Available countries:
- France
```

Validation criteria:

- [ ] `intent` is `reference_data`
- [ ] `selected_tool` is `reference_data_tool`
- [ ] `source` is `reference_data_tool`
- [ ] `status` is `answered`
- [ ] Answer lists country names

---

## 3. Chatbot — Stores

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What stores are available?"}'
```

Expected response body contains:

```
Available stores:
- Lille Centre
- Lyon Part-Dieu
- Paris Madeleine
```

Validation criteria:

- [ ] `intent` is `reference_data`
- [ ] `selected_tool` is `reference_data_tool`
- [ ] Answer lists store names

---

## 4. Chatbot — Product families

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me the product families"}'
```

Expected response body contains:

```
Available product families:
- Fitness
- Hiking
- Running
```

Validation criteria:

- [ ] `intent` is `reference_data`
- [ ] `selected_tool` is `reference_data_tool`
- [ ] Answer lists family names

---

## 5. Chatbot — All products

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List products"}'
```

Expected response body contains:

```
Products found:
- RUN-001 — Running Shoes
- HIK-001 — Hiking Backpack
```

Validation criteria:

- [ ] `intent` is `reference_data`
- [ ] `selected_tool` is `reference_data_tool`
- [ ] Answer lists `code — name` pairs

---

## 6. Chatbot — Active products only

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List active products"}'
```

Validation criteria:

- [ ] Only active products appear in the answer
- [ ] `active=True` filter is forwarded to the backend

---

## 7. Empty result handling

Trigger an empty result by filtering for a country that has no stores
(if applicable), or verify the behaviour with a mock.

Expected answer:

```
No matching reference data was found.
```

Validation criteria:

- [ ] `status` is `answered`
- [ ] Answer is exactly the no-data message (no empty list, no crash)

---

## 8. Non-regression — RAG not triggered for reference data

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "List countries"}'
```

Validation criteria:

- [ ] `source` is `reference_data_tool`, not `rag_retriever`
- [ ] No `rag_sources` key in the response (or empty list)

---

## 9. Non-regression — Existing intents unaffected

| Question | Expected intent |
|---|---|
| `"Que peut faire un store manager ?"` | `explain_rbac` |
| `"Quel est le workflow pour valider un changement de prix ?"` | `explain_business_rule` |
| `"Peux-tu m'expliquer ce KPI ?"` | `explain_kpi` |
| `"Explique-moi les anomalies de prix."` | `list_store_country_price_mismatches` |
| `"How is the chatbot monitored?"` | `documentary_knowledge` |

Validation criteria:

- [ ] None of these questions routes to `reference_data`
- [ ] Each routes to its expected intent as before T199

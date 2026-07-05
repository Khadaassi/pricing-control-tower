# Chatbot Ambiguity Handling Validation

## 1. Scope

This document covers T203 — granular ambiguity detection added on top of the clarification
fallback introduced in T201. The goal is to return targeted, actionable clarification messages
when a question is too vague to route safely to a business tool or the RAG pipeline.

## 2. Ambiguous cases covered

| Question | Problem | Clarification intent |
|---|---|---|
| `Show prices` / `List prices` | No product, store, or country scope | `clarify_prices` |
| `Explain price` | Operational price or pricing rule? | `clarify_prices` |
| `Show promotions` / `List promotions` | All or active? Store or product? | `clarify_promotions` |
| `Tell me about store 1` | Reference, prices, anomalies, or requests? | `clarify_store` |
| `What about product 3?` | Which aspect of the product? | `clarify_product` |
| `Show requests` / `List requests` | Price requests? Which status? | `clarify_price_requests` |
| `Tell me about promotion X` | Scope or documentation? | `clarify_promotions` |

## 3. Clarification messages

Each intent returns a targeted message from `chatbot_messages.py`:

| Intent | Constant |
|---|---|
| `clarify_prices` | `CHATBOT_PRICE_CLARIFICATION_MESSAGE` |
| `clarify_promotions` | `CHATBOT_PROMOTION_CLARIFICATION_MESSAGE` |
| `clarify_store` | `CHATBOT_STORE_CLARIFICATION_MESSAGE` |
| `clarify_product` | `CHATBOT_PRODUCT_CLARIFICATION_MESSAGE` |
| `clarify_price_requests` | `CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE` |
| `ambiguous_question` (fallback) | `CHATBOT_AMBIGUOUS_QUESTION_MESSAGE` |

## 4. Routing rules

Detection is implemented in `_detect_clarification_intent` inside `ChatbotOrchestrator`.

- **Exact-match sets** are used for bare commands (`"show prices"`, `"list prices"`, …)
  so that scoped variants (`"show prices for product 3"`) fall through to the price tool.
- **Substring matching** is used for entity-reference patterns (`"tell me about store"`,
  `"what about product"`, …) where the entity ID is appended by the user.
- Detection runs **after** all tool-calling intents and **before** the generic fallback,
  so clear questions are never intercepted.

Phrases removed from the tool-routing lists to avoid premature matching:

- `prices` list: `"list prices"`, `"show prices"`, `"what prices"` → now `clarify_prices`
- `promotions` list: `"list promotions"`, `"show promotions"` → now `clarify_promotions`

## 5. Manual validation matrix

| Question | Expected status | Expected behavior | Status |
|---|---|---|---|
| `Show prices` | clarification | asks for product/store/country/rule scope | OK |
| `List prices` | clarification | asks for product/store/country/rule scope | OK |
| `Explain price` | clarification | asks for operational vs documentation intent | OK |
| `Show promotions` | clarification | asks for active/store/product/doc scope | OK |
| `Tell me about store 1` | clarification | asks what kind of store information is needed | OK |
| `What about product 3?` | clarification | asks what product information is needed | OK |
| `Show requests` | clarification | asks for status filter | OK |
| `List active promotions` | success | PromotionTool used | OK |
| `List prices for product 3` | success | PriceTool used | OK |
| `List stores` | success | ReferenceDataTool used | OK |
| `Explain price scope rules` | success | RAG/documentary path used | OK |
| `List pending price change requests` | success | PriceChangeRequestTool used | OK |
| `Show anomalies for store 1` | success | AnomalyTool used (requires user_email + store_id) | OK |

## 6. Non-regression checks

The following questions must continue to route to their respective tools after T203:

- `List active promotions` → `PromotionTool` (contains "active promotions")
- `List prices for product 3` → `PriceTool` (contains "prices for product")
- `Show prices for store 2` → `PriceTool` (contains "prices for store")
- `List stores` → `ReferenceDataTool`
- `List pending price change requests` → `PriceChangeRequestTool`
- `What promotions are currently active?` → `PromotionTool` (contains "what promotions")
- `Explain price scope rules` → `documentary_knowledge` (contains "explain price scope")

Note: `"explain price scope"` is matched by the `documentary_knowledge` intent before
`_detect_clarification_intent` is reached, because "explain price scope" contains
"price scope rule" which is in the RAG keyword list. Only the bare `"explain price"`
triggers `clarify_prices`.

## 7. Conclusion

T203 adds five targeted clarification intents that give users actionable guidance instead
of a generic disambiguation message. Clear questions are unaffected: the detection runs
after all tool-routing checks and uses exact-match sets for bare phrases to prevent
false positives on scoped variants.

# Chatbot Use Cases — Pricing Data Assistant Agent

## 1. Purpose

The Pricing Data Assistant Agent is a controlled AI assistant integrated into Pricing Control Tower.

Its purpose is to help business users understand pricing data, price changes, KPI definitions, anomalies, and business rules.

The assistant is read-only and must never modify data.

## 2. MVP Scope

The MVP chatbot supports three operational use cases.

### UC1 — Get country revenue over a period

User question examples:

- What is the revenue for France between 2026-01-01 and 2026-01-31?
- Give me the country revenue for France in January 2026.
- How much revenue did France generate last month?

Authorized tool:

```text
get_country_revenue
````

Expected input:

* country identifier or country name
* start date
* end date

Expected answer:

* country
* period
* revenue amount
* currency when available
* short business interpretation

Expected behavior:

The assistant calls the authorized business tool, receives structured JSON, and reformulates the result in business language.

The assistant must not generate SQL.

---

### UC2 — List store price changes over a period

User question examples:

* List price changes for store Lille between 2026-01-01 and 2026-01-31.
* Which price changes happened in store 12 last month?
* Show me the price change history for this store.

Authorized tool:

```text
list_store_price_changes
```

Expected input:

* store identifier or store name
* start date
* end date

Expected answer:

* store
* period
* list of price changes
* product concerned
* old price
* new price
* effective date
* status when available
* short summary

Expected behavior:

The assistant retrieves the list from the authorized business endpoint and summarizes the result.

The assistant must not create, approve, reject, or apply price changes.

---

### UC3 — List store/country price mismatches

User question examples:

* Which products have a store price different from the country price?
* List price mismatches for store Lille.
* Are there products not aligned with the country price in this store?

Authorized tool:

```text
list_store_country_price_mismatches
```

Expected input:

* store identifier or store name
* optional date or current date depending on backend capability

Expected answer:

* store
* country
* list of mismatched products
* country price
* store price
* difference amount
* difference percentage when available
* short business interpretation

Expected behavior:

The assistant identifies mismatches using the authorized business tool and explains the result.

The assistant can suggest that the user reviews the mismatch, but must not create a price change request automatically.

---

## 3. Supported Question Categories

### 3.1 KPI Questions

Supported in MVP only when mapped to an authorized tool.

Included:

* country revenue over a period

Not included in MVP unless a dedicated tool exists:

* margin by product
* promotion performance
* average basket
* sales volume by store
* uplift calculation

Expected behavior for unsupported KPI questions:

The assistant explains that the KPI is not yet available in the chatbot MVP and suggests using the dashboard or future analytical tools.

---

### 3.2 Anomaly Questions

Supported in MVP only for price mismatches between store and country prices.

Included:

* store price different from country price
* products not aligned with country reference price

Not included in MVP unless a dedicated tool exists:

* margin drop detection
* ineffective promotion detection
* abnormal sales drop
* suspicious price evolution
* stock-related anomaly

Expected behavior:

The assistant may explain the concept of an anomaly but must not claim that an unsupported anomaly has been detected automatically.

---

### 3.3 Pricing Questions

Supported in MVP:

* list store price changes over a period
* list store/country price mismatches

Not allowed:

* create price change request
* approve price request
* reject price request
* apply price
* update price
* delete price

Expected behavior:

The assistant can explain pricing information and suggest manual review actions, but never performs pricing workflow actions.

---

### 3.4 Promotion Questions

Not operationally supported in the MVP unless a dedicated promotion tool is added.

Allowed as explanatory knowledge only:

* explain what a promotion is
* explain discount rate
* explain promotion period
* explain promotion scope

Not supported:

* create promotion
* stop promotion
* calculate promotion performance unless a dedicated tool exists
* compare promotions without an authorized tool

Expected behavior:

The assistant states that promotion analysis is not available in the chatbot MVP and redirects the user to the existing promotion dashboard when relevant.

---

### 3.5 RBAC Questions

Allowed as explanatory knowledge only.

Supported examples:

* What can a pricing analyst do?
* What can a store manager see?
* Why can’t a store manager approve a country promotion?

The assistant can explain documented roles and permissions.

Not allowed:

* change user role
* grant permission
* bypass RBAC
* reveal data outside the user scope

Expected behavior:

The assistant must respect the user scope passed by the application and must never suggest bypassing permissions.

---

## 4. Out-of-Scope Questions

The assistant must refuse or redirect when the user asks for:

* SQL query generation
* direct database access
* data modification
* price creation or update
* approval or rejection of a price request
* promotion creation or deletion
* RBAC bypass
* sensitive or unauthorized data
* unsupported analytics
* predictions or recommendations presented as automatic decisions
* actions outside Pricing Control Tower

Example refusal:

```text
I cannot perform this action because the assistant is read-only and does not modify pricing data. You can use the dedicated Pricing Control Tower workflow to submit or approve price changes.
```

---

## 5. Response Principles

The assistant responses must be:

* clear
* business-oriented
* concise
* based only on authorized tools
* transparent when data is missing
* explicit when a question is outside the MVP scope

The assistant must not invent:

* data
* prices
* revenues
* statuses
* endpoints
* SQL queries
* user permissions

---

## 6. MVP Validation Criteria

The chatbot MVP is considered valid if it can answer the following scenarios:

1. Get country revenue for a given period.
2. List price changes for a store over a given period.
3. List price mismatches between store and country prices.
4. Refuse a request to modify data.
5. Refuse or redirect an unsupported analytics question.
6. Explain that SQL generation and direct database access are not allowed.

````

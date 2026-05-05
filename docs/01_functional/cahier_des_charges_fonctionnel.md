# Functional Specification

> **Project:** Pricing Control Tower
> **Domain:** Price Management and Artificial Intelligence
> **Version:** 1.0 — MVP

---

## 1. Project Context

The Pricing Control Tower project is a web application for price management that centralizes, analyzes, and controls prices and promotions within a multi-store organization.

This project is carried out as part of an RNCP professional certification in AI development. Its goal is to demonstrate the ability to design a complete data architecture, develop a web application connected to data services, and integrate artificial intelligence features.

The project simulates a realistic business context with traceability, governance, and performance constraints.

---

## 2. Product Objectives

The application enables business users to work on the following axes:

### 2.1 Analysis and Management

- **Visualization** — Sales tracking in quantity and revenue.
- **Performance** — Analysis of price and promotion effectiveness.
- **Comparison** — Performance benchmarking between stores and at the national level.

### 2.2 Pricing and Promotions

- **Consultation** — Access to standard and promotional prices (country and store levels).
- **History** — Full history of applied prices.
- **Promotional effectiveness** — Measurement of sales acceleration relative to a *baseline*.

### 2.3 Decision Support and Governance

- **Detection** — Identification of performance anomalies or pricing inconsistencies.
- **Workflow** — Validation cycle management for any price change.
- **Traceability** — Full audit of actions performed on the platform.

### 2.4 Artificial Intelligence (Evolution)

- Key performance indicator (KPI) explanation.
- Anomaly root cause analysis.
- Corrective action suggestions (without automation).

---

## 3. MVP Scope

| Axis | Scope Definition |
|---|---|
| **Geographic** | France only |
| **Organization** | Multi-store structure |
| **Catalog** | 3 product families (~10 products per family) |
| **Pricing** | National prices and local overrides (store) |
| **Promotions** | National and local |
| **Data** | Simulated transactional flows |
| **Process** | Manual creation and validation workflow |
| **Analytics** | Central `obt_sales` table and specific KPIs |

---

## 4. Users

### MVP Phase

| Role | Description |
|---|---|
| **Administrator** | Single user with full access and modification rights. |

### Target Evolutions

| Role | Description |
|---|---|
| **Analyst** | Read-only access. |
| **Store Manager** | Local management. |
| **Country Manager** | Global vision and strategy. |
| **Validator** | Approval authority for change requests. |

---

## 5. Business Concepts

### 5.1 Product and Price

- **Product** — Entity belonging to a family, associated with one or more prices.
- **Price** — Defined at country or store level. It can be of type `STANDARD` or `PROMO`, has a validity period, and is subject to historical archiving.

When a price exists at both country and store level, the store price constitutes a local override and takes priority.

### 5.2 Promotion and Sale

- **Promotion** — Temporal entity influencing promotional prices at national or local level.
- **Sale** — Transaction made in store, linking a product to a price and, where applicable, to a promotion.

### 5.3 Validation Flow

- **Change request** — Request concerning a product or geographic scope, subject to validation before application.

In the MVP, a single administrator user can create, validate, and apply a price change request.
In a future evolution, rights will be restricted to authorized managers, with mandatory validation by a distinct role.

---

## 6. Business Rules

Business rules below are identified by a unique code (`RGxx`) to ensure traceability in code and tests.

### 6.1 Scope and Organization

| Rule | Statement |
|---|---|
| **RG01** | The application only manages **physical stores**. The channel concept (online / offline) is out of scope. |

### 6.2 Pricing Management

| Rule | Statement |
|---|---|
| **RG02** | A product can have **multiple successive prices** over time. |
| **RG03** | A price is always defined for a country (`country_id` mandatory). The `store_id` field is optional. |
| **RG04** | A price can be defined at **country** level (global price) or at **store** level (local specific price). |
| **RG05** | Any promotional price must be **imperatively** associated with an active promotion. |
| **RG06** | Price validity is bounded by `effective_from` and `effective_to` fields. |
| **RG07** | There must never be multiple active prices simultaneously for the same product in the same scope (country or store) over a given period. |

### 6.3 Promotion Management

| Rule | Statement |
|---|---|
| **RG08** | Promotions are strictly bounded by a start date and an end date. |
| **RG08bis** | For a given product, in a given store, at a given date, the applicable price is determined in the following priority order: (1) active store price, (2) failing that, active country price. |
| **RG09** | A promotion is defined either at country level (applicable to all stores in the country) or at a specific store level. |
| **RG09bis** | A promotion targets **a single product** (`product_id` NOT NULL). No bundles or sets. |
| **RG09ter** | The discount type (`discount_type`) is limited to two values: `PERCENTAGE` (percentage reduction) or `FIXED_PRICE` (imposed fixed price). |

### 6.4 Sales Management

| Rule | Statement |
|---|---|
| **RG10** | For each sale, quantity and amount must be **strictly positive**. |

### 6.5 Workflow and Audit

| Rule | Statement |
|---|---|
| **RG11** | Applying a new price is conditional on **prior validation**. |
| **RG12** | Request statuses follow the cycle: `PENDING` → `APPROVED` → `APPLIED` *(or `REJECTED` / `FAILED`)*. |
| **RG13** | Price history and audit log (user actions) are **mandatory**. |

---

## 7. KPIs and Analytics

### Data Structure

Uses a single central analytical table: `obt_sales`.

### Performance Indicators

- **Price** — Before/after change performance comparison and country-level benchmark.
- **Promotion**:
  - *Baseline* fixed at **14 days** before promotion start.
  - **Main KPI (uplift)**: calculated **only at product level** — same product BEFORE vs DURING promo. Family must never be used for this calculation.
  - **Complementary KPI (family)**: variation of other product sales in the same family during the promo, to detect cannibalization or halo effect.
  - Acceleration measurement (Quantity and Revenue).

---

## 8. Technical Architecture

| Component | Technology | Role |
|---|---|---|
| **Backend** | FastAPI | Business logic and REST API exposure |
| **Frontend** | Django / Tailwind CSS | User interface and server-side rendering (SSR) |
| **Database** | PostgreSQL | `pct_core` (transactional) and `pct_analytics` (data) storage |
| **Transformation** | dbt | Data pipeline for the `obt_sales` table |
| **AI Service** | Dedicated Python | Read-only analysis and suggestions |
| **Deployment** | Docker / GCP Cloud Run | Containerization and cloud hosting |

---

## 9. Constraints

- Carried out in **full autonomy**.
- Modular architecture favoring maintainability.
- Use of simulated data consistent with the sector.
- **Prohibition** of pricing decision automation (*human in the loop*).
- Requirement for **full traceability** on data flows and actions.

---

## 10. Definition of Done (DoD)

The project is considered complete after validation of the following steps:

- [ ] PostgreSQL instance operational.
- [ ] FastAPI API and Django application functional and interconnected.
- [ ] Analytical computations validated via dbt.
- [ ] KPIs available and compliant with business rules.
- [ ] AI service operational in read-only mode.
- [ ] CI/CD pipeline and monitoring configured.
- [ ] Exhaustive technical and functional documentation.

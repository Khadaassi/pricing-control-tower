# Data Generation — Sales Dataset (MVP)

## 1. Purpose

Generate a simulated sales dataset consistent with the Pricing Control Tower business model.

This dataset is used to:

- populate the `pct_core.sales_transaction` table
- enable dbt-based analytics
- simulate realistic scenarios for KPIs
- prepare future anomaly detection

---

## 2. General Assumptions

- One row = one receipt line item
- Quantity can be greater than 1
- The paid price always comes from the `price` table
- Store price takes priority over country price
- An active promotion is applied if a promo price is available
- Data is deterministic and reproducible (fixed seed)

---

## 3. Sales Generation

Each sale is generated according to the following steps:

1. Random selection of an active product
2. Random selection of a store
3. Transaction date generation
4. Selection of the active price at the date
5. Quantity computation
6. Revenue computation (`quantity × unit_price`)
7. Export to a CSV file

---

## 4. Quantity Distribution

### Purpose

Avoid an artificial uniform distribution and introduce simple, explainable variability.

### Approach

Quantity is computed from 3 main factors.

### 4.1 Product Variability

Each product is implicitly associated with a volume level:

- low volume
- medium volume
- high volume

Implementation:

```python
product_factor = product_id % 3
```

### 4.2 Store Variability

Stores are divided into two categories:

- low-volume stores
- high-volume stores

Implementation:

```python
store_factor = 1 if store_id % 2 == 0 else 0
```

### 4.3 Promotion Effect

Promotions increase the purchased quantity:

```python
promo_boost = 1 if price_type == "PROMO" else 0
```

### 4.4 Quantity Computation

```python
quantity = 1 + product_factor + store_factor + promo_boost
quantity += random.choice([0, 1])
```

### Expected Result

| Criterion | Value |
|---|---|
| Minimum quantity | 1 |
| Maximum quantity (before seasonality) | 6 |
| Distribution | Non-uniform |
| Variability | Explainable |
| Behavior | Reproducible |

---

## 5. Simple Seasonality

### Purpose

Introduce simple temporal variation to make analyses more credible.

### Approach

Seasonality relies on 3 elements:

### 5.1 Saturday Effect

Saturday is a high commercial activity day:

```python
saturday_boost = 1 if tx_date.weekday() == 5 else 0
```

### 5.2 Sunday Effect (closed stores)

Sunday is considered a closure day (with exceptions):

```python
if tx_date.weekday() == 6:
    if random.random() < 0.9:
        continue
```

> 90% of sales are skipped — a few persist (exceptional cases).

### 5.3 Monthly Effect

A simple variation is introduced over the period:

```python
month_boost_map = {
    1: 0,
    2: 0,
    3: 1,
    4: 1,
    5: 1,
    6: 2,
}
```

Partial application:

```python
if random.random() < 0.3:
    quantity += month_boost
```

### 5.4 Final Application

```python
quantity += saturday_boost

if random.random() < 0.3:
    quantity += month_boost

quantity = min(quantity, 8)
```

### Expected Result

- More sales on Saturday
- Very few sales on Sunday
- Slight volume increase in certain months
- Observable temporal variation
- Dataset remains stable and controlled

---

## 6. Consistency Checks

The following checks are applied:

- `revenue = quantity × unit_price`
- `promotion_id` ↔ `price_type` consistency
- Business constraint compliance
- Quantity distribution verified
- Sales per day distribution verified

---

## 7. MVP Limitations

The following simplifications are intentional:

- No customer behavior
- No product × store correlation
- No stock management
- No public holiday calendar
- No advanced seasonality (e.g., weather, events)
- No complex statistical modeling

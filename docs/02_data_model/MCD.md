# Simplified CDM — Pricing Control Tower

## 1. Purpose

This conceptual data model (CDM) describes the main business entities of the Pricing Control Tower system and their relationships.

It serves as the reference for:

* the PostgreSQL database design
* the SQLAlchemy model implementation
* the Alembic migration setup
* the overall system understanding

---

## 2. Main Entities

### Reference Data

* **Country**: country in which stores operate
* **Store**: physical or logical point of sale
* **Product**: product sold
* **ProductFamily**: product grouping
* **ProductImage**: illustration associated with a product

---

### Pricing

* **Price**: price of a product in a given store
* **PriceHistory**: history of price modifications

---

### Promotions

* **Promotion**: promotional action applied to a single **Product**, scoped to a country or a specific store

---

### Performance

* **Sale**: completed sale (main business fact for analysis)

---

### Workflow & Traceability

* **PriceChangeRequest**: request for a price modification
* **User**: system user (creation / validation)
* **AuditLog**: user action log

---

## 3. Main Relationships

### Reference Data

* A **Country** has multiple **Store**s

* A **Store** belongs to a single **Country**

* A **Product** belongs to a **ProductFamily**

* A **Product** can have multiple **ProductImage**s

---

### Pricing

* A **Product** is associated with multiple **Price**s

* A **Price** is defined for a **Product** and a **Store**

* A **Price** has multiple entries in **PriceHistory**

---

### Promotions

* A **Promotion** targets exactly one **Product**
* A **Promotion** is scoped to a **Country** (optionally a specific **Store**)
* A **Promotion** can be linked to a **Price**
* A **Promotion** can be associated with **Sale** transactions

---

### Performance

* A **Sale** concerns a **Product**
* A **Sale** is made in a **Store**
* A **Sale** can be associated with a **Promotion**

---

### Workflow

* A **PriceChangeRequest** concerns a **Product**

* A **PriceChangeRequest** concerns a **Store**

* A **PriceChangeRequest** is linked to a **Price**

* A **User** creates or validates a **PriceChangeRequest**

---

### Traceability

* A **User** generates entries in **AuditLog**

---

## 4. Main Business Rules

* A price is always defined for a **Product / Store** pair
* A price can be of type **STANDARD** or **PROMO**
* A price can be marked as **country-recommended** (boolean)
* Any price modification must be traced in **PriceHistory**
* Any significant user action must be traced in **AuditLog**

---

## 5. Simplifications for the MVP

To maintain a manageable complexity level for the first version:

* The **channel (online / store)** is not explicitly modeled
* Promotion targeting is simplified (no `PromotionTarget` entity)
* The country recommendation is carried by an attribute on the **Price** entity
* The price change workflow is directly linked to **Price**

These choices allow progressive implementation while remaining extensible.

---

## 6. Planned Evolutions

The model may evolve in future versions to include:

* A **Channel** entity (online / instore)
* A **PromotionTarget** entity for finer targeting
* More advanced pricing rules
* Optimizations for the analytical layer (`pct_analytics`)

---

## 7. Conclusion

This CDM provides a coherent, understandable, and actionable base for:

* the logical data model (LDM) creation
* the database implementation
* the backend development

It reflects a balance between simplicity (MVP) and extensibility.

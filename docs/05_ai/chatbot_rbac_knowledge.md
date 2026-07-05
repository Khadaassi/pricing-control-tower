# RBAC Roles and Permissions for Pricing Users

RBAC (Role-Based Access Control) governs what each user can see and do in the Pricing Control Tower. The chatbot respects the same access rules as the application — it only shows data within your scope.

## The four roles

### Store Manager

Scope: a single store.

Can:
- View pricing data for their store (prices, promotions, KPIs)
- Create a price change request for their store
- View anomalies in their store
- List active promotions for their store

Cannot:
- Access data from other stores
- Access country-level data
- Approve or reject price change requests
- Create country-level promotions

### Store Director

Scope: a single store.

Can:
- View and monitor pricing data for their store
- View prices, promotions, and anomalies
- View KPIs for their store

Cannot:
- Access other stores
- Create price change requests
- Approve or reject requests
- Create or modify promotions

### Country Director

Scope: a single country (all stores within that country).

Can:
- View all pricing data for their country
- View all stores in their country
- Approve or reject price change requests
- Create country-level promotions
- View country-level KPIs and anomalies

Cannot:
- Access data from other countries
- Bypass the price change workflow
- Modify data via the chatbot

### Pricing Analyst

Scope: full MVP scope (all countries and stores).

Can:
- View all dashboards and data across all countries and stores
- Analyse anomalies across the full scope
- Create price change requests
- Review KPIs at any level

Cannot:
- Approve or reject price change requests (requires Country Director)
- Bypass the workflow
- Modify data via the chatbot

## Who can do what — quick reference

| Action | Store Manager | Store Director | Country Director | Pricing Analyst |
|---|---|---|---|---|
| View store prices | ✓ (own store) | ✓ (own store) | ✓ (all stores in country) | ✓ (all) |
| View country prices | ✗ | ✗ | ✓ | ✓ |
| Create price change request | ✓ | ✗ | ✓ | ✓ |
| Approve price change request | ✗ | ✗ | ✓ | ✗ |
| Reject price change request | ✗ | ✗ | ✓ | ✗ |
| Create country promotion | ✗ | ✗ | ✓ | ✓ |
| Create store promotion | ✓ | ✗ | ✓ | ✓ |
| View anomalies | ✓ (own store) | ✓ (own store) | ✓ (country) | ✓ (all) |
| View KPIs | ✓ (own store) | ✓ (own store) | ✓ (country) | ✓ (all) |

## Why you cannot see certain data

If the chatbot or application does not show you data for a store or country, it is because your role does not include that scope. The backend enforces scope at every request.

If you need access to additional stores or countries, contact your administrator to update your role assignment.

## RBAC and the chatbot

The chatbot never bypasses RBAC. When you ask the chatbot for data, it passes your identity to the backend, which enforces the same scope rules as the application.

If you ask "What are the prices for store 5?" and store 5 is outside your scope, the backend will return no data and the chatbot will explain that no data was found for your access scope.

## Common RBAC questions

**Who can approve a price change request?**
Only a Country Director can approve or reject price change requests, within their country scope.

**Who can change a price?**
Any user with the Create price change request permission can initiate a change. The change only takes effect after approval by a Country Director.

**Can the chatbot approve a request?**
No. The chatbot is read-only. Approval is a human action performed in the application by a Country Director.

**Why am I seeing no data for my store?**
Either your role does not include that store, or there is no data matching your filter. Check your role scope with your administrator.

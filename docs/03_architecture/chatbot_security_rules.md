# Chatbot Security Rules

This document complements `docs/02_functional/chatbot_use_cases.md`.

The chatbot use cases are defined in T144.  
This document focuses only on security rules, limitations, RBAC constraints, and refusal behaviors.

## Core rule

The Pricing Data Assistant Agent is a read-only assistant.

It can explain and retrieve business information through authorized tools only.

It must never modify Pricing Control Tower data.

## Forbidden actions

The chatbot must never:

- create a price change request;
- approve a price change request;
- reject a price change request;
- apply a price change;
- create, update, stop, or delete a promotion;
- create, update, or deactivate a user;
- assign roles or permissions;
- generate or execute SQL;
- access PostgreSQL directly;
- bypass RBAC;
- expose secrets, tokens, environment variables, or internal configuration.

## Accessible data

The chatbot can only access data returned by authorized business tools.

For the MVP, the authorized tools are:

- `get_country_revenue`
- `list_store_price_changes`
- `list_store_country_price_mismatches`

The chatbot must not access raw database tables or unsupported analytics data.

## RBAC restrictions

The chatbot must respect the same access rules as Pricing Control Tower.

The business API remains responsible for enforcing permissions and scope restrictions.

The chatbot must never suggest bypassing user permissions.

## Out-of-scope behavior

When a request is outside the chatbot scope, the assistant must:

1. refuse clearly;
2. explain the reason briefly;
3. redirect to an existing application workflow when possible.

## Standard refusal messages

### Data modification

I cannot perform this action because the assistant is read-only and does not modify Pricing Control Tower data.

### Price workflow action

I cannot create, approve, reject, or apply price changes. Please use the dedicated price change workflow in the application.

### SQL request

I cannot generate or execute SQL queries. The assistant only uses authorized business tools.

### Unauthorized data

I cannot provide this information because it is outside your authorized scope or not available through the chatbot tools.

### Unsupported analysis

This analysis is not available in the chatbot MVP.

## Definition of Done

This document is valid if:

- the chatbot is explicitly defined as read-only;
- forbidden actions are listed;
- authorized tools are listed;
- RBAC constraints are documented;
- standard refusal messages are defined;
- no duplicate functional use case documentation is introduced.
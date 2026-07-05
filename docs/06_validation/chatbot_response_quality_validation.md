# T202 — Chatbot Response Quality Validation

## Writing rules applied

| Rule | Applied in |
|---|---|
| Answer directly to the question | `ResponseGenerationService.format_tool_response` — Summary is first |
| Use short sentences | All format methods |
| Structure responses in readable blocks | Summary / Details / Suggested next step |
| Do not invent information | Anti-hallucination rules in `RAGPromptBuilder` |
| Never hide missing data | Empty-case returns explicit "No matching data was found." |
| Mention limits when context-dependent | Guardrail and fallback messages say explicitly what is unavailable |
| Recommend only when justified | "Suggested next step" only for PENDING requests or price comparisons |
| Never propose automatic write actions | Guardrail confirms no action is applied; "Suggested next step" verbs are review / compare / check |

---

## Response format matrix

| Question | Route | Format | Suggested next step | Status |
|---|---|---|---|---|
| List active promotions | PromotionTool | Summary + Details + next step | Yes — review before extending | ✅ |
| List pending price change requests | PriceChangeRequestTool | Summary + Details + next step | Yes — review workflow | ✅ |
| Show approved price requests | PriceChangeRequestTool | Summary + Details | No (approved, no action needed) | ✅ |
| List prices | PriceTool | Summary + Details + next step | Yes — compare with reference | ✅ |
| List countries | ReferenceDataTool | Summary + Details | No | ✅ |
| What stores are available? | ReferenceDataTool | Summary + Details | No | ✅ |
| List active products | ReferenceDataTool | Summary + Details | No | ✅ |
| Explain price change workflow | RAG | Direct answer + details + sources | Optional (LLM decides) | ✅ |
| Approve request 12 | Guardrail | Cannot act + alternatives | N/A | ✅ |
| Tell me about store 1 | Clarification | Ask for missing detail | N/A | ✅ |
| Unknown supplier question | Fallback | List supported topics | N/A | ✅ |
| No matching data (any tool) | Tool | "No matching data was found." | No | ✅ |

---

## Tool response example — promotions

```
Summary:
1 promotion(s) found.

Details:
- Product 5 — 20.00% discount — from 2026-06-01 to 2026-06-15

Suggested next step:
Review promotions before extending them.
```

## Tool response example — price change requests (pending)

```
Summary:
1 price change request(s) found.

Details:
- Request #12 — Product 4 — pending — requested price: 19.99

Suggested next step:
Review the validation workflow for pending requests.
```

## Static response example — guardrail

```
I cannot perform this action directly.

What I can do:
- explain the workflow
- help identify the relevant request
- show the current status if the data is available
```

## Static response example — clarification

```
I need one detail to answer correctly.

Are you asking about:
- current operational data (prices, promotions, price change requests)
- reference data (stores, products, countries)
- business rules or documentation?
```

## Static response example — fallback

```
I cannot answer this reliably with the available tools or documentation.

You can ask me about:
- prices
- promotions
- anomalies
- price change requests
- products and stores
- roles and permissions
- KPI definitions
- chatbot documentation
```

---

## RAG prompt style guidelines added (T202)

Added to `prompt_builder.py`:

```
Writing style:
- Use a concise business tone.
- Start with the direct answer.
- Use bullet points only when they improve readability.
- Do not over-explain technical implementation details unless the user explicitly asks.
- Add a short "Suggested next step" only if it is directly supported by the documentary context.
- Keep responses between 3 and 8 lines for simple answers.
- Limit bullet points in details to 3 where possible.

Expected answer format:
1. Direct answer
2. Important details, if useful (max 3 bullet points)
3. Suggested next step (only if supported by the documentary context)
4. Sources used
```

Anti-hallucination rules from T197 are preserved unchanged.

---

## Forbidden recommendation patterns (verified)

| Pattern | Present in any response? |
|---|---|
| "apply now" | No |
| "approve now" | No |
| "reject now" | No |
| Fabricated margin or revenue impact | No |
| Invented cause or blame | No |
| Automatic decision without data | No |

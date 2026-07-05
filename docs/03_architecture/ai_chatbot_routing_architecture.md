# Architecture du routage du chatbot IA

## Vue d'ensemble

Le chatbot du Pricing Control Tower repose sur un routage d'intention **déterministe** : aucun LLM ne classe les questions. À la place, un registre de règles déclaratives associe des expressions normalisées à des intentions, selon un ordre de priorité strict.

Cette approche garantit :
- une latence prévisible (pas d'appel LLM pour la classification)
- un comportement entièrement testable et rejouable
- une séparation nette entre la détection d'intention et la génération de réponse

---

## Architecture modulaire

Le monolithe original (`chatbot_orchestrator.py`, ~2 300 lignes) a été décomposé en couches indépendantes :

```
app/
├── orchestrator/
│   ├── chatbot_orchestrator.py   # Point d'entrée public (~230 lignes)
│   ├── normalization.py          # normalize() : minuscule + apostrophes + accents
│   ├── intent_types.py           # Enum Intent, RouteType, dataclasses
│   ├── intent_registry.py        # INTENT_RULES : liste déclarative ordonnée
│   ├── intent_router.py          # IntentRouter : parcourt les règles
│   ├── response_dispatcher.py    # ResponseDispatcher : oriente vers le handler
│   └── chat_context.py           # ChatContext : paramètres d'une question
│
├── intents/
│   ├── guardrail_phrases.py      # Expressions d'actions d'écriture interdites
│   ├── rbac_phrases.py           # Rôles, permissions, droits
│   ├── workflow_phrases.py       # Règles métier, workflow, promotions inefficaces
│   ├── anomaly_phrases.py        # Anomalies, définitions, criticité
│   ├── pricing_phrases.py        # KPI data, KPI explication, prix, demandes
│   ├── promotion_phrases.py      # Promotions, clarifications
│   ├── reference_data_phrases.py # Magasins, pays, produits, familles
│   ├── capability_phrases.py     # Capacités et limites du chatbot
│   └── decision_phrases.py       # Aide à la décision, recommandation
│
└── handlers/
    ├── guardrail_handler.py      # Refus d'actions d'écriture
    ├── static_response_handler.py # Réponses statiques (capacités, limites, KPI guide)
    ├── clarification_handler.py   # Demandes de précision
    ├── tool_response_handler.py   # Appels aux services et outils métier
    └── rag_response_handler.py    # Génération RAG via ChromaDB + LLM
```

---

## Flux d'une question

```
Question utilisateur
       │
       ▼
  normalize()          ← minuscule, apostrophes → ', accents NFKD supprimés
       │
       ▼
  ChatContext          ← original_question, normalized_question, user_email, store_id, lang
       │
       ▼
  IntentRouter.route()
       │
       ├─ parcourt INTENT_RULES par priorité croissante
       ├─ teste : exact_phrases → sous-chaîne (phrases) → regex
       └─ retourne IntentMatch (intent, route_type, matched_phrase)
              │
              ▼
       ResponseDispatcher.dispatch()
              │
              ├── RouteType.GUARDRAIL     → GuardrailHandler
              ├── RouteType.STATIC        → StaticResponseHandler
              ├── RouteType.CLARIFICATION → ClarificationHandler
              ├── RouteType.TOOL          → ToolResponseHandler
              ├── RouteType.RAG           → RAGResponseHandler
              └── RouteType.UNSUPPORTED   → message non supporté
                          │
                          ▼
                  dict réponse uniforme
              { question, intent, selected_tool, status, answer, source, … }
```

---

## Normalisation

La fonction `normalize()` (`app/orchestrator/normalization.py`) est appliquée à **la question** avant matching et à **chaque expression** du registre au chargement du module.

```python
def normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"  +", " ", text).strip()
    return text
```

Effets garantis :
| Entrée | Sortie |
|--------|--------|
| `"Quels sont les Différents Rôles ?"` | `"quels sont les differents roles ?"` |
| `"Gérer une promotion"` | `"gerer une promotion"` |
| `"peux’tu approuver"` | `"peux'tu approuver"` |
| `"  prix   magasin  "` | `"prix magasin"` |

Les tirets sont préservés (`peux-tu` reste `peux-tu`).

---

## Registre d'intentions (INTENT_RULES)

Le registre (`app/orchestrator/intent_registry.py`) est une liste d'`IntentRule` ordonnées par priorité. **La règle avec le numéro de priorité le plus bas gagne.**

| Priorité | Intent | RouteType | Source des expressions |
|----------|--------|-----------|------------------------|
| 0 | `GUARDRAIL` | `GUARDRAIL` | `guardrail_phrases.py` |
| 10 | `EXPLAIN_RBAC` | `TOOL` | `rbac_phrases.py` |
| 20 | `EXPLAIN_BUSINESS_RULE` | `TOOL` | `workflow_phrases.py` |
| 25 | `DOCUMENTARY_KNOWLEDGE` | `RAG` | `workflow_phrases.py` (anomalies documentaires) |
| 30 | `EXPLAIN_ANOMALY_DEFINITION` | `TOOL` | `anomaly_phrases.py` |
| 35 | `LIST_ANOMALIES` | `TOOL` | `anomaly_phrases.py` (PRICE_TYPE) |
| 40 | `LIST_STORE_COUNTRY_PRICE_MISMATCHES` | `TOOL` | `anomaly_phrases.py` (mismatch) |
| 45 | `LIST_ANOMALIES` | `TOOL` | `anomaly_phrases.py` (général) |
| 50 | `LIST_STORE_PRICE_CHANGES` | `TOOL` | `pricing_phrases.py` |
| 55 | `GET_KPI_DATA` | `TOOL` | `pricing_phrases.py` + regex `\bca\b` |
| 60 | `DECISION_KPI_GUIDANCE` | `STATIC` | `decision_phrases.py` |
| 65 | `EXPLAIN_KPI` | `TOOL` | `pricing_phrases.py` |
| 70 | `PROMOTIONS` | `TOOL` | `promotion_phrases.py` |
| 75 | `PRICES` | `TOOL` | `pricing_phrases.py` |
| 80 | `REFERENCE_DATA` | `TOOL` | `reference_data_phrases.py` |
| 85 | `CHATBOT_CAPABILITIES` | `STATIC` | `capability_phrases.py` |
| 90 | `CHATBOT_LIMITS` | `STATIC` | `capability_phrases.py` |
| 95 | `CLARIFY_PROMOTION_CONTEXT` | `CLARIFICATION` | `promotion_phrases.py` |
| 100 | `GENERIC_RECOMMENDATION_CLARIFICATION` | `CLARIFICATION` | `decision_phrases.py` |
| 110 | `DOCUMENTARY_KNOWLEDGE` | `RAG` | `workflow_phrases.py` |
| 120–125 | Clarifications granulaires | `CLARIFICATION` | pricing, promotion, reference_data phrases |
| ∞ | `UNKNOWN` | `UNSUPPORTED` | aucune règle correspondante |

---

## Handlers

### GuardrailHandler
Retourne un message de refus structuré. Le chatbot est **lecture seule** : toute demande d'action d'écriture (approuver, rejeter, créer, supprimer, modifier) est bloquée à ce niveau.

### StaticResponseHandler
Retourne des réponses fixes sans appel réseau pour trois intents :
- `CHATBOT_CAPABILITIES` — description des capacités du chatbot
- `CHATBOT_LIMITS` — description des limites
- `DECISION_KPI_GUIDANCE` — checklist statique d'indicateurs à vérifier avant une décision

### ClarificationHandler
Retourne un message de clarification bilingue (FR/EN) lorsqu'une question est trop vague pour être traitée sans contexte supplémentaire (ex. "prix" seul, "cette promotion", etc.).

### ToolResponseHandler
Orchestre les appels aux services et outils métier. Gère les intents :
- `EXPLAIN_RBAC` → `RBACExplanationService`
- `EXPLAIN_BUSINESS_RULE` → `BusinessRulesExplanationService`
- `EXPLAIN_KPI` → `KPIExplanationService`
- `GET_KPI_DATA` → `KPIDataTool`
- `LIST_ANOMALIES` → `AnomalyTool` (avec sous-classification : critique, margin, promo)
- `LIST_STORE_COUNTRY_PRICE_MISMATCHES` → `AnomalyTool`
- `LIST_STORE_PRICE_CHANGES` → `PriceChangeRequestTool`
- `PROMOTIONS` → `PromotionTool`
- `PRICES` → `PriceTool`
- `REFERENCE_DATA` → `ReferenceDataTool`

### RAGResponseHandler
Interroge ChromaDB (`DocumentRetriever`), filtre par score de pertinence (`rag_min_score`), construit un prompt via `RAGPromptBuilder`, génère la réponse via `BaseLLMProvider`. Les exceptions (ChromaDB indisponible, timeout LLM) sont interceptées et retournent un message d'erreur technique structuré sans lever d'exception vers l'orchestrateur.

---

## Décisions de conception

### Pourquoi un routage déterministe ?

Le MVP cible des questions métier bien délimitées (anomalies, KPI, promotions, RBAC). Un classifieur LLM ajouterait de la latence, du coût et de l'imprévisibilité sans apporter de valeur pour ce périmètre. Le routage déterministe est 100 % testable et rejouable.

### Pourquoi pré-normaliser les expressions au chargement ?

Les expressions du registre sont normalisées une seule fois via `_n()` et `_ne()` à l'import du module. Le matching runtime est alors une simple comparaison de sous-chaînes, sans aucun traitement répété.

### Pourquoi `Intent(str, Enum)` ?

Les valeurs des enum sont identiques aux chaînes originales utilisées dans les tests et l'API existante (`"explain_rbac"`, `"get_kpi_data"`, etc.). La rétro-compatibilité est garantie sans aucune migration.

### Pourquoi les promotions inefficaces routent-elles vers `explain_business_rule` ?

Les questions du type "promotion ne fonctionne pas" ou "gérer une promotion inefficace" ne sont pas des questions de données (pas d'appel à `PromotionTool`) : elles demandent une explication des règles métier applicables. Elles sont donc traitées par `BusinessRulesExplanationService` (priority 20), avant que le pipeline RAG (priority 110) ou le tool promotion (priority 70) ne soient évalués.

---

## Tests

Deux fichiers de tests couvrent spécifiquement cette architecture :

| Fichier | Périmètre |
|---------|-----------|
| `tests/orchestrator/test_normalization.py` | 21 cas unitaires de `normalize()` |
| `tests/orchestrator/test_intent_router.py` | 56 cas de routage par intent, priorité et invariance accent |

Ces tests ne dépendent d'aucun mock de service externe — ils testent uniquement la logique déterministe du routage.

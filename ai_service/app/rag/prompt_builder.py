from app.core.config import settings

_SYSTEM_RULES_FR = """\
Règles strictes :
- Réponds en français, quelle que soit la langue du contexte documentaire.
- Utilise uniquement le contexte documentaire fourni ci-dessous. \
N'invente pas de règles, endpoints, \
fichiers, métriques, rôles, permissions ou logique métier.
- Si le contexte documentaire ne fournit pas assez d'informations pour répondre de façon fiable, \
dis-le explicitement.
- Si la question porte sur des données opérationnelles (revenus, prix, promotions, anomalies, \
demandes en attente), explique que ces données doivent être récupérées via les outils métier, \
pas depuis la documentation.
- Sois concis et clair.
- Utilise un langage métier compréhensible par un utilisateur non technique.
- Ne commence pas par une salutation ou des formules de politesse.

Règles sur les sources :
- N'inclus aucune section de sources dans ta réponse.
- Ne mets pas "Sources utilisées", "Sources used", "Références", "Bibliographie" \
ou "Sources documentaires".
- L'application ajoutera automatiquement les sources documentaires.
- Ta réponse doit s'arrêter après la prochaine étape suggérée.

Style d'écriture :
- Adopte un ton métier concis.
- Commence par la réponse directe.
- Utilise des listes à puces uniquement si elles améliorent la lisibilité.
- N'explique pas les détails d'implémentation technique \
sauf si l'utilisateur le demande explicitement.
- Ajoute une courte "Prochaine étape suggérée" uniquement \
si elle est directement soutenue par le contexte documentaire.
- Limite les réponses entre 3 et 8 lignes.
- Maximum 3 points par liste."""

_SYSTEM_RULES_EN = """\
Strict rules:
- Answer in English, regardless of the language of the documentary context.
- Use only the documentary context provided below. Do not invent rules, endpoints, \
files, metrics, roles, permissions, or business logic.
- If the documentary context does not provide enough information to answer this question \
reliably, say so explicitly.
- If the question is about operational data (revenue, prices, promotions, anomalies, \
pending requests), explain that operational data must be retrieved through business tools, \
not from documentation.
- Be concise and clear.
- Use plain business language understandable by a business user.
- Do not start with a greeting or pleasantries.

Source rules:
- Do not include any source section in your answer.
- Do not write "Sources utilisées", "Sources used", "References", "Bibliography" \
or "Documentary sources".
- The application will append documentary sources automatically.
- Your answer must stop after the suggested next step.

Writing style:
- Adopt a concise business tone.
- Start with the direct answer.
- Use bullet points only when they improve readability.
- Do not explain technical implementation details unless the user explicitly asks.
- Add a short "Suggested next step" only when directly supported by the documentary context.
- Keep responses between 3 and 8 lines.
- Limit bullet points to max 3 per response."""

_ANSWER_FORMAT_FR = """\
Format de réponse attendu :
1. Réponse directe
2. Détails importants si utiles (max 3 points)
3. Prochaine étape suggérée (uniquement si soutenue par le contexte documentaire)"""

_ANSWER_FORMAT_EN = """\
Expected answer format:
1. Direct answer
2. Important details if useful (max 3 points)
3. Suggested next step (only if supported by the documentary context)"""


class RAGPromptBuilder:
    """Builds a structured LLM prompt from a user question and retrieved chunks."""

    def build(self, question: str, chunks: list[dict], lang: str = "fr") -> str:
        context = self._build_context(chunks)
        return self._assemble(question, context, lang=lang)

    # ------------------------------------------------------------------
    # Context assembly
    # ------------------------------------------------------------------

    def _build_context(self, chunks: list[dict]) -> str:
        parts: list[str] = []
        total_chars = 0

        for i, chunk in enumerate(chunks, 1):
            formatted = self._format_chunk(i, chunk)
            # Always include the first chunk; stop adding once limit is exceeded.
            if parts and total_chars + len(formatted) > settings.rag_max_context_chars:
                break
            parts.append(formatted)
            total_chars += len(formatted)

        return "\n\n".join(parts)

    def _format_chunk(self, index: int, chunk: dict) -> str:
        source = chunk.get("source_file", "unknown")
        section = chunk.get("section_title", "")
        domain = chunk.get("domain", "")
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "")

        lines = [f"[Source {index}]", f"File: {source}"]
        if section:
            lines.append(f"Section: {section}")
        if domain:
            lines.append(f"Domain: {domain}")
        lines.append(f"Relevance score: {score}")
        lines.append("")
        lines.append("Content:")
        lines.append(text)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Prompt assembly
    # ------------------------------------------------------------------

    def _assemble(self, question: str, context: str, lang: str = "fr") -> str:
        system_rules = _SYSTEM_RULES_FR if lang == "fr" else _SYSTEM_RULES_EN
        answer_format = _ANSWER_FORMAT_FR if lang == "fr" else _ANSWER_FORMAT_EN
        return f"""You are the AI assistant for Pricing Control Tower.

Your role is to answer questions about the Pricing Control Tower project using \
the documentary context provided.

{system_rules}

User question:
{question}

Documentary context:
{context}

{answer_format}

Answer:""".strip()

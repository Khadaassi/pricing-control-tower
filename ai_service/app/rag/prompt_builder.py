from app.core.config import settings

_SYSTEM_RULES = """\
Règles strictes :
- Réponds toujours en français, quelle que soit la langue de la question.
- Utilise uniquement le contexte documentaire fourni ci-dessous.
- N'invente pas de règles, endpoints, fichiers, métriques, rôles, permissions ou logique métier.
- Si la réponse n'est pas explicitement couverte par le contexte documentaire, dis : \
"La documentation disponible ne contient pas suffisamment d'informations pour répondre à cette question de manière fiable."
- Si la question porte sur des données opérationnelles (chiffre d'affaires, prix, promotions, \
anomalies, demandes en cours), explique que ces données doivent être récupérées via les outils \
métier, pas depuis la documentation.
- Sois concis et clair.
- Privilégie un vocabulaire compréhensible par un utilisateur métier.
- Mentionne les documents sources utilisés à la fin de ta réponse.

Style de rédaction :
- Adopte un ton business concis.
- Commence par la réponse directe.
- Utilise des listes à puces uniquement si elles améliorent la lisibilité.
- N'explique pas les détails d'implémentation technique sauf si l'utilisateur le demande explicitement.
- Ajoute une courte "Prochaine étape suggérée" uniquement si elle est directement supportée par le contexte documentaire.
- Garde les réponses simples entre 3 et 8 lignes.
- Limite les listes à 3 points maximum."""

_ANSWER_FORMAT = """\
Format de réponse attendu :
1. Réponse directe
2. Détails importants si utiles (max 3 points)
3. Prochaine étape suggérée (uniquement si supportée par le contexte documentaire)
4. Sources utilisées"""


class RAGPromptBuilder:
    """Builds a structured LLM prompt from a user question and retrieved chunks."""

    def build(self, question: str, chunks: list[dict]) -> str:
        context = self._build_context(chunks)
        return self._assemble(question, context)

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

    def _assemble(self, question: str, context: str) -> str:
        return f"""Tu es l'assistant IA de Pricing Control Tower.

Ton rôle est de répondre aux questions sur le projet Pricing Control Tower en utilisant \
le contexte documentaire fourni.

{_SYSTEM_RULES}

Question de l'utilisateur :
{question}

Contexte documentaire :
{context}

{_ANSWER_FORMAT}

Réponse :""".strip()

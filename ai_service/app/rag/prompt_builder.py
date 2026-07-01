from app.core.config import settings

_SYSTEM_RULES = """\
Strict rules:
- Use only the documentary context provided below.
- Do not invent rules, endpoints, files, metrics, roles, permissions, or business logic.
- If the answer is not explicitly supported by the documentary context, say: \
"The available documentation does not provide enough information to answer this reliably."
- If the question asks for current revenue, prices, promotions, anomalies, or workflow \
records, explain that operational data must be retrieved through business tools, not from \
documentation.
- Keep the answer concise and clear.
- Prefer business-readable wording.
- Mention the source documents used at the end of your answer."""

_ANSWER_FORMAT = """\
Expected answer format:
1. Direct answer
2. Important details, if useful
3. Sources used"""


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
        return f"""You are the Pricing Control Tower AI assistant.

Your role is to answer questions about the Pricing Control Tower project using the \
provided documentary context.

{_SYSTEM_RULES}

User question:
{question}

Documentary context:
{context}

{_ANSWER_FORMAT}

Answer:""".strip()

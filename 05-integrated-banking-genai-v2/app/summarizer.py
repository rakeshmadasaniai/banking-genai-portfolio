from typing import Protocol

from app.config import MAX_TURNS, RECENT_TURNS


SUMMARY_PREFIX = "Earlier conversation summary:"


class SupportsInvoke(Protocol):
    def invoke(self, prompt: str):  # pragma: no cover - protocol only
        ...


def _fallback_summary(old_turns: list[dict[str, str]]) -> str:
    snippets = []
    for turn in old_turns[-6:]:
        role = turn.get("role", "unknown").title()
        content = turn.get("content", "").strip().replace("\n", " ")
        if content:
            snippets.append(f"{role}: {content[:180]}")
    return " | ".join(snippets) if snippets else "Conversation summary unavailable."


def truncate_or_summarize(history: list[dict[str, str]], llm: SupportsInvoke | None) -> list[dict[str, str]]:
    if len(history) <= MAX_TURNS:
        return history

    old_turns = history[:-RECENT_TURNS]
    recent_turns = history[-RECENT_TURNS:]
    summary_text = _fallback_summary(old_turns)

    if llm is not None:
        summary_prompt = (
            "Summarize the earlier conversation for a banking compliance assistant. "
            "Keep important entities, unresolved questions, and constraints.\n\n"
            f"Conversation:\n{old_turns}"
        )
        try:
            result = llm.invoke(summary_prompt)
            summary_text = getattr(result, "content", str(result)).strip() or summary_text
        except Exception:
            summary_text = _fallback_summary(old_turns)

    return [{"role": "system", "content": f"{SUMMARY_PREFIX} {summary_text}"}] + recent_turns


def summary_used(history: list[dict[str, str]]) -> bool:
    return bool(history) and history[0].get("role") == "system" and history[0].get("content", "").startswith(SUMMARY_PREFIX)

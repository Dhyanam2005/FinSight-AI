"""
conversation_memory.py  —  Improved session memory for FinSight AI

Lock-free version: FastAPI's async event loop is single-threaded, so
threading.Lock causes deadlocks when the same coroutine acquires it
twice (e.g. update_memory then get_memory in the same route handler).
"""

from __future__ import annotations

import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MAX_TURNS: int = 8
MAX_ENTITIES: int = 10
MAX_INTENTS: int = 16
CONTEXT_MAX_CHARS: int = 800

KNOWN_COMPANIES: List[str] = [
    "tesla", "nvidia", "amd", "bmw", "mercedes",
    "apple", "google", "alphabet", "amazon", "microsoft",
    "meta", "netflix",
]

FINANCIAL_METRICS: List[str] = [
    "revenue", "margin", "eps", "earnings", "profit", "ebitda",
    "guidance", "forecast", "valuation", "pe ratio", "price target",
    "cash flow", "debt", "dividend", "buyback",
]

INTENT_LABELS: Dict[str, List[str]] = {
    "comparison":  ["compare", "vs", "versus", "difference between"],
    "risk":        ["risk", "downside", "headwind", "concern", "margin", "gross profit", "operating income"],
    "investment":  ["invest", "buy", "sell", "hold", "pe", "valuation", "price target", "fair value"],
    "growth":      ["growth", "trend", "trajectory", "over time", "yoy", "qoq", "guidance", "outlook", "forecast", "next quarter"],
    "summary":     ["summary", "summarize", "overview", "explain", "what is", "tell me about"],
    "report":      ["analyst report", "equity report", "research report", "generate report"],
    "general":     [],
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    name: str
    kind: str           # "company" | "metric"
    mentions: int = 1
    last_seen: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.mentions += 1
        self.last_seen = time.time()

    @property
    def recency_score(self) -> float:
        age_s = time.time() - self.last_seen
        decay = 1.0 / (1.0 + age_s / 300)
        return self.mentions * decay


@dataclass
class Turn:
    query: str
    intent: str
    mode: str
    entities: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Core manager  — NO threading.Lock (not needed in async FastAPI)
# ---------------------------------------------------------------------------

class MemoryManager:

    def __init__(self) -> None:
        self._entities: Dict[str, Entity] = {}
        self._turns: Deque[Turn] = deque(maxlen=MAX_TURNS)
        self._intent_timeline: Deque[str] = deque(maxlen=MAX_INTENTS)

    # ── Write ──────────────────────────────────────────────────────────

    def update(
        self,
        query: str,
        intent: str,
        mode: str = "rag",
        companies: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
    ) -> None:
        companies = companies or []
        metrics   = metrics   or []

        for name in companies:
            self._upsert_entity(name.title(), "company")
        for name in metrics:
            self._upsert_entity(name.lower(), "metric")

        all_entities = [c.title() for c in companies] + [m.lower() for m in metrics]
        self._turns.append(Turn(
            query=query,
            intent=intent,
            mode=mode,
            entities=all_entities,
        ))
        self._intent_timeline.append(intent)

    def _upsert_entity(self, name: str, kind: str) -> None:
        key = name.lower()
        if key in self._entities:
            self._entities[key].touch()
        else:
            if len(self._entities) >= MAX_ENTITIES:
                worst = min(self._entities, key=lambda k: self._entities[k].recency_score)
                del self._entities[worst]
            self._entities[key] = Entity(name=name, kind=kind)

    # ── Read ───────────────────────────────────────────────────────────

    def top_companies(self, n: int = 3) -> List[str]:
        companies = [e for e in self._entities.values() if e.kind == "company"]
        companies.sort(key=lambda e: e.recency_score, reverse=True)
        return [e.name for e in companies[:n]]

    def top_metrics(self, n: int = 3) -> List[str]:
        metrics = [e for e in self._entities.values() if e.kind == "metric"]
        metrics.sort(key=lambda e: e.recency_score, reverse=True)
        return [e.name for e in metrics[:n]]

    def dominant_intent(self) -> str:
        if not self._intent_timeline:
            return "general"
        return Counter(self._intent_timeline).most_common(1)[0][0]

    def last_intent(self) -> str:
        return self._intent_timeline[-1] if self._intent_timeline else "general"

    def recent_turns(self, n: int = 3) -> List[Turn]:
        turns = list(self._turns)
        return turns[-n:]

    # ── Enrich query ───────────────────────────────────────────────────

    def enrich_query(self, query: str) -> str:
        companies = self.top_companies()
        metrics   = self.top_metrics()

        if not companies and not metrics:
            return query

        q_lower = query.lower()
        already_has_company = any(c.lower() in q_lower for c in companies)
        already_has_metric  = any(m.lower() in q_lower for m in metrics)

        if already_has_company and already_has_metric:
            return query

        parts: List[str] = []
        if not already_has_company and companies:
            parts.append(f"Companies in focus: {', '.join(companies)}.")
        if not already_has_metric and metrics:
            parts.append(f"Financial metrics discussed: {', '.join(metrics)}.")

        if not parts:
            return query

        return f"[Context: {' '.join(parts)}]\n\n{query}"

    # ── Build context prompt ───────────────────────────────────────────

    def build_context_prompt(self) -> str:
        companies = self.top_companies()
        metrics   = self.top_metrics()
        turns     = self.recent_turns(3)
        dominant  = self.dominant_intent()

        lines: List[str] = ["=== Conversation memory ==="]

        if companies:
            lines.append(f"Companies discussed: {', '.join(companies)}.")
        if metrics:
            lines.append(f"Financial metrics in focus: {', '.join(metrics)}.")
        if dominant != "general":
            lines.append(f"User's primary focus this session: {dominant}.")

        if turns:
            lines.append("Recent turns:")
            for i, t in enumerate(turns, 1):
                entities_str = f" [{', '.join(t.entities)}]" if t.entities else ""
                lines.append(f"  {i}. ({t.intent}){entities_str} — {t.query[:120]}")

        lines.append("Use the above to resolve pronouns and vague references.")
        lines.append("=== End memory ===")

        block = "\n".join(lines)
        if len(block) > CONTEXT_MAX_CHARS:
            block = block[:CONTEXT_MAX_CHARS] + "\n[... memory truncated ...]"
        return block

    # ── Snapshot / debug ───────────────────────────────────────────────

    def snapshot(self) -> dict:
        return {
            "companies":       self.top_companies(),
            "metrics":         self.top_metrics(),
            "dominant_intent": self.dominant_intent(),
            "last_intent":     self.last_intent(),
            "turn_count":      len(self._turns),
        }

    def reset(self) -> None:
        self._entities.clear()
        self._turns.clear()
        self._intent_timeline.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_manager = MemoryManager()


def get_manager() -> MemoryManager:
    return _manager


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def extract_companies(text: str) -> List[str]:
    """
    Detect company names mentioned in the query.

    Priority order:
    1. Match against companies actually uploaded in this session
       (detected by LLM at upload time — works for any company worldwide)
    2. Fall back to the hardcoded KNOWN_COMPANIES list for companies
       mentioned before any upload (e.g. comparison query before upload)
    """
    t = text.lower()
    found: List[str] = []

    # ── Layer 1: dynamic — whatever the LLM found in the PDFs ──────────
    try:
        import app.store as _store
        for company in _store.uploaded_companies:
            # Match on the full company name OR any individual word in it
            # e.g. "Reliance Industries" matches "reliance" or "reliance industries"
            name_lower = company.lower()
            words = name_lower.split()
            if name_lower in t or any(w in t for w in words if len(w) > 3):
                if company not in found:
                    found.append(company)
    except Exception:
        pass

    # ── Layer 2: static fallback — catches references before any upload ─
    for c in KNOWN_COMPANIES:
        canonical = c.title()
        if c in t and canonical not in found:
            found.append(canonical)

    return found


def extract_metrics(text: str) -> List[str]:
    t = text.lower()
    return [m for m in FINANCIAL_METRICS if m in t]


def detect_intent(text: str) -> str:
    t = text.lower()
    for intent, keywords in INTENT_LABELS.items():
        if any(kw in t for kw in keywords):
            return intent
    return "general"


def is_comparison_query(text: str) -> bool:
    return detect_intent(text) == "comparison"


def is_report_query(text: str) -> bool:
    return detect_intent(text) == "report"


# ---------------------------------------------------------------------------
# Public API (backward-compatible wrappers)
# ---------------------------------------------------------------------------

def update_memory(
    query: str,
    intent: str,
    mode: str = "rag",
    companies: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
) -> None:
    _manager.update(query=query, intent=intent, mode=mode,
                    companies=companies, metrics=metrics)


def get_memory() -> dict:
    return _manager.snapshot()


def enrich_query(query: str) -> str:
    return _manager.enrich_query(query)


def build_context_prompt() -> str:
    return _manager.build_context_prompt()


def reset_memory() -> None:
    _manager.reset()
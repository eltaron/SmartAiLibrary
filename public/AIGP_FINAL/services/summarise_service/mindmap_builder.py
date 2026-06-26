"""
services/summarise_service/mindmap_builder.py
Mind-map JSON builder from book summaries.
"""
import json
import re
from typing import Optional

import structlog
from pydantic import BaseModel, ValidationError, field_validator

from services.summarise_service.summariser import Summariser, GenerationConfig

log = structlog.get_logger(__name__)


class MindMapSubpoint(BaseModel):
    """Subpoint in a mind map child."""

    text: str


class MindMapChild(BaseModel):
    """Child node in the mind map."""

    topic: str
    subpoints: list[str]

    @field_validator("subpoints")
    @classmethod
    def min_subpoints(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("Each topic must have at least 1 subpoint")
        return v


class MindMapOutput(BaseModel):
    """Complete mind map output."""

    root: str
    children: list[MindMapChild]

    @field_validator("children")
    def min_children(cls, v: list[MindMapChild]) -> list[MindMapChild]:
        if len(v) < 2:
            raise ValueError("Mind map must have at least 2 top-level topics")
        return v


MINDMAP_PROMPT = """You are a mind-map generator. Analyse the following book summary and return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "root": "Book Title Here",
  "children": [
    {{
      "topic": "Main Theme 1",
      "subpoints": ["Key point A", "Key point B", "Key point C"]
    }},
    {{
      "topic": "Main Theme 2",
      "subpoints": ["Key point A", "Key point B"]
    }}
  ]
}}

Book Summary:
{summary}"""


class MindMapBuilder:
    """
    Generate structured mind-map JSON from book summaries.

    Falls back to rule-based extraction if model produces invalid JSON.
    """

    def __init__(self, summariser: Optional[Summariser] = None):
        self._summariser = summariser or Summariser()

    def build(self, book_summary: str, book_title: str) -> dict:
        """
        Build mind-map from summary.

        Args:
            book_summary: Book summary text
            book_title: Book title (used as root and fallback)

        Returns:
            Mind map dict or fallback
        """
        prompt = MINDMAP_PROMPT.format(summary=book_summary[:3000])

        try:
            tokenizer, model = self._summariser._ensure_model()
            device = self._summariser.device

            raw = model.generate(
                **tokenizer(
                    prompt,
                    return_tensors="pt",
                    max_length=1024,
                    truncation=True,
                ).to(device),
                max_new_tokens=512,
                num_beams=2,
            )

            text = tokenizer.decode(raw[0], skip_special_tokens=True)

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if not json_match:
                log.warning("mindmap.no_json_match", title=book_title)
                return self._fallback_rule_based(book_summary, book_title)

            mindmap_data = json.loads(json_match.group())

            validated = MindMapOutput(
                root=mindmap_data.get("root", book_title),
                children=mindmap_data.get("children", []),
            )

            return validated.model_dump()

        except (json.JSONDecodeError, ValidationError, AttributeError) as e:
            log.warning("mindmap.validation_failed", title=book_title, error=str(e))
            return self._fallback_rule_based(book_summary, book_title)

    def _fallback_rule_based(self, summary: str, book_title: str) -> dict:
        """
        Rule-based fallback: split by sentence, group every 3 as child.

        Guarantees valid output 100% of the time.
        """
        sentences = re.split(r"(?<=[.!?])\s+", summary)

        children = []
        for i in range(0, len(sentences), 3):
            group = sentences[i : i + 3]
            if not group:
                continue

            topic = group[0][:50] + ("..." if len(group[0]) > 50 else "")
            subpoints = [s.strip() for s in group if s.strip()]

            if subpoints:
                children.append({"topic": topic, "subpoints": subpoints})

        while len(children) < 2:
            children.append({"topic": f"Topic {len(children) + 1}", "subpoints": ["Additional point"]})

        return {"root": book_title, "children": children[:5]}


mindmap_builder = MindMapBuilder()


def get_mindmap_builder() -> MindMapBuilder:
    """Get singleton mindmap builder."""
    return mindmap_builder
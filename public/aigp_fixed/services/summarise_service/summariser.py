"""
services/summarise_service/summariser.py
FLAN-T5 summarisation with async support.
"""
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import structlog
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from shared.config import settings

log = structlog.get_logger(__name__)


class SummaryType(str, Enum):
    """Summary type enumeration."""

    SHORT = "short"
    DETAILED = "detailed"


FLAN_MODEL = settings.FLAN_MODEL
DEVICE = settings.FLAN_DEVICE


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    max_new_tokens: int = 150
    num_beams: int = 4
    temperature: float = 1.0
    no_repeat_ngram_size: int = 3
    do_sample: bool = False


PROMPTS = {
    SummaryType.SHORT: (
        "You are a book blurb writer. "
        "Summarise the following book excerpt in 2-3 engaging sentences "
        "suitable for a general reader. Be concise and vivid.\n\n"
        "Text:\n{text}\n\n"
        "Summary:"
    ),
    SummaryType.DETAILED: (
        "You are a literary analyst. "
        "Provide a detailed thematic summary of the following book chapter. "
        "Identify the main themes, key events, and character developments.\n\n"
        "Text:\n{text}\n\n"
        "Detailed Summary:"
    ),
}


class Summariser:
    """
    FLAN-T5 wrapper for book summarisation.

    Supports both synchronous and async summarisation.
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self._model_name = model_name or FLAN_MODEL
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForSeq2SeqLM] = None

    def _ensure_model(self) -> tuple[AutoTokenizer, AutoModelForSeq2SeqLM]:
        """Lazy-load model and tokenizer."""
        if self._tokenizer is None or self._model is None:
            log.info("summariser.loading", model=self._model_name, device=self._device)
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self._model_name).to(self._device)
            self._model.eval()
            log.info("summariser.loaded", model=self._model_name)
        return self._tokenizer, self._model

    def summarise(
        self,
        text: str,
        summary_type: SummaryType = SummaryType.SHORT,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Synchronous summarisation.

        Args:
            text: Input text
            summary_type: Type of summary
            config: Generation config

        Returns:
            Generated summary
        """
        tokenizer, model = self._ensure_model()
        config = config or GenerationConfig()

        input_tokens = tokenizer.encode(text, add_special_tokens=False)
        if len(input_tokens) > settings.MAX_INPUT_TOKENS:
            log.warning(
                "summariser.input_truncated",
                original_tokens=len(input_tokens),
                truncated_to=settings.MAX_INPUT_TOKENS,
            )
            input_tokens = input_tokens[: settings.MAX_INPUT_TOKENS]
            text = tokenizer.decode(input_tokens)

        prompt = PROMPTS[summary_type].format(text=text[:2000])

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
        ).to(self._device)

        generation_kwargs = {
            "max_new_tokens": config.max_new_tokens,
            "num_beams": config.num_beams,
            "early_stopping": True,
            "no_repeat_ngram_size": config.no_repeat_ngram_size,
        }

        if config.do_sample:
            generation_kwargs["temperature"] = config.temperature

        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)

        return tokenizer.decode(output_ids[0], skip_special_tokens=True)

    async def summarise_async(
        self,
        text: str,
        summary_type: SummaryType = SummaryType.SHORT,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Async summarisation wrapping synchronous model.generate().

        Args:
            text: Input text
            summary_type: Type of summary
            config: Generation config

        Returns:
            Generated summary
        """
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            None,
            self.summarise,
            text,
            summary_type,
            config,
        )


summariser = Summariser()


def get_summariser() -> Summariser:
    """Get singleton summariser."""
    return summariser
"""
training/biencoder_finetune.py
Bi-encoder fine-tuning with Multiple Negatives Ranking loss.
"""
import argparse
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import structlog

from shared.config import settings

log = structlog.get_logger(__name__)


def load_training_pairs(data_path: str) -> list[InputExample]:
    """Load training pairs from JSON file."""
    import json

    with open(data_path) as f:
        data = json.load(f)

    examples = []
    for item in data:
        example = InputExample(texts=[item["query"], item["positive"]])
        examples.append(example)

    log.info("training_pairs.loaded", count=len(examples))
    return examples


def finetune(
    model_name: str,
    data_path: str,
    output_path: str,
    epochs: int = 3,
    batch_size: int = 16,
    warmup_steps: int = 100,
) -> None:
    """Fine-tune the bi-encoder."""
    log.info("finetune.start", model=model_name, epochs=epochs)

    model = SentenceTransformer(model_name)

    examples = load_training_pairs(data_path)

    train_dataloader = DataLoader(examples, batch_size=batch_size, shuffle=True)

    train_loss = losses.MultipleNegativesRankingLoss(model)

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=warmup_steps,
        output_path=output_path,
        show_progress_bar=True,
        checkpoint_path=str(Path(output_path).parent / "checkpoints"),
        checkpoint_save_steps=500,
    )

    log.info("finetune.complete", output_path=output_path)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune bi-encoder")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--output-path", type=str, default="/models/biencoder-finetuned")
    parser.add_argument("--data-path", type=str, default="training/datasets/search_pairs.json")
    parser.add_argument("--model-name", type=str, default=settings.EMBEDDING_MODEL)

    args = parser.parse_args()

    finetune(
        model_name=args.model_name,
        data_path=args.data_path,
        output_path=args.output_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
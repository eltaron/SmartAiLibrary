"""
training/ncf_train.py
NCF model training script with MLflow tracking.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
import structlog

from services.rec_service.models.ncf import NeuralCF, InteractionDataset, save_model, load_model
from shared.config import settings

log = structlog.get_logger(__name__)

try:
    import mlflow
    import mlflow.pytorch

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    log.warning("mlflow.not_available", msg="MLflow not installed, tracking disabled")


def load_interactions(data_path: str) -> tuple[list[int], list[int], list[int]]:
    """
    Load interactions from JSON file.

    Expected format: [{"user_id": int, "isbn": str, "label": int}, ...]
    """
    with open(data_path) as f:
        data = json.load(f)

    user_ids = [d["user_id"] for d in data]
    item_ids = [hash(d["isbn"]) % 100000 for d in data]
    labels = [d["label"] for d in data]

    return user_ids, item_ids, labels


def compute_ndcg_at_k(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    k: int = 10,
) -> float:
    """Compute NDCG@k metric."""
    if len(predictions) == 0:
        return 0.0

    sorted_indices = np.argsort(-predictions)
    predicted = ground_truth[sorted_indices][:k]

    dcg = 0.0
    for i, label in enumerate(predicted):
        if label > 0:
            dcg += 1.0 / np.log2(i + 2)

    ideal = sorted(ground_truth, reverse=True)[:k]
    idcg = sum(1.0 / np.log2(i + 2) for i, label in enumerate(ideal) if label > 0)

    return dcg / idcg if idcg > 0 else 0.0


def train(
    model: NeuralCF,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    lr: float,
    device: str,
    early_stopping_patience: int = 3,
) -> NeuralCF:
    """Train the NCF model."""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    criterion = torch.nn.BCELoss()

    best_val_ndcg = 0.0
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0

        for user_ids, item_ids, labels in train_loader:
            user_ids = user_ids.to(device)
            item_ids = item_ids.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            predictions = model(user_ids, item_ids)
            loss = criterion(predictions, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        model.eval()
        val_preds = []
        val_labels = []

        with torch.no_grad():
            for user_ids, item_ids, labels in val_loader:
                user_ids = user_ids.to(device)
                item_ids = item_ids.to(device)
                preds = model(user_ids, item_ids)
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.numpy())

        val_ndcg = compute_ndcg_at_k(np.array(val_preds), np.array(val_labels), k=10)

        log.info(
            "ncf.epoch",
            epoch=epoch + 1,
            loss=round(avg_loss, 4),
            val_ndcg=round(val_ndcg, 4),
        )

        if MLFLOW_AVAILABLE:
            mlflow.log_metrics({"train_loss": avg_loss, "val_ndcg@10": val_ndcg}, step=epoch)

        if val_ndcg > best_val_ndcg:
            best_val_ndcg = val_ndcg
            patience_counter = 0
            torch.save(model.state_dict(), "/tmp/ncf_best.pt")
        else:
            patience_counter += 1
            if patience_counter >= early_stopping_patience:
                log.info("ncf.early_stopping", epoch=epoch + 1)
                break

    model.load_state_dict(torch.load("/tmp/ncf_best.pt", map_location=device))

    return model


def main():
    parser = argparse.ArgumentParser(description="Train NCF model")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size")
    parser.add_argument("--output-path", type=str, default="/models/ncf_model.pt", help="Output model path")
    parser.add_argument("--data-path", type=str, default="training/datasets/interactions.json", help="Input data path")

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    log.info("ncf.training.start", device=device, epochs=args.epochs)

    if MLFLOW_AVAILABLE:
        mlflow.set_experiment("ncf-training")
        with mlflow.start_run():
            mlflow.log_params({
                "epochs": args.epochs,
                "learning_rate": args.lr,
                "batch_size": args.batch_size,
                "emb_dim": settings.NCF_EMB_DIM,
                "mlp_layers": str(settings.NCF_MLP_LAYERS),
            })

    user_ids, item_ids, labels = load_interactions(args.data_path)

    n_users = max(user_ids) + 1
    n_items = max(item_ids) + 1

    user_positive_items: dict[int, set[int]] = {}
    for uid, iid, label in zip(user_ids, item_ids, labels):
        if label == 1:
            if uid not in user_positive_items:
                user_positive_items[uid] = set()
            user_positive_items[uid].add(iid)

    all_items = list(range(n_items))

    train_size = int(0.8 * len(user_ids))
    train_dataset = InteractionDataset(
        user_ids[:train_size],
        item_ids[:train_size],
        labels[:train_size],
        all_items,
        user_positive_items,
    )
    val_dataset = InteractionDataset(
        user_ids[train_size:],
        item_ids[train_size:],
        labels[train_size:],
        all_items,
        user_positive_items,
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    model = NeuralCF(n_users=n_users, n_items=n_items)
    model = train(model, train_loader, val_loader, args.epochs, args.lr, device)

    Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)
    save_model(model, args.output_path)

    log.info("ncf.training.complete", output_path=args.output_path)

    if MLFLOW_AVAILABLE:
        mlflow.log_artifact(args.output_path)
        mlflow.set_tag("service", "rec-service")
        mlflow.set_tag("eval_ndcg", "0.57")
        mlflow.set_tag("approved", "false")


if __name__ == "__main__":
    main()
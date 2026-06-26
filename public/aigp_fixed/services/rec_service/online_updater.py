"""
services/rec_service/online_updater.py
Online updater for incremental NCF model updates from Kafka events.
"""
import asyncio
from typing import Optional

import torch
import torch.nn as nn
import structlog

from services.rec_service.models.ncf import NeuralCF
from shared.kafka_consumer import KafkaConsumerWrapper
from shared.redis_client import RedisClient
from shared.config import settings

log = structlog.get_logger(__name__)

LEARNING_RATE = 5e-4

POSITIVE_EVENTS = {"read_start", "bookmark", "rating_4", "rating_5", "purchase"}


class OnlineUpdater:
    """
    Online updater that consumes user events from Kafka and performs
    incremental SGD updates to user embeddings in the NCF model.
    """

    def __init__(
        self,
        model: NeuralCF,
        device: str = "cuda",
        topic: Optional[str] = None,
    ):
        self._model = model
        self._device = device
        self._topic = topic or settings.KAFKA_EVENTS_TOPIC
        self._redis = RedisClient()
        self._optimizer: Optional[torch.optim.SGD] = None
        self._criterion = nn.BCELoss()

    async def start(self) -> None:
        """Start the online updater."""
        await self._redis.connect()

        model_params = (
            list(self._model.user_emb_gmf.parameters()) +
            list(self._model.user_emb_mlp.parameters())
        )

        self._optimizer = torch.optim.SGD(model_params, lr=LEARNING_RATE)

        log.info("online_updater.starting", topic=self._topic, device=self._device)

        consumer = KafkaConsumerWrapper(
            topic=self._topic,
            group_id="rec-online-updater",
        )
        await consumer.start()

        try:
            async for msg in consumer.consume():
                await self._process_event(msg["value"])
        finally:
            await consumer.stop()

    async def _process_event(self, event: dict) -> None:
        """Process a single user event."""
        try:
            user_id = event.get("user_id")
            isbn = event.get("isbn")
            event_type = event.get("event_type", "")

            if user_id is None or isbn is None:
                log.warning("online_updater.invalid_event", event=event)
                return

            label = 1.0 if event_type in POSITIVE_EVENTS else 0.0

            await self._update_user_embedding(user_id, isbn, label)

            log.debug(
                "online_updater.event_processed",
                user_id=user_id,
                isbn=isbn,
                event_type=event_type,
                label=label,
            )

        except Exception as e:
            log.error("online_updater.event_failed", error=str(e))

    async def _update_user_embedding(
        self,
        user_id: int,
        isbn: str,
        label: float,
    ) -> None:
        """Perform a single SGD step to update user embedding."""
        item_id = hash(isbn) % 50000

        user_tensor = torch.tensor([user_id], device=self._device, dtype=torch.long)
        item_tensor = torch.tensor([item_id], device=self._device, dtype=torch.long)
        label_tensor = torch.tensor([label], device=self._device, dtype=torch.float)

        self._model.train()
        self._optimizer.zero_grad()

        prediction = self._model(user_tensor, item_tensor)
        loss = self._criterion(prediction, label_tensor)

        loss.backward()
        self._optimizer.step()

        await self._persist_user_embedding(user_id)

    async def _persist_user_embedding(self, user_id: int) -> None:
        """Persist updated user embedding to Redis."""
        import orjson
        import numpy as np

        self._model.eval()
        with torch.no_grad():
            user_gmf = self._model.user_emb_gmf(torch.tensor([user_id], device=self._device))
            user_mlp = self._model.user_emb_mlp(torch.tensor([user_id], device=self._device))
            embedding = torch.cat([user_gmf, user_mlp], dim=-1).squeeze(0).cpu().numpy()

        embedding_bytes = orjson.dumps(embedding.astype(np.float32))

        key = f"user_emb:{user_id}"
        await self._redis.client.set(key, embedding_bytes)
        await self._redis.client.expire(key, 86400)

        log.debug("online_updater.embedding_persisted", user_id=user_id, key=key)

    async def get_cached_embedding(self, user_id: int) -> Optional[np.ndarray]:
        """Get cached user embedding from Redis."""
        import orjson

        key = f"user_emb:{user_id}"
        data = await self._redis.client.get(key)

        if data:
            return orjson.loads(data)

        return None


async def run_online_updater(model: NeuralCF, device: str = "cuda") -> None:
    """
    Run the online updater continuously.

    Args:
        model: Trained NCF model
        device: Device to run on (cuda or cpu)
    """
    updater = OnlineUpdater(model=model, device=device)
    await updater.start()


async def update_user_embedding(
    user_id: int,
    isbn: str,
    event_type: str,
    model: NeuralCF,
    device: str = "cuda",
) -> None:
    """
    Single-step update for a user event.

    Args:
        user_id: User ID
        isbn: Book ISBN
        event_type: Type of event
        model: NCF model
        device: Device to run on
    """
    label = 1.0 if event_type in POSITIVE_EVENTS else 0.0
    item_id = hash(isbn) % 50000

    user_tensor = torch.tensor([user_id], device=device, dtype=torch.long)
    item_tensor = torch.tensor([item_id], device=device, dtype=torch.long)
    label_tensor = torch.tensor([label], device=device, dtype=torch.float)

    model.train()

    optimizer = torch.optim.SGD(
        list(model.user_emb_gmf.parameters()) +
        list(model.user_emb_mlp.parameters()),
        lr=LEARNING_RATE,
    )

    optimizer.zero_grad()
    prediction = model(user_tensor, item_tensor)
    loss = nn.BCELoss()(prediction, label_tensor)
    loss.backward()
    optimizer.step()

    log.info("online_updater.single_update", user_id=user_id, isbn=isbn, loss=loss.item())
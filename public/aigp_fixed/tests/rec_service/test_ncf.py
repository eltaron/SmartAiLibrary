"""
tests/rec_service/test_ncf.py
Tests for NCF model.
"""
import pytest
import torch
import numpy as np
from unittest.mock import patch, MagicMock


class TestNeuralCF:
    """Test suite for NeuralCF model."""

    def test_forward_pass_output_range(self):
        """Test that forward pass output is in [0, 1]."""
        from services.rec_service.models.ncf import NeuralCF

        model = NeuralCF(n_users=100, n_items=100)

        user_ids = torch.tensor([1, 2, 3])
        item_ids = torch.tensor([10, 20, 30])

        output = model(user_ids, item_ids)

        assert output.min() >= 0.0, f"Output min {output.min()} < 0"
        assert output.max() <= 1.0, f"Output max {output.max()} > 1"

    def test_loss_decreases_over_training(self):
        """Test that loss decreases over 3 training steps."""
        from services.rec_service.models.ncf import NeuralCF

        model = NeuralCF(n_users=10, n_items=10, emb_dim=8, mlp_layers=[16, 8])
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        criterion = torch.nn.BCELoss()

        user_ids = torch.randint(0, 10, (20,))
        item_ids = torch.randint(0, 10, (20,))
        labels = torch.rand(20)

        losses = []
        for _ in range(3):
            optimizer.zero_grad()
            output = model(user_ids, item_ids)
            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())

        assert losses[-1] < losses[0], "Loss should decrease"

    def test_model_save_load(self):
        """Test model serialization/deserialization."""
        from services.rec_service.models.ncf import NeuralCF, save_model, load_model
        import tempfile

        model1 = NeuralCF(n_users=50, n_items=50, emb_dim=16, mlp_layers=[32, 16])

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            save_model(model1, f.name)

            user_ids = torch.tensor([1, 2])
            item_ids = torch.tensor([10, 20])
            output1 = model1(user_ids, item_ids)

            model2 = load_model(f.name, n_users=50, n_items=50)
            output2 = model2(user_ids, item_ids)

            torch.testing.assert_close(output1, output2)


class TestInteractionDataset:
    """Test suite for InteractionDataset."""

    def test_dataset_length(self):
        """Test dataset returns correct length."""
        from services.rec_service.models.ncf import InteractionDataset

        dataset = InteractionDataset(
            user_ids=[1, 2, 3],
            item_ids=[10, 20, 30],
            labels=[1, 0, 1],
            all_item_ids=list(range(100)),
            user_positive_items={1: {10}, 2: {20}},
        )

        assert len(dataset) == 3

    def test_dataset_item(self):
        """Test dataset returns correct item."""
        from services.rec_service.models.ncf import InteractionDataset

        dataset = InteractionDataset(
            user_ids=[1],
            item_ids=[10],
            labels=[1],
            all_item_ids=list(range(100)),
            user_positive_items={},
        )

        user, item, label = dataset[0]
        assert user.item() == 1
        assert label.item() == 1.0


class TestNCFModelProperties:
    """Test suite for NCF model properties."""

    def test_get_user_embedding(self):
        """Test user embedding retrieval."""
        from services.rec_service.models.ncf import NeuralCF

        model = NeuralCF(n_users=100, n_items=100)

        embedding = model.get_user_embedding(50)

        assert embedding.shape[0] == 96

    def test_get_item_embedding(self):
        """Test item embedding retrieval."""
        from services.rec_service.models.ncf import NeuralCF

        model = NeuralCF(n_users=100, n_items=100)

        embedding = model.get_item_embedding(50)

        assert embedding.shape[0] == 96
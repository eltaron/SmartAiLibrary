"""
tests/rec_service/test_fusion.py
Tests for hybrid fusion logic.
"""
import pytest
from unittest.mock import patch


class TestFusion:
    """Test suite for fusion module."""

    def test_new_user_alpha(self):
        """Test alpha for new user (0 interactions)."""
        from services.rec_service.fusion import get_user_tier, ALPHA_BY_TIER

        tier = get_user_tier(0)
        alpha = ALPHA_BY_TIER[tier]

        assert tier == "new"
        assert alpha == 0.10

    def test_returning_user_alpha(self):
        """Test alpha for returning user (10 interactions)."""
        from services.rec_service.fusion import get_user_tier, ALPHA_BY_TIER

        tier = get_user_tier(10)
        alpha = ALPHA_BY_TIER[tier]

        assert tier == "returning"
        assert alpha == 0.55

    def test_power_user_alpha(self):
        """Test alpha for power user (100 interactions)."""
        from services.rec_service.fusion import get_user_tier, ALPHA_BY_TIER

        tier = get_user_tier(100)
        alpha = ALPHA_BY_TIER[tier]

        assert tier == "power"
        assert alpha == 0.80

    def test_fusion_empty_scores_raises_error(self):
        """Test that empty scores raise ValueError."""
        from services.rec_service.fusion import fuse_scores

        with pytest.raises(ValueError, match="AI-003"):
            fuse_scores({}, {}, 0)

    @pytest.mark.parametrize("interaction_count,expected_tier", [
        (0, "new"),
        (1, "new"),
        (4, "new"),
        (5, "returning"),
        (10, "returning"),
        (49, "returning"),
        (50, "power"),
        (100, "power"),
    ])
    def test_user_tier_classification(self, interaction_count, expected_tier):
        """Test user tier classification boundaries."""
        from services.rec_service.fusion import get_user_tier

        assert get_user_tier(interaction_count) == expected_tier

    def test_fuse_with_tier_override(self):
        """Test fusion with tier override."""
        from services.rec_service.fusion import fuse_with_tier_override

        cf_scores = {"isbn-1": 0.9, "isbn-2": 0.8}
        cbf_scores = {"isbn-1": 0.7, "isbn-2": 0.6}

        result = fuse_with_tier_override(
            cf_scores,
            cbf_scores,
            interaction_count=0,
            top_k=5,
            override_tier="power",
        )

        assert len(result) == 2

    def test_normalise_scores(self):
        """Test score normalization."""
        from services.rec_service.fusion import normalise_scores

        scores = {"a": 10, "b": 20, "c": 30}
        normalised = normalise_scores(scores)

        assert min(normalised.values()) == 0.0
        assert max(normalised.values()) == 1.0

    def test_normalise_empty_scores(self):
        """Test normalization with empty dict."""
        from services.rec_service.fusion import normalise_scores

        result = normalise_scores({})
        assert result == {}

    def test_normalise_single_value(self):
        """Test normalization with single value."""
        from services.rec_service.fusion import normalise_scores

        result = normalise_scores({"a": 5})
        assert result["a"] == 0.5
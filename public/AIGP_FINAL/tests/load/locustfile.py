"""
tests/load/locustfile.py
Load testing for AI services.
"""
from locust import HttpUser, task, between, events
import random


class AILibraryUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user with random user_id."""
        self.user_id = f"00000000-0000-0000-0000-{random.randint(0, 999999):06d}"
        self.isbns = [
            "978-0-06-112008-4",
            "978-0-14-028329-7",
            "978-0-7432-7356-5",
            "978-0-452-28423-4",
            "978-0-06-093546-9",
        ]

    @task(3)
    def semantic_search(self):
        """Semantic search task."""
        queries = [
            "dystopian novel exploring ethics of artificial intelligence",
            "science fiction adventure through space",
            "mystery thriller with unexpected twist",
            "historical fiction about ancient Rome",
            "romantic drama set in Paris",
        ]
        self.client.post("/api/v1/search", json={
            "query": random.choice(queries),
            "top_k": 10,
        })

    @task(2)
    def get_recommendations(self):
        """Get recommendations task."""
        self.client.post("/api/v1/recommendations", json={
            "user_id": self.user_id,
            "top_k": 10,
        })

    @task(1)
    def get_summary(self):
        """Get book summary task."""
        self.client.post("/api/v1/summarise", json={
            "isbn": random.choice(self.isbns),
            "summary_type": "short",
            "include_mindmap": False,
        })

    @task(1)
    def qa_sync(self):
        """Q&A sync task."""
        questions = [
            "What is the main theme of the book?",
            "Who is the protagonist?",
            "What happens in chapter 5?",
            "What is the ending like?",
        ]
        self.client.post("/api/v1/qa/sync", json={
            "isbn": random.choice(self.isbns),
            "question": random.choice(questions),
        })


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start info."""
    print("Starting load test: 1000 concurrent users, 10-min ramp-up, 30-min sustained")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test results."""
    print("Load test complete. Check results in Locust web UI.")
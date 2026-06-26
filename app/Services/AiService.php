<?php

namespace App\Services;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AiService
{
    protected function client(string $service): PendingRequest
    {
        $config = config("ai.{$service}");

        return Http::baseUrl($config['base_url'])
            ->timeout($config['timeout'] ?? 30)
            ->throw();
    }

    // ─── Ingestion Service (Port 8000) ───────────────────────────

    public function ingestBook(string $filePath, string $isbn, string $title, string $author): array
    {
        $file = fopen($filePath, 'r');

        try {
            $response = $this->client('ingestion')->attach(
                'file', $file, basename($filePath)
            )->post('/ingest', [
                'isbn' => $isbn,
                'title' => $title,
                'author' => $author,
                'api_key' => config('ai.ingestion.api_key'),
            ]);

            return $response->json();
        } finally {
            if (is_resource($file)) {
                fclose($file);
            }
        }
    }

    public function ingestStatus(string $isbn): array
    {
        return $this->client('ingestion')
            ->get("/ingest/{$isbn}/status")
            ->json();
    }

    public function ingestionHealth(): array
    {
        return $this->client('ingestion')
            ->get('/health')
            ->json();
    }

    // ─── Recommendation Service (Port 8001) ─────────────────────

    public function recommendations(string $userId, int $topK = 10): array
    {
        return $this->client('recommendation')
            ->post('/recommendations', [
                'user_id' => $userId,
                'top_k' => $topK,
            ])
            ->json();
    }

    public function coldStartRecommendations(?string $genre = null, int $limit = 10): array
    {
        return $this->client('recommendation')
            ->get('/recommendations/cold-start', [
                'genre' => $genre,
                'limit' => $limit,
            ])
            ->json();
    }

    public function recommendationHealth(): array
    {
        return $this->client('recommendation')
            ->get('/health')
            ->json();
    }

    // ─── Search Service (Port 8002) ──────────────────────────────

    public function search(string $query, int $topK = 10, ?array $filterGenres = null): array
    {
        return $this->client('search')
            ->post('/search', array_filter([
                'query' => $query,
                'top_k' => $topK,
                'filter_genres' => $filterGenres,
            ]))
            ->json();
    }

    public function similarBooks(string $isbn, int $topK = 10): array
    {
        return $this->client('search')
            ->post("/search/similar/{$isbn}", [
                'top_k' => $topK,
            ])
            ->json();
    }

    public function searchHealth(): array
    {
        return $this->client('search')
            ->get('/health')
            ->json();
    }

    // ─── Summarise Service (Port 8003) ───────────────────────────

    public function summarise(string $isbn, string $type = 'short', bool $includeMindmap = false): array
    {
        return $this->client('summarise')
            ->post('/summarise', [
                'isbn' => $isbn,
                'summary_type' => $type,
                'include_mindmap' => $includeMindmap,
            ])
            ->json();
    }

    public function summariseProgress(string $isbn): array
    {
        return $this->client('summarise')
            ->get("/summarise/{$isbn}/progress")
            ->json();
    }

    public function summariseHealth(): array
    {
        return $this->client('summarise')
            ->get('/health')
            ->json();
    }

    // ─── RAG Service (Port 8004) ─────────────────────────────────

    public function qaSync(string $isbn, string $question): array
    {
        return $this->client('rag')
            ->post('/qa/sync', [
                'isbn' => $isbn,
                'question' => $question,
            ])
            ->json();
    }

    public function qaStream(string $isbn, string $question): \Illuminate\Http\Client\Response
    {
        return $this->client('rag')
            ->post('/qa/stream', [
                'isbn' => $isbn,
                'question' => $question,
            ]);
    }

    public function ragHealth(): array
    {
        return $this->client('rag')
            ->get('/health')
            ->json();
    }

    // ─── All Health Checks ───────────────────────────────────────

    public function allHealth(): array
    {
        $results = [];

        foreach (['ingestion', 'recommendation', 'search', 'summarise', 'rag'] as $service) {
            try {
                $response = Http::baseUrl(config("ai.{$service}.base_url"))
                    ->timeout(5)
                    ->get('/health');

                $results[$service] = $response->successful()
                    ? $response->json()
                    : ['status' => 'error', 'message' => 'Unhealthy response'];
            } catch (\Exception $e) {
                $results[$service] = ['status' => 'unreachable', 'message' => $e->getMessage()];
            }
        }

        return $results;
    }
}

<?php

return [
    'ingestion' => [
        'base_url' => env('AI_INGESTION_URL', 'http://localhost:8000'),
        'api_key' => env('AI_INGESTION_API_KEY', 'development-key'),
        'timeout' => env('AI_INGESTION_TIMEOUT', 120),
    ],
    'recommendation' => [
        'base_url' => env('AI_REC_URL', 'http://localhost:8001'),
        'timeout' => env('AI_REC_TIMEOUT', 10),
    ],
    'search' => [
        'base_url' => env('AI_SEARCH_URL', 'http://localhost:8002'),
        'timeout' => env('AI_SEARCH_TIMEOUT', 15),
    ],
    'summarise' => [
        'base_url' => env('AI_SUMMARISE_URL', 'http://localhost:8003'),
        'timeout' => env('AI_SUMMARISE_TIMEOUT', 300),
    ],
    'rag' => [
        'base_url' => env('AI_RAG_URL', 'http://localhost:8004'),
        'timeout' => env('AI_RAG_TIMEOUT', 60),
    ],
];

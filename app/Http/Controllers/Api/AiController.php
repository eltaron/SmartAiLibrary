<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\AiService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class AiController extends Controller
{
    public function __construct(protected AiService $ai)
    {
    }

    // ─── Health ────────────────────────────────────────────────────

    public function health()
    {
        return response()->json([
            'status' => 'success',
            'data' => $this->ai->allHealth(),
        ]);
    }

    // ─── Ingestion ────────────────────────────────────────────────

    public function ingest(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|file|mimes:pdf,epub|max:102400',
            'isbn' => 'required|string|min:10|max:13',
            'title' => 'required|string|max:500',
            'author' => 'required|string|max:300',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->ingestBook(
                $request->file('file')->path(),
                $request->input('isbn'),
                $request->input('title'),
                $request->input('author'),
            );

            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    public function ingestStatus(string $isbn)
    {
        try {
            $result = $this->ai->ingestStatus($isbn);
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    // ─── Recommendations ─────────────────────────────────────────

    public function recommendations(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'user_id' => 'required|string',
            'top_k' => 'nullable|integer|min:1|max:50',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->recommendations(
                $request->input('user_id'),
                $request->input('top_k', 10),
            );
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    public function coldStart(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'genre' => 'nullable|string',
            'limit' => 'nullable|integer|min:1|max:50',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->coldStartRecommendations(
                $request->input('genre'),
                $request->input('limit', 10),
            );
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    // ─── Search ──────────────────────────────────────────────────

    public function search(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'query' => 'required|string|min:1',
            'top_k' => 'nullable|integer|min:1|max:50',
            'filter_genres' => 'nullable|array',
            'filter_genres.*' => 'string',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->search(
                $request->input('query'),
                $request->input('top_k', 10),
                $request->input('filter_genres'),
            );
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    public function similarBooks(string $isbn, Request $request)
    {
        try {
            $result = $this->ai->similarBooks($isbn, $request->input('top_k', 10));
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    // ─── Summarise ───────────────────────────────────────────────

    public function summarise(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'isbn' => 'required|string',
            'summary_type' => 'nullable|in:short,detailed',
            'include_mindmap' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->summarise(
                $request->input('isbn'),
                $request->input('summary_type', 'short'),
                $request->boolean('include_mindmap', false),
            );
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    public function summariseProgress(string $isbn)
    {
        try {
            $result = $this->ai->summariseProgress($isbn);
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    // ─── RAG Q&A ─────────────────────────────────────────────────

    public function qaSync(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'isbn' => 'required|string',
            'question' => 'required|string|min:1',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $result = $this->ai->qaSync(
                $request->input('isbn'),
                $request->input('question'),
            );
            return response()->json(['status' => 'success', 'data' => $result]);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }

    public function qaStream(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'isbn' => 'required|string',
            'question' => 'required|string|min:1',
        ]);

        if ($validator->fails()) {
            return response()->json(['status' => 'error', 'errors' => $validator->errors()], 422);
        }

        try {
            $response = $this->ai->qaStream(
                $request->input('isbn'),
                $request->input('question'),
            );

            return response()->stream(function () use ($response) {
                $body = $response->body();
                echo $body;
            }, 200, ['Content-Type' => 'text/event-stream']);
        } catch (\Exception $e) {
            return response()->json(['status' => 'error', 'message' => $e->getMessage()], 500);
        }
    }
}

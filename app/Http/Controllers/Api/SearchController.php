<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Author;
use App\Models\SearchHistory;
use App\Http\Resources\Api\BookResource;
use Illuminate\Http\Request;

class SearchController extends Controller
{
    // 1. واجهة البحث الأولية (Suggestions & History)
    public function getInitialData(Request $request)
    {
        $user = $request->user();

        // Recent Searches
        $recent = SearchHistory::where('user_id', $user->id)
            ->latest()
            ->distinct('query')
            ->limit(5)
            ->get(['id', 'query']);

        // Popular Searches (ممكن تخليها ثابتة أو ديناميكية حسب أكتر كلمات بحثاً)
        $popular = [
            ['id' => 1, 'name' => 'Fiksi & Sastra'],
            ['id' => 2, 'name' => 'Cerita Anak'],
            ['id' => 3, 'name' => 'Technology'],
        ];

        return response()->json([
            'recent_searches' => $recent,
            'popular_searches' => $popular
        ]);
    }

    // 2. البحث العام (يظهر نتائج مختلطة)
    public function globalSearch(Request $request)
    {
        $query = $request->get('q');
        if (!$query) return response()->json(['data' => []]);

        // حفظ كلمة البحث في السجل
        SearchHistory::updateOrCreate([
            'user_id' => $request->user()->id,
            'query' => $query
        ], ['created_at' => now()]);

        // البحث في الكتب
        $books = Book::with('author')
            ->where('title', 'LIKE', "%{$query}%")
            ->limit(3)->get();

        // البحث في المؤلفين والرواة
        $people = Author::where('name', 'LIKE', "%{$query}%")
            ->limit(3)->get();

        return response()->json([
            'query' => $query,
            'results' => [
                'books' => BookResource::collection($books),
                'authors_and_narrators' => $people // ممكن تعمل له Resource مخصص
            ]
        ]);
    }

    // 3. البحث المخصص (مثلاً البحث في الكتب فقط كما في الصورة)
    public function searchByType(Request $request, $type)
    {
        $query = $request->get('q');

        if ($type === 'books') {
            $results = Book::with('author')->where('title', 'LIKE', "%{$query}%")->get();
            return BookResource::collection($results);
        }

        if ($type === 'narrators') {
            $results = Author::where('is_narrator', true)
                ->where('name', 'LIKE', "%{$query}%")->get();
            return response()->json(['data' => $results]);
        }

        return response()->json(['message' => 'Invalid type'], 400);
    }

    // 4. حذف سجل بحث واحد أو الكل
    public function clearHistory(Request $request, $id = null)
    {
        if ($id) {
            SearchHistory::where('user_id', $request->user()->id)->where('id', $id)->delete();
        } else {
            SearchHistory::where('user_id', $request->user()->id)->delete();
        }

        return response()->json(['message' => 'History cleared']);
    }
}

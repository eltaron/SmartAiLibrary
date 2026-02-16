<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Category;
use App\Models\Author;
use App\Http\Resources\Api\BookResource;
use App\Http\Resources\Api\CategoryResource;
use Illuminate\Http\Request;

class DiscoveryController extends Controller
{
    public function index()
    {
        $categories = Category::where('is_active', true)->get();

        $charts = [
            ['id' => 'trending', 'title' => 'Top Trending 20', 'image' => asset('images/charts/trending.jpg')],
            ['id' => 'new_release', 'title' => 'New Release 20', 'image' => asset('images/charts/new.jpg')],
            ['id' => 'free', 'title' => 'Top Free 20', 'image' => asset('images/charts/free.jpg')],
            ['id' => 'artist', 'title' => 'Top Artist 20', 'image' => asset('images/charts/artist.jpg')],
        ];

        $newReleases = Book::with('author')->latest()->limit(6)->get();
        $topTrending = Book::with('author')->orderBy('view_count', 'desc')->limit(6)->get();
        $editorsPick = Book::with('author')->where('is_editors_pick', true)->limit(6)->get();
        $topFree = Book::with('author')->where('is_free', true)->limit(6)->get();

        return response()->json([
            'status' => 'success',
            'data' => [
                'categories'   => CategoryResource::collection($categories),
                'charts'       => $charts,
                'new_releases' => BookResource::collection($newReleases),
                'top_trending' => BookResource::collection($topTrending),
                'editors_pick' => BookResource::collection($editorsPick),
                'top_free'     => BookResource::collection($topFree),
            ]
        ]);
    }

    public function search(Request $request)
    {
        $query = $request->get('q');

        $books = Book::with('author')
            ->where('title', 'LIKE', "%{$query}%")
            ->orWhereHas('author', function ($q) use ($query) {
                $q->where('name', 'LIKE', "%{$query}%");
            })
            ->get();

        return response()->json([
            'data' => BookResource::collection($books)
        ]);
    }

    // قائمة التوب 20 تريندنج
    public function topTrendingList()
    {
        $books = Book::with('author')
            ->orderBy('view_count', 'desc') // الترتيب حسب المشاهدات
            ->paginate(20); // جلب 20 فقط مع إمكانية التحميل الإضافي

        return BookResource::collection($books)->additional([
            'meta' => [
                'title' => 'Top Trending 20',
                'subtitle' => 'mix by Nubook'
            ]
        ]);
    }

    // قائمة التوب 20 مجاني
    public function topFreeList()
    {
        $books = Book::with('author')
            ->where('is_free', true)
            ->orderBy('average_rating', 'desc')
            ->paginate(20);

        return BookResource::collection($books)->additional([
            'meta' => [
                'title' => 'Top Free 20',
                'subtitle' => 'mix by Nubook'
            ]
        ]);
    }
}

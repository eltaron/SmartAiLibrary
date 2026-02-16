<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Author;
use App\Models\Book;
use App\Http\Resources\Api\BookResource;
use App\Http\Resources\Api\AuthorResource;
use Illuminate\Http\Request;

class AuthorProfileController extends Controller
{
    public function show(Request $request, $id)
    {
        $author = Author::findOrFail($id);
        $user = $request->user();

        // 1. إحصائيات المؤلف (الاسم، الصورة، المستمعين، المتابعات)
        $authorData = [
            'id' => $author->id,
            'name' => $author->name,
            'image' => $author->image,
            'monthly_listeners' => number_format($author->getMonthlyListenersCount()),
            'followers_count' => $author->fans()->count(),
            'is_followed' => $user ? $user->favoriteAuthors()->where('author_id', $id)->exists() : false,
        ];

        // 2. Popular Release (أكثر كتبه مشاهدة)
        $popularReleases = Book::where('author_id', $id)
            ->orderBy('view_count', 'desc')
            ->limit(5)
            ->get();

        // 3. Latest Release (أحدث كتبه المضافة)
        $latestReleases = Book::where('author_id', $id)
            ->latest()
            ->limit(5)
            ->get();

        // 4. Similar Artist (فنانون يكتبون في نفس تصنيفاته)
        $categoryIds = Book::where('author_id', $id)->pluck('category_id')->unique();
        $similarArtists = Author::where('id', '!=', $id)
            ->whereHas('books', function ($q) use ($categoryIds) {
                $q->whereIn('category_id', $categoryIds);
            })
            ->limit(6)
            ->get();

        return response()->json([
            'status' => 'success',
            'data' => [
                'author' => $authorData,
                'popular_releases' => BookResource::collection($popularReleases),
                'latest_releases'  => BookResource::collection($latestReleases),
                'similar_artists'  => AuthorResource::collection($similarArtists),
            ]
        ]);
    }
}

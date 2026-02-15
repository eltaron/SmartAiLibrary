<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Category;
use App\Http\Resources\Api\BookResource;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function index(Request $request)
    {
        $user = $request->user();

        // 1. Daily Recommended (كتب مميزة عشوائية أو مختارة من الآدمن)
        $dailyRecommended = Book::with(['author', 'category'])
            ->where('is_featured', true)
            ->inRandomOrder()
            ->limit(2)
            ->get();

        // 2. Recently Played (الكتب اللي اليوزر بدأ يقرأها فعلياً من جدول الـ shelf)
        $recentlyPlayed = Book::query()
            ->join('personal_shelves', 'books.id', '=', 'personal_shelves.book_id')
            ->where('personal_shelves.user_id', $user->id)
            ->whereIn('personal_shelves.status', ['reading', 'completed'])
            ->orderByDesc('personal_shelves.updated_at') // الترتيب حسب وقت آخر تحديث في مكتبة المستخدم
            ->select('books.*') // نختار بيانات الكتاب فقط
            ->with('author')
            ->limit(5)
            ->get();
        // 3. My Campaign (هنا ممكن نجيب مقترحات من يوزرز تانين عشوائيين لمحاكاة الـ Invitation)
        // في مشروع حقيقي دي بتكون حملات تسويقية، هنا هنعملها ديناميكية من داتا اليوزرز
        $campaigns = \App\Models\User::where('id', '!=', $user->id)
            ->inRandomOrder()
            ->limit(2)
            ->get()
            ->map(function ($otherUser) {
                $randomBook = Book::inRandomOrder()->first();
                return [
                    'user_name' => $otherUser->name,
                    'user_avatar' => $otherUser->avatar_url,
                    'message' => "invite you to buy this book together",
                    'book' => new BookResource($randomBook),
                    'discount' => '40% off'
                ];
            });

        // 4. New Release (أحدث الكتب المضافة)
        $newReleases = Book::with('author')
            ->latest()
            ->limit(10)
            ->get();

        // 5. You Might Also Like (بناءً على التصنيفات اللي اليوزر اختارها في الـ Onboarding)
        $userInterests = $user->categories()->pluck('categories.id');
        $youMightLike = Book::with('author')
            ->whereIn('category_id', $userInterests)
            ->orWhere('average_rating', '>', 4)
            ->inRandomOrder()
            ->limit(10)
            ->get();

        // التجميع النهائي للرد
        return response()->json([
            'status' => 'success',
            'data' => [
                'daily_recommended' => BookResource::collection($dailyRecommended),
                'recently_played'   => BookResource::collection($recentlyPlayed),
                'my_campaigns'      => $campaigns,
                'new_releases'      => BookResource::collection($newReleases),
                'you_might_like'    => BookResource::collection($youMightLike),
            ]
        ]);
    }
}

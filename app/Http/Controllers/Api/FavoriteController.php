<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Author;
use App\Models\Book;
use App\Models\PersonalShelf;
use App\Http\Resources\Api\BookResource;
use App\Http\Resources\Api\AuthorResource;
use Illuminate\Http\Request;

class FavoriteController extends Controller
{
    // 1. جلب العناصر المفضلة حسب النوع (tabs)
    public function index(Request $request, $type)
    {
        $user = $request->user();

        if ($type === 'book') {
            // جلب الكتب التي تم وضع علامة مفضلة عليها في الرف
            $bookIds = $user->favoriteBooks()->pluck('book_id');
            $books = Book::with('author')->whereIn('id', $bookIds)->paginate(15);
            return BookResource::collection($books);
        }

        if ($type === 'author') {
            // مؤلفين (ليسوا رواة)
            $authors = $user->favoriteAuthors()
                ->where('is_narrator', false)
                ->paginate(15);
            return AuthorResource::collection($authors);
        }

        if ($type === 'narator') {
            // الرواة المفضلين
            $narrators = $user->favoriteAuthors()
                ->where('is_narrator', true)
                ->paginate(15);
            return AuthorResource::collection($narrators);
        }

        return response()->json(['message' => 'Invalid type'], 400);
    }

    // 2. إضافة أو حذف كتاب من المفضلة
    public function toggleBookFavorite(Request $request, $id)
    {
        $shelf = PersonalShelf::updateOrCreate(
            ['user_id' => $request->user()->id, 'book_id' => $id],
            // إذا لم يكن موجوداً، سيتم إنشاؤه وجعل is_favorite عكس حالتها الحالية أو true
        );

        $shelf->is_favorite = !$shelf->is_favorite;
        $shelf->save();

        return response()->json([
            'status' => $shelf->is_favorite,
            'message' => $shelf->is_favorite ? 'Added to favorites' : 'Removed from favorites'
        ]);
    }

    // 3. إضافة أو حذف مؤلف/راوي من المفضلة
    public function toggleAuthorFavorite(Request $request, $id)
    {
        $user = $request->user();
        // دالة toggle تقوم بالإضافة إذا لم يوجد والحذف إذا وجد تلقائياً
        $status = $user->favoriteAuthors()->toggle($id);

        $isAttached = count($status['attached']) > 0;

        return response()->json([
            'status' => $isAttached,
            'message' => $isAttached ? 'Following author' : 'Unfollowed author'
        ]);
    }
}

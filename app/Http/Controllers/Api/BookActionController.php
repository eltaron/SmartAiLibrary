<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\PersonalShelf;
use Illuminate\Http\Request;

class BookActionController extends Controller
{
    // 1. زر "Add to Favorites"
    // نستخدم نفس المنطق السابق للـ Toggle
    public function toggleFavorite(Request $request, $id)
    {
        $shelf = PersonalShelf::updateOrCreate(
            ['user_id' => $request->user()->id, 'book_id' => $id]
        );
        $shelf->is_favorite = !$shelf->is_favorite;
        $shelf->save();

        return response()->json([
            'is_favorite' => $shelf->is_favorite,
            'message' => $shelf->is_favorite ? 'Added to favorites' : 'Removed from favorites'
        ]);
    }

    // 2. زر "Don’t play this"
    // لإخفاء الكتاب من الظهور لليوزر في الاقتراحات
    public function blockBook(Request $request, $id)
    {
        $shelf = PersonalShelf::updateOrCreate(
            ['user_id' => $request->user()->id, 'book_id' => $id]
        );
        $shelf->is_blocked = true;
        $shelf->status = 'dropped'; // نغير الحالة لتجاهل الكتاب
        $shelf->save();

        return response()->json(['message' => 'We will show you less of this book']);
    }

    // 3. زر "Listen"
    // عند الضغط عليه، نسجل أن المستخدم بدأ الاستماع (ليظهر في Recently Played)
    public function logListen(Request $request, $id)
    {
        $shelf = PersonalShelf::updateOrCreate(
            ['user_id' => $request->user()->id, 'book_id' => $id]
        );
        $shelf->status = 'reading';
        $shelf->touch(); // تحديث وقت الـ updated_at ليظهر أول واحد في الـ Home
        $shelf->save();

        return response()->json(['message' => 'Playback started']);
    }

    // 4. زر "Share"
    // توليد رابط فريد للكتاب (Deep Link)
    public function shareBook($id)
    {
        $book = Book::findOrFail($id);
        $shareUrl = url("/books/{$book->slug}"); // الرابط الذي سيتم نسخه

        return response()->json([
            'share_url' => $shareUrl,
            'text' => "Check out this book: {$book->title} on NuBook Library!"
        ]);
    }
}

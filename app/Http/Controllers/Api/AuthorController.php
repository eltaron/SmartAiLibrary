<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Author;
use App\Http\Resources\Api\AuthorResource;
use Illuminate\Http\Request;

class AuthorController extends Controller
{
    // عرض قائمة بكل الفنانين/المؤلفين
    public function index()
    {
        $authors = Author::paginate(20);
        return AuthorResource::collection($authors);
    }

    // عرض الفنانين المشابهين (Similar Artists)
    public function similar($id)
    {
        $author = Author::findOrFail($id);

        // هنجيب التصنيفات اللي المؤلف ده كتب فيها
        $categoryIds = $author->books()->pluck('category_id')->unique();

        // هنجيب مؤلفين تانين ليهم كتب في نفس التصنيفات دي
        $similarAuthors = Author::where('id', '!=', $id)
            ->whereHas('books', function ($query) use ($categoryIds) {
                $query->whereIn('category_id', $categoryIds);
            })
            ->inRandomOrder()
            ->paginate(20);

        return AuthorResource::collection($similarAuthors)->additional([
            'meta' => [
                'title' => 'Similar Artist',
                'mix_by' => 'Nubook',
                'original_author' => $author->name
            ]
        ]);
    }
}

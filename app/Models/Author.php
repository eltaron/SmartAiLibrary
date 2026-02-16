<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Author extends Model
{
    use HasFactory;

    protected $guarded = [];

    public function books()
    {
        return $this->hasMany(Book::class);
    }
    public function fans()
    {
        return $this->belongsToMany(User::class, 'author_user');
    }
    public function getMonthlyListenersCount()
    {
        return \App\Models\PersonalShelf::whereHas('book', function ($q) {
            $q->where('author_id', $this->id);
        })
            ->where('updated_at', '>=', now()->subDays(30))
            ->distinct('user_id')
            ->count();
    }
}

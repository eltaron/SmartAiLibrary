<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Book extends Model
{
    use HasFactory;

    protected $guarded = [];

    protected $casts = [
        'published_date' => 'date',
        'is_featured' => 'boolean',
    ];

    public function author()
    {
        return $this->belongsTo(Author::class);
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function chapters()
    {
        return $this->hasMany(Chapter::class)->orderBy('order_column');
    }

    public function reviews()
    {
        return $this->hasMany(Review::class);
    }

    public function aiAnalysis()
    {
        return $this->hasOne(AiAnalyse::class);
    }

    public function aiMetadata()
    {
        return $this->hasOne(AiMetadata::class);
    }
    public function library()
    {
        return $this->hasMany(PersonalShelf::class);
    }
}

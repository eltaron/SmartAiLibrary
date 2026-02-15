<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class AiMetadata extends Model
{
    use HasFactory;

    protected $table = 'ai_metadata';

    protected $guarded = [];

    protected $casts = [
        'keywords' => 'array',
        'entities' => 'array',
        'vector_embeddings' => 'array',
    ];

    // العلاقة العكسية مع الكتاب
    public function book()
    {
        return $this->belongsTo(Book::class);
    }
}

<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class BookResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'cover_image' => $this->cover_image,
            'author_name' => $this->author?->name,
            'category_name' => $this->category?->name,
            'average_rating' => (float) $this->average_rating,
            'duration' => $this->duration, // لو كتاب صوتي
            'is_featured' => $this->is_featured,
            'published_at' => $this->published_date?->format('Y-m-d'),
        ];
    }
}

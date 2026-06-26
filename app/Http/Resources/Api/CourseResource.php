<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class CourseResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'slug' => $this->slug,
            'description' => $this->description,
            'cover_image' => $this->cover_image,
            'category_name' => $this->category?->name,
            'language' => $this->language,
            'duration' => $this->duration,
            'average_rating' => (float) $this->average_rating,
            'is_featured' => $this->is_featured,
            'is_free' => $this->is_free,
            'videos_count' => $this->whenCounted('videos'),
            'videos' => CourseVideoResource::collection($this->whenLoaded('videos')),
            'created_at' => $this->created_at,
        ];
    }
}

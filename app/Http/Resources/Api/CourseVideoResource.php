<?php

namespace App\Http\Resources\Api;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class CourseVideoResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'video_url' => $this->video_url ? asset('storage/' . $this->video_url) : null,
            'duration_seconds' => $this->duration_seconds,
            'content_text' => $this->content_text,
            'order' => $this->order_column,
        ];
    }
}

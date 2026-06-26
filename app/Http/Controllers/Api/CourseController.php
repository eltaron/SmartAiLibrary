<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Course;
use App\Models\CourseVideo;
use App\Http\Resources\Api\CourseResource;
use App\Http\Resources\Api\CourseVideoResource;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Storage;

class CourseController extends Controller
{
    public function index()
    {
        $courses = Course::with('category')
            ->withCount('videos')
            ->latest()
            ->paginate(20);

        return CourseResource::collection($courses);
    }

    public function show($id)
    {
        $course = Course::with(['category', 'videos'])->findOrFail($id);

        return new CourseResource($course);
    }

    public function featured()
    {
        $courses = Course::with('category')
            ->withCount('videos')
            ->where('is_featured', true)
            ->latest()
            ->limit(10)
            ->get();

        return CourseResource::collection($courses);
    }

    public function free()
    {
        $courses = Course::with('category')
            ->withCount('videos')
            ->where('is_free', true)
            ->latest()
            ->limit(20)
            ->get();

        return CourseResource::collection($courses);
    }

    public function byCategory($categoryId)
    {
        $courses = Course::with('category')
            ->withCount('videos')
            ->where('category_id', $categoryId)
            ->latest()
            ->paginate(20);

        return CourseResource::collection($courses);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'title' => 'required|string|max:255',
            'category_id' => 'required|exists:categories,id',
            'description' => 'nullable|string',
            'cover_image' => 'nullable|image|max:2048',
            'language' => 'nullable|string|max:10',
            'duration' => 'nullable|string|max:50',
            'is_featured' => 'boolean',
            'is_free' => 'boolean',
        ]);

        $data['slug'] = Str::slug($data['title']) . '-' . uniqid();

        if ($request->hasFile('cover_image')) {
            $data['cover_image'] = $request->file('cover_image')->store('courses/covers', 'public');
        }

        $course = Course::create($data);

        return new CourseResource($course->load('category'));
    }

    public function update(Request $request, $id)
    {
        $course = Course::findOrFail($id);

        $data = $request->validate([
            'title' => 'sometimes|string|max:255',
            'category_id' => 'sometimes|exists:categories,id',
            'description' => 'nullable|string',
            'cover_image' => 'nullable|image|max:2048',
            'language' => 'nullable|string|max:10',
            'duration' => 'nullable|string|max:50',
            'is_featured' => 'boolean',
            'is_free' => 'boolean',
        ]);

        if (isset($data['title'])) {
            $data['slug'] = Str::slug($data['title']) . '-' . uniqid();
        }

        if ($request->hasFile('cover_image')) {
            if ($course->cover_image) {
                Storage::disk('public')->delete($course->cover_image);
            }
            $data['cover_image'] = $request->file('cover_image')->store('courses/covers', 'public');
        }

        $course->update($data);

        return new CourseResource($course->load('category'));
    }

    public function destroy($id)
    {
        $course = Course::findOrFail($id);

        if ($course->cover_image) {
            Storage::disk('public')->delete($course->cover_image);
        }

        foreach ($course->videos as $video) {
            if ($video->video_url) {
                Storage::disk('public')->delete($video->video_url);
            }
        }

        $course->delete();

        return response()->json(['message' => 'Course deleted successfully']);
    }

    // Video management
    public function addVideo(Request $request, $courseId)
    {
        $course = Course::findOrFail($courseId);

        $data = $request->validate([
            'title' => 'required|string|max:255',
            'video' => 'required|mimes:mp4,mov,avi,wmv,flv,mkv|max:204800',
            'duration_seconds' => 'nullable|integer|min:0',
            'content_text' => 'nullable|string',
            'order_column' => 'nullable|integer|min:1',
        ]);

        $data['course_id'] = $course->id;

        if ($request->hasFile('video')) {
            $path = $request->file('video')->store('courses/videos', 'public');
            $data['video_url'] = $path;
            $data['video_path'] = $path;
        }

        $video = CourseVideo::create($data);

        return new CourseVideoResource($video);
    }

    public function updateVideo(Request $request, $courseId, $videoId)
    {
        $course = Course::findOrFail($courseId);
        $video = $course->videos()->findOrFail($videoId);

        $data = $request->validate([
            'title' => 'sometimes|string|max:255',
            'video' => 'nullable|mimes:mp4,mov,avi,wmv,flv,mkv|max:204800',
            'duration_seconds' => 'nullable|integer|min:0',
            'content_text' => 'nullable|string',
            'order_column' => 'nullable|integer|min:1',
        ]);

        if ($request->hasFile('video')) {
            if ($video->video_url) {
                Storage::disk('public')->delete($video->video_url);
            }
            $path = $request->file('video')->store('courses/videos', 'public');
            $data['video_url'] = $path;
            $data['video_path'] = $path;
        }

        $video->update($data);

        return new CourseVideoResource($video);
    }

    public function deleteVideo($courseId, $videoId)
    {
        $course = Course::findOrFail($courseId);
        $video = $course->videos()->findOrFail($videoId);

        if ($video->video_url) {
            Storage::disk('public')->delete($video->video_url);
        }

        $video->delete();

        return response()->json(['message' => 'Video deleted successfully']);
    }

    public function videos($courseId)
    {
        $course = Course::findOrFail($courseId);

        return CourseVideoResource::collection($course->videos);
    }
}

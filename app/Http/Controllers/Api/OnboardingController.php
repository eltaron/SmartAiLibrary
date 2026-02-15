<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\Category;

class OnboardingController extends Controller
{
    // 1. تحديث البروفايل (تاريخ الميلاد، النوع)
    public function updateProfile(Request $request)
    {
        $request->validate([
            'birth_date' => 'required|date', // "What's your date of birth?" screen
            'gender' => 'required|in:male,female', // "What's your gender?" screen
            'name' => 'sometimes|string', // "What's your name?" screen (update)
            'avatar' => 'sometimes|image|max:2048' // "Edit Profile" screen
        ]);

        $user = $request->user();

        // رفع الصورة إذا وجدت
        if ($request->hasFile('avatar')) {
            $path = $request->file('avatar')->store('avatars', 'public');
            $user->avatar_url = asset('storage/' . $path);
        }

        $user->update($request->only(['birth_date', 'gender', 'name']));

        return response()->json([
            'message' => 'Profile updated successfully',
            'data' => $user
        ]);
    }

    // 2. جلب التصنيفات للاختيار (Pick more topics screen)
    public function getTopics()
    {
        $topics = Category::select('id', 'name', 'icon')->where('is_active', true)->get();
        return response()->json(['data' => $topics]);
    }

    // 3. حفظ اختيارات المستخدم
    public function saveTopics(Request $request)
    {
        $request->validate([
            'category_ids' => 'required|array',
            'category_ids.*' => 'exists:categories,id'
        ]);

        // هنا بنفترض إنك عامل علاقة Many-to-Many بين User و Category (لو مش معمولة، نعملها)
        // User belongsToMany Category
        // هنفترض وجود جدول `category_user`

        $request->user()->categories()->sync($request->category_ids);

        // حالياً ممكن نرجع رسالة نجاح بس لحد ما نظبط العلاقة
        return response()->json(['message' => 'Topics saved successfully']);
    }
}

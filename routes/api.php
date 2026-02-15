<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\NewPasswordController;
use App\Http\Controllers\Api\OnboardingController;

/*
|--------------------------------------------------------------------------
| API Routes - Smart AI Library
|--------------------------------------------------------------------------
*/

// Authentication Routes (Public)
Route::post('/register', [AuthController::class, 'register']); // إنشاء حساب
Route::post('/login', [AuthController::class, 'login']);       // تسجيل دخول
Route::post('/forgot-password', [NewPasswordController::class, 'forgotPassword']); // نسيت كلمة السر

// Social Auth
Route::get('/auth/{provider}/redirect', [AuthController::class, 'socialRedirect']);
Route::get('/auth/{provider}/callback', [AuthController::class, 'socialCallback']);

// Protected Routes (يجب أن يكون مسجلاً)
Route::middleware('auth:sanctum')->group(function () {

    // Auth Management
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', function (Request $request) {
        return $request->user();
    });

    // Onboarding Process (Screenshots)
    Route::post('/profile/update', [OnboardingController::class, 'updateProfile']); // لحفظ الميلاد والنوع
    Route::get('/topics', [OnboardingController::class, 'getTopics']);            // لعرض شاشة التصنيفات
    Route::post('/topics/save', [OnboardingController::class, 'saveTopics']);     // لحفظ اختيارات التصنيفات

});

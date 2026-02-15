<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\HomeController;
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
// Password Reset OTP Flow
Route::post('/forgot-password/send-otp', [NewPasswordController::class, 'sendOtp']);
Route::post('/forgot-password/verify-otp', [NewPasswordController::class, 'verifyOtp']);
Route::post('/forgot-password/reset', [NewPasswordController::class, 'resetPassword']);
// Social Auth
Route::get('/auth/{provider}/redirect', [AuthController::class, 'socialRedirect']);
Route::get('/auth/{provider}/callback', [AuthController::class, 'socialCallback']);


Route::middleware('auth:sanctum')->group(function () {
    Route::get('/home', [HomeController::class, 'index']);

    // Auth Management
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', function (Request $request) {
        return $request->user();
    });

    // Onboarding Process (Screenshots)
    Route::post('/profile/update', [OnboardingController::class, 'updateProfile']);
    Route::get('/topics', [OnboardingController::class, 'getTopics']);
    Route::post('/topics/save', [OnboardingController::class, 'saveTopics']);
});

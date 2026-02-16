<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\AuthorController;
use App\Http\Controllers\Api\AuthorProfileController;
use App\Http\Controllers\Api\BookActionController;
use App\Http\Controllers\Api\DiscoveryController;
use App\Http\Controllers\Api\FavoriteController;
use App\Http\Controllers\Api\HomeController;
use App\Http\Controllers\Api\NewPasswordController;
use App\Http\Controllers\Api\OnboardingController;
use App\Http\Controllers\Api\SearchController;

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
    Route::get('/discover', [DiscoveryController::class, 'index']);
    Route::get('/search', [DiscoveryController::class, 'search']);

    // Search Routes
    Route::get('/search/initial', [SearchController::class, 'getInitialData']); // الصفحة الفاضية
    Route::get('/search/global', [SearchController::class, 'globalSearch']);    // البحث العام
    Route::get('/search/filter/{type}', [SearchController::class, 'searchByType']); // بحث متخصص
    Route::delete('/search/history/{id?}', [SearchController::class, 'clearHistory']); // مسح السجل

    // Auth Management
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', function (Request $request) {
        return $request->user();
    });

    // Onboarding Process (Screenshots)
    Route::post('/profile/update', [OnboardingController::class, 'updateProfile']);
    Route::get('/topics', [OnboardingController::class, 'getTopics']);
    Route::post('/topics/save', [OnboardingController::class, 'saveTopics']);

    // قوائم الـ 20 المخصصة
    Route::get('/discover/trending-20', [DiscoveryController::class, 'topTrendingList']);
    Route::get('/discover/free-20', [DiscoveryController::class, 'topFreeList']);

    // روابط المؤلفين والفنانين
    Route::get('/authors', [AuthorController::class, 'index']);
    Route::get('/authors/{id}/similar', [AuthorController::class, 'similar']);

    // الحصول على القوائم (التبويبات في الصور)
    Route::get('/favorites/{type}', [FavoriteController::class, 'index']); // type: book, author, narator
    // عمليات الـ Toggle (عند الضغط على القلب أو متابعة)
    Route::post('/favorites/book/{id}', [FavoriteController::class, 'toggleBookFavorite']);
    Route::post('/favorites/author/{id}', [FavoriteController::class, 'toggleAuthorFavorite']);

    // روابط قائمة الخيارات (Modal Actions)
    Route::post('/books/{id}/favorite', [BookActionController::class, 'toggleFavorite']);
    Route::post('/books/{id}/block', [BookActionController::class, 'blockBook']);
    Route::post('/books/{id}/listen', [BookActionController::class, 'logListen']);
    Route::get('/books/{id}/share', [BookActionController::class, 'shareBook']);

    Route::get('/authors/{id}/profile', [AuthorProfileController::class, 'show']);
});

<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Auth;
use Illuminate\Validation\ValidationException;
use Laravel\Socialite\Facades\Socialite;

class AuthController extends Controller
{
    // 1. تسجيل مستخدم جديد
    public function register(Request $request)
    {
        $request->validate([
            'email' => 'required|email|unique:users',
            'password' => 'required|min:8', // كما في السكرين شوت (at least 8 chars)
            'name' => 'required|string',
            'username' => 'nullable|unique:users|alpha_dash', // اختياري في البداية
        ]);

        $user = User::create([
            'name' => $request->name,
            'email' => $request->email,
            'username' => $request->username ?? explode('@', $request->email)[0] . rand(100, 999),
            'password' => Hash::make($request->password),
            'role' => 'student', // القيمة الافتراضية
        ]);

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'message' => 'User registered successfully',
            'data' => $user,
            'token' => $token
        ], 201);
    }

    // 2. تسجيل الدخول (يدعم الإيميل أو اسم المستخدم كما في السكرين)
    public function login(Request $request)
    {
        $request->validate([
            'login' => 'required', // could be email or username
            'password' => 'required'
        ]);

        $loginType = filter_var($request->login, FILTER_VALIDATE_EMAIL) ? 'email' : 'username';

        if (!Auth::attempt([$loginType => $request->login, 'password' => $request->password])) {
            return response()->json(['message' => 'Invalid credentials'], 401);
        }

        $user = Auth::user();
        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'message' => 'Logged in successfully',
            'data' => $user,
            'token' => $token,
            'is_profile_complete' => !is_null($user->birth_date) // هل أكمل بياناته أم لا؟
        ]);
    }

    // 3. الخروج
    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();
        return response()->json(['message' => 'Logged out successfully']);
    }

    // 4. السوشيال ميديا (رابط التوجيه)
    public function socialRedirect($provider)
    {
        // يرجع الرابط للفرونت إند عشان يفتحوه في المتصفح/Webview
        return response()->json([
            'url' => Socialite::driver($provider)->stateless()->redirect()->getTargetUrl()
        ]);
    }

    // 5. السوشيال ميديا (الكول باك)
    public function socialCallback($provider)
    {
        try {
            // Front-end sends the token/user data in a real app,
            // but for standard flow this expects backend callback handling.
            // For pure API, usually you send "access_token" from provider to backend.
            $socialUser = Socialite::driver($provider)->stateless()->user();

            $user = User::updateOrCreate([
                'email' => $socialUser->getEmail(),
            ], [
                'name' => $socialUser->getName(),
                'avatar_url' => $socialUser->getAvatar(),
                'password' => Hash::make(\Str::random(16)), // باسورد عشوائي
            ]);

            $token = $user->createToken('auth_token')->plainTextToken;

            return response()->json([
                'message' => 'Social login successful',
                'token' => $token,
                'user' => $user
            ]);
        } catch (\Exception $e) {
            return response()->json(['error' => 'Social Auth Failed'], 400);
        }
    }
}

<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Mail;
use App\Mail\OtpMail;
use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

class NewPasswordController extends Controller
{
    // 1. إرسال الـ OTP
    public function sendOtp(Request $request)
    {
        $request->validate(['email' => 'required|email|exists:users,email']);

        $otp = rand(1000, 9999); // توليد 4 أرقام

        // حفظ الـ OTP في الجدول
        DB::table('password_reset_tokens')->updateOrInsert(
            ['email' => $request->email],
            [
                'otp' => $otp,
                'token' => Str::random(60), // لارفيل بيحتاجه كـ fallback
                'created_at' => now()
            ]
        );

        // إرسال الإيميل
        Mail::to($request->email)->send(new OtpMail($otp));

        return response()->json(['message' => 'OTP sent to your email']);
    }

    // 2. التحقق من الـ OTP
    public function verifyOtp(Request $request)
    {
        $request->validate([
            'email' => 'required|email|exists:users,email',
            'otp' => 'required|string'
        ]);

        $reset = DB::table('password_reset_tokens')
            ->where('email', $request->email)
            ->where('otp', $request->otp)
            ->where('created_at', '>', now()->subMinutes(10)) // صلاحية 10 دقائق
            ->first();

        if (!$reset) {
            return response()->json(['message' => 'Invalid or expired OTP'], 422);
        }

        return response()->json(['message' => 'OTP verified successfully']);
    }

    // 3. تعيين كلمة السر الجديدة
    public function resetPassword(Request $request)
    {
        $request->validate([
            'email' => 'required|email|exists:users,email',
            'otp' => 'required|string',
            'password' => 'required|min:8|confirmed'
        ]);

        // نتحقق تاني للأمان
        $reset = DB::table('password_reset_tokens')
            ->where('email', $request->email)
            ->where('otp', $request->otp)
            ->first();

        if (!$reset) {
            return response()->json(['message' => 'Unauthorized action'], 403);
        }

        // تحديث الباسورد
        $user = User::where('email', $request->email)->first();
        $user->update(['password' => Hash::make($request->password)]);

        // حذف الـ OTP بعد الاستخدام
        DB::table('password_reset_tokens')->where('email', $request->email)->delete();

        return response()->json(['message' => 'Password reset successfully']);
    }
}

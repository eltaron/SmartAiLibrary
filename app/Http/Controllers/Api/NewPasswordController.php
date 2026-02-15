<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Password;
use Illuminate\Support\Facades\DB;

class NewPasswordController extends Controller
{
    // ارسال رابط إعادة التعيين
    public function forgotPassword(Request $request)
    {
        $request->validate(['email' => 'required|email']);

        // Laravel Default Password Reset
        $status = Password::sendResetLink($request->only('email'));

        if ($status === Password::RESET_LINK_SENT) {
            return response()->json(['message' => __($status)]);
        }

        return response()->json(['email' => __($status)], 400);
    }
}

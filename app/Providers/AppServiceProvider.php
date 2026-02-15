<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use Illuminate\Auth\Notifications\ResetPassword;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        ResetPassword::createUrlUsing(function (object $notifiable, string $token) {
            // هنا يمكنك وضع رابط الدومين الخاص بك أو رابط عميق للتطبيق (Deep Link)
            return 'http://127.0.0.1:8000/reset-password/' . $token . '?email=' . $notifiable->getEmailForPasswordReset();
        });
    }
}

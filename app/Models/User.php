<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $guarded = [];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
    ];

    public function library()
    {
        return $this->hasMany(PersonalShelf::class);
    }

    public function reviews()
    {
        return $this->hasMany(Review::class);
    }
    public function categories()
    {
        return $this->belongsToMany(Category::class);
    }
    // المؤلفين المفضلين
    public function favoriteAuthors()
    {
        return $this->belongsToMany(Author::class, 'author_user');
    }

    // الكتب المفضلة (من خلال جدول الرف الشخصي)
    public function favoriteBooks()
    {
        return $this->hasMany(PersonalShelf::class)->where('is_favorite', true);
    }
}

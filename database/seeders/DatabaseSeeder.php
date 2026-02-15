<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\User;
use App\Models\Category;
use App\Models\Author;
use App\Models\Book;
use App\Models\Chapter;
use App\Models\AiMetadata;
use App\Models\Review;
use App\Models\PersonalShelf;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // 1. إنشاء حساب الآدمن للدخول
        User::factory()->create([
            'name' => 'Admin User',
            'email' => 'admin@admin.com',
            'password' => bcrypt('password'), // كلمة المرور
            'role' => 'admin',
        ]);

        // 2. إنشاء 50 مستخدم عادي
        $users = User::factory(50)->create();

        // 3. إنشاء تصنيفات محددة عشان تكون واقعية
        $categories = collect([
            'Novel',
            'Science & Tech',
            'History',
            'Biographies',
            'Self Help',
            'Programming',
            'Inspirational',
            'Comedy',
            'Horror',
            'Kids'
        ])->map(function ($name) {
            return Category::factory()->create([
                'name' => $name,
                'slug' => str()->slug($name)
            ]);
        });

        // 4. إنشاء 20 مؤلف
        $authors = Author::factory(20)->create();

        // 5. إنشاء الكتب (100 كتاب) وتوابعها
        $books = Book::factory(100)
            ->recycle($authors) // استخدم المؤلفين الموجودين
            ->recycle($categories) // استخدم التصنيفات الموجودة
            ->create()
            ->each(function ($book) use ($users) {

                // أ: إنشاء Metadata لكل كتاب (ضروري للـ AI)
                AiMetadata::factory()->create(['book_id' => $book->id]);

                // ب: إنشاء 3 إلى 5 فصول لكل كتاب
                Chapter::factory(rand(3, 5))->create(['book_id' => $book->id]);

                // ج: إنشاء 5 إلى 10 تقييمات لكل كتاب من يوزرز عشوائيين
                Review::factory(rand(5, 10))->create([
                    'book_id' => $book->id,
                    'user_id' => $users->random()->id,
                ]);
            });

        // 6. تعبئة المكتبات الشخصية للمستخدمين
        // كل مستخدم هيكون عنده من 1 إلى 5 كتب في مكتبته
        $users->each(function ($user) use ($books) {
            PersonalShelf::factory(rand(1, 5))->create([
                'user_id' => $user->id,
                'book_id' => $books->random()->id,
            ]);
        });

        // 7. إنشاء داتا مطابقة للصورة (عشان البرزنتيشن)
        $this->createDemoData();
    }

    // دالة خاصة لإنشاء داتا الـ Screenshot
    private function createDemoData()
    {
        $author = Author::factory()->create(['name' => 'Iwan Fals', 'is_narrator' => true]);
        $category = Category::where('slug', 'novel')->first();

        $book = Book::factory()->create([
            'title' => 'Manusia Setengah Dewa',
            'slug' => 'manusia-setengah-dewa',
            'author_id' => $author->id,
            'category_id' => $category->id ?? Category::factory()->create()->id,
            'cover_image' => 'https://via.placeholder.com/400x600.png?text=Manusia',
            'average_rating' => 4.2
        ]);

        Chapter::factory()->create(['book_id' => $book->id, 'title' => 'Part 1']);
        Chapter::factory()->create(['book_id' => $book->id, 'title' => 'Part 2']);
        AiMetadata::factory()->create(['book_id' => $book->id, 'summary' => 'Lorem ipsum dolor sit amet...']);
    }
}

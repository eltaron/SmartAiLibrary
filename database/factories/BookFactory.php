<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Book>
 */
class BookFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $title = fake()->sentence(3);
        return [
            'title' => $title,
            'slug' => str()->slug($title) . '-' . fake()->numberBetween(100, 999),
            // العلاقات هيتم تعبئتها في الـ Seeder عشان نضمن انها موجودة
            'author_id' => \App\Models\Author::factory(),
            'category_id' => \App\Models\Category::factory(),
            'description' => fake()->paragraphs(3, true),
            'cover_image' => 'https://placehold.co/400x600/222222/FFFFFF/png?text=Book+Cover',
            'file_path' => 'books/dummy.pdf', // مسار وهمي
            'isbn' => fake()->isbn13(),
            'published_date' => fake()->date(),
            'publisher' => fake()->company(),
            'language' => 'en',
            'page_count' => fake()->numberBetween(100, 1000),
            'duration' => fake()->numberBetween(60, 600) . ' mins',
            'view_count' => fake()->numberBetween(100, 50000),
            'average_rating' => fake()->randomFloat(1, 1, 5),
        ];
    }
}

<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Category>
 */
class CategoryFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $name = fake()->unique()->randomElement([
            'Science Fiction',
            'Romance',
            'Mystery',
            'Technology',
            'History',
            'Self Help',
            'Programming',
            'Business',
            'Comedy',
            'Horror',
            'Biography',
            'Health'
        ]);
        return [
            'name' => $name,
            'slug' => str()->slug($name),
            'icon' => 'heroicon-o-book-open',
            'is_active' => true,
        ];
    }
}

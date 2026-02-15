<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Author>
 */
class AuthorFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'bio' => fake()->paragraph(),
            'image' => 'https://i.pravatar.cc/300?u=' . fake()->numberBetween(1, 1000),
            'is_narrator' => fake()->boolean(30), // 30% فرصة يكون راوي صوتي
        ];
    }
}

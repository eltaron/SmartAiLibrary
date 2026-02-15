<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\PersonalShelf>
 */
class PersonalShelfFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            // IDs passed later
            'status' => fake()->randomElement(['want_to_read', 'reading', 'completed']),
            'is_favorite' => fake()->boolean(),
            'current_page' => fake()->numberBetween(1, 300),
        ];
    }
}

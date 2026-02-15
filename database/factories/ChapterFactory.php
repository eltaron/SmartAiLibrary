<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Chapter>
 */
class ChapterFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            // Book ID passed from seeder
            'title' => fake()->sentence(4),
            'audio_url' => 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3', // ملف صوتي للتجربة
            'duration_seconds' => fake()->numberBetween(180, 1200),
            'order_column' => fake()->numberBetween(1, 10),
        ];
    }
}

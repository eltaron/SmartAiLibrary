<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\AiMetadata>
 */
class AiMetadataFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            // Book ID will be passed from seeder
            'summary' => fake()->paragraph(),
            'detailed_summary' => fake()->text(2000),
            'keywords' => fake()->words(10), // مصفوفة كلمات
            'entities' => ['person' => fake()->name(), 'location' => fake()->city()],
            'sentiment' => fake()->randomElement(['Positive', 'Neutral', 'Negative']),
            'vector_embeddings' => [], // يمكن تركها فارغة حالياً
        ];
    }
}

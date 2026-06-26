<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Course;
use App\Models\CourseVideo;
use Illuminate\Database\Seeder;

class CourseSeeder extends Seeder
{
    public function run(): void
    {
        $categoryIds = Category::pluck('id')->toArray();

        if (empty($categoryIds)) {
            $cat = Category::create(['name' => 'Programming', 'slug' => 'programming']);
            $categoryIds = [$cat->id];
        }

        $courses = [
            [
                'title' => 'Introduction to Python Programming',
                'slug' => 'intro-to-python',
                'description' => 'Learn Python from scratch. This course covers variables, loops, functions, and object-oriented programming with hands-on projects.',
                'language' => 'en',
                'duration' => '12 hours',
                'is_featured' => true,
                'is_free' => true,
                'videos' => [
                    ['title' => 'Welcome & Setup', 'duration_seconds' => 480, 'order_column' => 1],
                    ['title' => 'Variables & Data Types', 'duration_seconds' => 720, 'order_column' => 2],
                    ['title' => 'Control Flow (If/Else)', 'duration_seconds' => 600, 'order_column' => 3],
                    ['title' => 'Loops & Iterations', 'duration_seconds' => 540, 'order_column' => 4],
                    ['title' => 'Functions & Modules', 'duration_seconds' => 900, 'order_column' => 5],
                ],
            ],
            [
                'title' => 'Laravel for Beginners',
                'slug' => 'laravel-for-beginners',
                'description' => 'Build modern web applications with Laravel. Learn MVC, Blade, Eloquent, routing, and authentication.',
                'language' => 'en',
                'duration' => '18 hours',
                'is_featured' => true,
                'is_free' => false,
                'videos' => [
                    ['title' => 'What is Laravel?', 'duration_seconds' => 360, 'order_column' => 1],
                    ['title' => 'Installation & Setup', 'duration_seconds' => 600, 'order_column' => 2],
                    ['title' => 'Routing & Controllers', 'duration_seconds' => 840, 'order_column' => 3],
                    ['title' => 'Blade Templating Engine', 'duration_seconds' => 720, 'order_column' => 4],
                    ['title' => 'Eloquent ORM Basics', 'duration_seconds' => 960, 'order_column' => 5],
                ],
            ],
            [
                'title' => 'Data Science & Machine Learning',
                'slug' => 'data-science-ml',
                'description' => 'Master data science concepts including statistics, pandas, scikit-learn, and building ML models.',
                'language' => 'en',
                'duration' => '24 hours',
                'is_featured' => true,
                'is_free' => false,
                'videos' => [
                    ['title' => 'Introduction to Data Science', 'duration_seconds' => 420, 'order_column' => 1],
                    ['title' => 'NumPy & Pandas Fundamentals', 'duration_seconds' => 900, 'order_column' => 2],
                    ['title' => 'Data Visualization with Matplotlib', 'duration_seconds' => 660, 'order_column' => 3],
                    ['title' => 'Supervised Learning Algorithms', 'duration_seconds' => 1200, 'order_column' => 4],
                    ['title' => 'Model Evaluation & Deployment', 'duration_seconds' => 780, 'order_column' => 5],
                ],
            ],
            [
                'title' => 'UI/UX Design Fundamentals',
                'slug' => 'ui-ux-design',
                'description' => 'Learn design thinking, wireframing, prototyping, and user research to create stunning digital experiences.',
                'language' => 'en',
                'duration' => '10 hours',
                'is_featured' => false,
                'is_free' => true,
                'videos' => [
                    ['title' => 'Design Thinking Process', 'duration_seconds' => 540, 'order_column' => 1],
                    ['title' => 'Wireframing & Prototyping', 'duration_seconds' => 720, 'order_column' => 2],
                    ['title' => 'Color Theory & Typography', 'duration_seconds' => 600, 'order_column' => 3],
                    ['title' => 'User Research Methods', 'duration_seconds' => 480, 'order_column' => 4],
                ],
            ],
            [
                'title' => 'JavaScript: From Zero to Hero',
                'slug' => 'javascript-zero-to-hero',
                'description' => 'Comprehensive JavaScript course covering ES6+, DOM manipulation, async programming, and modern frameworks.',
                'language' => 'en',
                'duration' => '20 hours',
                'is_featured' => true,
                'is_free' => true,
                'videos' => [
                    ['title' => 'JavaScript Basics', 'duration_seconds' => 600, 'order_column' => 1],
                    ['title' => 'DOM Manipulation', 'duration_seconds' => 720, 'order_column' => 2],
                    ['title' => 'ES6+ Features', 'duration_seconds' => 540, 'order_column' => 3],
                    ['title' => 'Async JavaScript & APIs', 'duration_seconds' => 900, 'order_column' => 4],
                    ['title' => 'Introduction to React', 'duration_seconds' => 1200, 'order_column' => 5],
                ],
            ],
            [
                'title' => 'Cybersecurity Essentials',
                'slug' => 'cybersecurity-essentials',
                'description' => 'Protect systems and networks from cyber threats. Learn encryption, network security, and ethical hacking basics.',
                'language' => 'en',
                'duration' => '15 hours',
                'is_featured' => false,
                'is_free' => false,
                'videos' => [
                    ['title' => 'Introduction to Cybersecurity', 'duration_seconds' => 360, 'order_column' => 1],
                    ['title' => 'Network Security Fundamentals', 'duration_seconds' => 840, 'order_column' => 2],
                    ['title' => 'Cryptography Basics', 'duration_seconds' => 600, 'order_column' => 3],
                    ['title' => 'Ethical Hacking Overview', 'duration_seconds' => 720, 'order_column' => 4],
                ],
            ],
        ];

        foreach ($courses as $courseData) {
            $videos = $courseData['videos'];
            unset($courseData['videos']);

            $courseData['category_id'] = $categoryIds[array_rand($categoryIds)];
            $courseData['average_rating'] = round(3 + (mt_rand() / mt_getrandmax()) * 2, 1);

            $course = Course::create($courseData);

            foreach ($videos as $videoData) {
                $course->videos()->create($videoData);
            }
        }

        $this->command->info('Courses seeded successfully: ' . count($courses) . ' courses with videos.');
    }
}

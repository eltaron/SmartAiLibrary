<?php

namespace App\Filament\Widgets;

use App\Models\Book;
use App\Models\Course;
use Carbon\Carbon;
use Filament\Widgets\ChartWidget;
use Illuminate\Support\Facades\DB;

class LatestBooksChart extends ChartWidget
{
    protected static ?int $sort = 2;

    protected static ?string $heading = 'Content Growth (Last 6 Months)';

    protected int|string|array $columnSpan = 'full';

    protected function getData(): array
    {
        $months = collect(range(5, 0))->map(function ($i) {
            return now()->subMonths($i)->format('Y-m');
        });

        $booksCounts = $months->map(function ($month) {
            return Book::where(DB::raw("DATE_FORMAT(created_at, '%Y-%m')"), $month)->count();
        });

        $coursesCounts = $months->map(function ($month) {
            return Course::where(DB::raw("DATE_FORMAT(created_at, '%Y-%m')"), $month)->count();
        });

        $labels = $months->map(function ($month) {
            return Carbon::createFromFormat('Y-m', $month)->format('M Y');
        });

        return [
            'datasets' => [
                [
                    'label' => 'Books',
                    'data' => $booksCounts->toArray(),
                    'backgroundColor' => '#3b82f6',
                    'borderColor' => '#3b82f6',
                    'tension' => 0.3,
                ],
                [
                    'label' => 'Courses',
                    'data' => $coursesCounts->toArray(),
                    'backgroundColor' => '#f59e0b',
                    'borderColor' => '#f59e0b',
                    'tension' => 0.3,
                ],
            ],
            'labels' => $labels->toArray(),
        ];
    }

    protected function getType(): string
    {
        return 'line';
    }
}

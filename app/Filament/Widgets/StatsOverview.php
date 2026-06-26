<?php

namespace App\Filament\Widgets;

use App\Models\Book;
use App\Models\Course;
use App\Models\User;
use App\Models\Author;
use App\Models\Category;
use App\Models\Review;
use App\Models\PersonalShelf;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class StatsOverview extends BaseWidget
{
    protected static ?int $sort = 1;

    protected function getStats(): array
    {
        return [
            Stat::make('Total Users', User::count())
                ->description('Registered accounts')
                ->descriptionIcon('heroicon-m-users')
                ->color('info'),

            Stat::make('Total Books', Book::count())
                ->description('In the library catalog')
                ->descriptionIcon('heroicon-m-book-open')
                ->color('success'),

            Stat::make('Total Courses', Course::count())
                ->description('Available courses')
                ->descriptionIcon('heroicon-m-academic-cap')
                ->color('warning'),

            Stat::make('Total Authors', Author::count())
                ->description('Writers & narrators')
                ->descriptionIcon('heroicon-m-pencil')
                ->color('danger'),

            Stat::make('Categories', Category::count())
                ->description('Active categories')
                ->descriptionIcon('heroicon-m-tag')
                ->color('gray'),

            Stat::make('Total Reviews', Review::count())
                ->description('User ratings & feedback')
                ->descriptionIcon('heroicon-m-star')
                ->color('success'),

            Stat::make('Active Reads', PersonalShelf::whereIn('status', ['reading', 'want_to_read'])->count())
                ->description('Books being read now')
                ->descriptionIcon('heroicon-m-eye')
                ->color('info'),

            Stat::make('Completed Books', PersonalShelf::where('status', 'completed')->count())
                ->description('Finished by users')
                ->descriptionIcon('heroicon-m-check-badge')
                ->color('success'),
        ];
    }
}

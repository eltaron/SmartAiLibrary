<?php

namespace App\Filament\Resources;

use App\Filament\Resources\PersonalShelfResource\Pages;
use App\Models\PersonalShelf;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class PersonalShelfResource extends Resource
{
    protected static ?string $model = PersonalShelf::class;

    protected static ?string $navigationIcon = 'heroicon-o-bookmark';

    protected static ?string $navigationGroup = 'Community';

    protected static ?int $navigationSort = 2;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('user_id')
                    ->relationship('user', 'name')
                    ->required()
                    ->searchable()
                    ->preload(),
                Forms\Components\Select::make('book_id')
                    ->relationship('book', 'title')
                    ->required()
                    ->searchable()
                    ->preload(),
                Forms\Components\Select::make('status')
                    ->options([
                        'want_to_read' => 'Want to Read',
                        'reading' => 'Reading',
                        'completed' => 'Completed',
                        'dropped' => 'Dropped',
                    ])
                    ->required(),
                Forms\Components\Toggle::make('is_favorite')
                    ->label('Favorite'),
                Forms\Components\Toggle::make('is_blocked')
                    ->label('Blocked'),
                Forms\Components\TextInput::make('current_page')
                    ->required()
                    ->numeric()
                    ->default(0)
                    ->label('Current Page'),
                Forms\Components\TextInput::make('current_chapter_id')
                    ->numeric()
                    ->default(null)
                    ->label('Current Chapter'),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('user.name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('book.title')
                    ->searchable()
                    ->sortable()
                    ->limit(30),
                Tables\Columns\TextColumn::make('status')
                    ->badge()
                    ->color(fn ($state) => match ($state) {
                        'reading' => 'info',
                        'completed' => 'success',
                        'want_to_read' => 'warning',
                        'dropped' => 'danger',
                        default => 'gray',
                    }),
                Tables\Columns\IconColumn::make('is_favorite')
                    ->boolean()
                    ->label('Fav'),
                Tables\Columns\IconColumn::make('is_blocked')
                    ->boolean()
                    ->label('Blocked'),
                Tables\Columns\TextColumn::make('current_page')
                    ->numeric()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->defaultSort('created_at', 'desc')
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'want_to_read' => 'Want to Read',
                        'reading' => 'Reading',
                        'completed' => 'Completed',
                        'dropped' => 'Dropped',
                    ]),
                Tables\Filters\TernaryFilter::make('is_favorite'),
                Tables\Filters\TernaryFilter::make('is_blocked'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListPersonalShelves::route('/'),
            'create' => Pages\CreatePersonalShelf::route('/create'),
            'edit' => Pages\EditPersonalShelf::route('/{record}/edit'),
        ];
    }
}

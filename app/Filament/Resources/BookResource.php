<?php

namespace App\Filament\Resources;

use App\Filament\Resources\BookResource\Pages;
use App\Filament\Resources\BookResource\RelationManagers;
use App\Models\Book;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class BookResource extends Resource
{
    protected static ?string $model = Book::class;

    protected static ?string $navigationIcon = 'heroicon-o-book-open';

    protected static ?string $navigationGroup = 'Library';

    protected static ?int $navigationSort = 1;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('title')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('slug')
                    ->required()
                    ->maxLength(255),
                Forms\Components\Select::make('author_id')
                    ->relationship('author', 'name')
                    ->required()
                    ->searchable()
                    ->preload(),
                Forms\Components\Select::make('category_id')
                    ->relationship('category', 'name')
                    ->required()
                    ->searchable()
                    ->preload(),
                Forms\Components\Textarea::make('description')
                    ->columnSpanFull(),
                Forms\Components\FileUpload::make('cover_image')
                    ->image()
                    ->directory('books/covers'),
                Forms\Components\TextInput::make('file_path')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\TextInput::make('preview_file_path')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\TextInput::make('isbn')
                    ->label('ISBN')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\DatePicker::make('published_date'),
                Forms\Components\TextInput::make('publisher')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\TextInput::make('language')
                    ->required()
                    ->maxLength(255)
                    ->default('en'),
                Forms\Components\TextInput::make('page_count')
                    ->numeric()
                    ->default(null),
                Forms\Components\TextInput::make('duration')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\TextInput::make('view_count')
                    ->required()
                    ->numeric()
                    ->default(0),
                Forms\Components\TextInput::make('download_count')
                    ->required()
                    ->numeric()
                    ->default(0),
                Forms\Components\TextInput::make('average_rating')
                    ->required()
                    ->numeric()
                    ->default(0),
                Forms\Components\Toggle::make('is_featured'),
                Forms\Components\Toggle::make('is_free'),
                Forms\Components\Toggle::make('is_editors_pick'),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('title')
                    ->searchable()
                    ->limit(40),
                Tables\Columns\TextColumn::make('slug')
                    ->searchable()
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\TextColumn::make('author.name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('category.name')
                    ->sortable(),
                Tables\Columns\ImageColumn::make('cover_image')
                    ->square()
                    ->size(50),
                Tables\Columns\TextColumn::make('language')
                    ->badge(),
                Tables\Columns\IconColumn::make('is_featured')
                    ->boolean()
                    ->toggleable(),
                Tables\Columns\IconColumn::make('is_free')
                    ->boolean()
                    ->toggleable(),
                Tables\Columns\TextColumn::make('average_rating')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('view_count')
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
                Tables\Filters\SelectFilter::make('category')
                    ->relationship('category', 'name'),
                Tables\Filters\TernaryFilter::make('is_featured'),
                Tables\Filters\TernaryFilter::make('is_free'),
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
        return [
            RelationManagers\ChaptersRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListBooks::route('/'),
            'create' => Pages\CreateBook::route('/create'),
            'edit' => Pages\EditBook::route('/{record}/edit'),
        ];
    }
}

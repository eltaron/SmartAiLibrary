<?php

namespace App\Filament\Resources;

use App\Filament\Resources\AiMetadataResource\Pages;
use App\Models\AiMetadata;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class AiMetadataResource extends Resource
{
    protected static ?string $model = AiMetadata::class;

    protected static ?string $navigationIcon = 'heroicon-o-sparkles';

    protected static ?string $navigationGroup = 'AI Engine';

    protected static ?int $navigationSort = 1;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('book_id')
                    ->relationship('book', 'title')
                    ->required()
                    ->searchable()
                    ->preload(),
                Forms\Components\Textarea::make('summary')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('detailed_summary')
                    ->label('Detailed Summary')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('keywords')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('entities')
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('sentiment')
                    ->maxLength(255)
                    ->default(null),
                Forms\Components\Textarea::make('vector_embeddings')
                    ->label('Vector Embeddings')
                    ->columnSpanFull(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('book.title')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('sentiment')
                    ->badge()
                    ->color(fn ($state) => match ($state) {
                        'positive' => 'success',
                        'neutral' => 'gray',
                        'negative' => 'danger',
                        default => 'gray',
                    })
                    ->searchable(),
                Tables\Columns\TextColumn::make('keywords')
                    ->limit(30)
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->defaultSort('created_at', 'desc')
            ->filters([])
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
            'index' => Pages\ListAiMetadata::route('/'),
            'create' => Pages\CreateAiMetadata::route('/create'),
            'edit' => Pages\EditAiMetadata::route('/{record}/edit'),
        ];
    }
}

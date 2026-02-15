<?php

namespace App\Filament\Resources\AiMetadataResource\Pages;

use App\Filament\Resources\AiMetadataResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListAiMetadata extends ListRecords
{
    protected static string $resource = AiMetadataResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make(),
        ];
    }
}

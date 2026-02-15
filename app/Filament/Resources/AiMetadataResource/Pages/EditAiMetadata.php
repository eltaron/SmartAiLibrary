<?php

namespace App\Filament\Resources\AiMetadataResource\Pages;

use App\Filament\Resources\AiMetadataResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditAiMetadata extends EditRecord
{
    protected static string $resource = AiMetadataResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}

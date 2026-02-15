<?php

namespace App\Filament\Resources\PersonalShelfResource\Pages;

use App\Filament\Resources\PersonalShelfResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditPersonalShelf extends EditRecord
{
    protected static string $resource = PersonalShelfResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}

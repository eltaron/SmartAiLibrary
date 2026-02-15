<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('personal_shelves', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('book_id')->constrained()->cascadeOnDelete();
            $table->enum('status', ['want_to_read', 'reading', 'completed', 'dropped'])->default('want_to_read');
            $table->boolean('is_favorite')->default(false); // القلب في التصميم
            $table->integer('current_page')->default(0); // أين توقف
            $table->integer('current_chapter_id')->nullable(); // للملفات الصوتية
            $table->timestamps();
        });
    }
    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('personal_shelves');
    }
};

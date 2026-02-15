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
        Schema::create('chapters', function (Blueprint $table) {
            $table->id();
            $table->foreignId('book_id')->constrained()->cascadeOnDelete();
            $table->string('title'); // Chapter 1: The Beginning
            $table->string('audio_url')->nullable(); // مسار الملف الصوتي
            $table->integer('duration_seconds')->default(0); // مدة المقطع
            $table->text('content_text')->nullable(); // لو عايزين النص مكتوب للفصل
            $table->integer('order_column')->default(1); // لترتيب الفصول
            $table->timestamps();
        });
    }
    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('chapters');
    }
};

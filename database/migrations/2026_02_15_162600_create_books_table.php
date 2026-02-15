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
        Schema::create('books', function (Blueprint $table) {
            $table->id();
            $table->string('title');
            $table->string('slug')->unique();
            $table->foreignId('author_id')->constrained()->cascadeOnDelete();
            $table->foreignId('category_id')->constrained()->cascadeOnDelete();
            $table->text('description')->nullable(); // للنص الذي سيستخدمه Semantic Search
            $table->string('cover_image')->nullable();

            // مسارات الملفات
            $table->string('file_path')->nullable(); // PDF/EPUB
            $table->string('preview_file_path')->nullable(); // عينة للقراءة

            // Metadata
            $table->string('isbn')->nullable();
            $table->date('published_date')->nullable();
            $table->string('publisher')->nullable();
            $table->string('language')->default('en');
            $table->integer('page_count')->nullable();
            $table->string('duration')->nullable(); // لو كتاب صوتي (ساعة ونصف مثلاً)

            // إحصائيات بسيطة للترشيحات
            $table->integer('view_count')->default(0);
            $table->integer('download_count')->default(0);
            $table->float('average_rating')->default(0);

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('books');
    }
};

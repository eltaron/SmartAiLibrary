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
        Schema::create('ai_analyses', function (Blueprint $table) {
            $table->id();
            $table->foreignId('book_id')->constrained()->cascadeOnDelete();
            $table->text('summary_short')->nullable(); // ملخص قصير
            $table->longText('summary_detailed')->nullable(); // ملخص طويل
            $table->json('keywords')->nullable(); // كلمات مفتاحية للاقتراحات
            $table->json('topics')->nullable(); // المواضيع
            $table->text('vector_embeddings')->nullable(); // لو هتخزن الـ Vector كنص للبحث (اختياري)
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('ai_analyses');
    }
};

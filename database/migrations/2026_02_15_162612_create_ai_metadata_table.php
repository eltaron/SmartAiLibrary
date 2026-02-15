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
        Schema::create('ai_metadata', function (Blueprint $table) {
            $table->id();

            // ربط مع جدول الكتب
            $table->foreignId('book_id')->constrained('books')->cascadeOnDelete();

            // ملخصات الذكاء الاصطناعي
            $table->text('summary')->nullable(); // الملخص القصير
            $table->longText('detailed_summary')->nullable(); // الملخص التفصيلي

            // تحليل المحتوى (NLP)
            $table->json('keywords')->nullable(); // كلمات مفتاحية (Tags)
            $table->json('entities')->nullable(); // أسماء أشخاص أو أماكن تم استخراجها من النص
            $table->string('sentiment')->nullable(); // (Positive, Neutral, Negative) لو محتاجه

            // للبحث الدلالي (Semantic Search)
            // سنخزن الـ Vector Embeddings هنا (عبارة عن مصفوفة أرقام طويلة)
            $table->json('vector_embeddings')->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('ai_metadata');
    }
};

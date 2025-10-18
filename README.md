# AI-Driven Exam Evaluator Agent

Akıllı, açıklanabilir ve gerçek zamanlı sonuç akışıyla yazılı sınav değerlendirmesi yapan agentic mimaride bir sistem.

## Özellikler

- PDF yükleme: Cevap anahtarı ve birden çok öğrenci PDF'i.
- Agentic değerlendirme hattı: Parser → Grader → Verifier → Feedback → Summary.
- Canlı sonuç: WebSocket ile her soru için anlık sonuçlar ve öğrenci özeti.
- Açıklanabilirlik: Gerekçeler, rubrik kırılımı, tam puan için öneriler.
- Takip soruları: Belirli soru/öğrenci bağlamında Q&A.

Detaylı mimari için: `ARCHITECTURE.md`.

## Teknoloji Yığını

- Backend: FastAPI, Python 3.10+, Pydantic, aiofiles
- Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS
- AI/LLM: OpenAI Chat Completions (gpt-4o-mini)
- PDF: pdfplumber

## Klasör Yapısı

- `backend/` FastAPI uygulaması, ajanlar ve servisler
- `frontend/` Next.js arayüzü
- `test_files/` Örnek PDF’ler (cevap anahtarı ve öğrenciler)

## Hızlı Başlangıç (Geliştirme)

1. Ortam değişkeni oluşturun (backend kökünde `.env`):

OPENAI_API_KEY=YOUR_OPENAI_KEY

2. Backend bağımlılıklarını kurun ve çalıştırın:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Frontend’i çalıştırın (yeni bir terminalde):

```bash
cd frontend
npm install
npm run dev
```

4. Tarayıcıdan http://localhost:3000 adresine gidin. PDF’leri yükleyip değerlendirmeyi başlatın.

5. İsteğe bağlı: Örnek iş başlatma (backend):

```bash
curl -X POST http://127.0.0.1:8000/api/dev/start-sample-job
```

## Backend API Özeti

- POST `/api/jobs`
  - FormData alanları: `answer_key` (PDF), `student_sheets` (PDF[])
  - Dönüş: `{ job_id, status }`
- GET `/api/dev/start-sample-job`
  - Örnek PDF’lerle değerlendirme başlatır (development amaçlı).
- WS `/api/jobs/{job_id}/ws`
  - JSON text mesajları: `job_started`, `partial_result`, `student_summary`, `job_done`, `error`.
- POST `/api/followup/{job_id}/{student_id}/{question_id}`
  - Body: `{ "query": "..." }` → Dönüş: `{ "answer": "..." }`

## Veri Sözleşmesi (Frontend-Backend)

- `partial_result` yükü: `{ job_id, student_id, question_id, score, max_score, justification, friendly_feedback?, verifier_status }`
- `student_summary` yükü: `{ student_id, summary_report }`
- `job_started`: `{ total_questions }`

Schema detayları için `backend/app/schemas.py`.

## Geliştirme Notları

- WebSocket kullanımı: Her job için tek WS kanalı. Event’ler JSON string olarak gönderilir ve frontend’de parse edilir.
- Bellek içi depolama: `StorageAgent` sonuçları ve sohbet geçmişini RAM’de tutar; kalıcı depolama eklemek kolaydır.
- Prompts: `backend/prompts/` altında. Gerekirse özelleştirin.

## Sorun Giderme

- 401/403 veya LLM hataları: `OPENAI_API_KEY` doğru ve backend ortamında yüklü mü?
- PDF metin çıkarma başarısız: `pdfplumber` bazı PDF’lerde sınırlı olabilir; OCR entegrasyonu gerekebilir.
- WebSocket bağlanmıyor: Backend 127.0.0.1:8000’de çalışıyor mu? CORS/Firewall?

## Lisans

Bu depo, proje sahibinin şartları doğrultusunda kullanılmaktadır.

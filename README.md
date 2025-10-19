# AI-Driven Exam Evaluator Agent

Akıllı, açıklanabilir ve gerçek zamanlı sonuç akışıyla yazılı sınav değerlendirmesi yapan agentic mimaride bir sistem.

## AI Araç Kullanımı

Projeye başlamadan önce tüm süreci zihnimde kurgulayıp kağıt üzerinde detaylı bir şekilde planladım ve mimari tasarımı oluşturdum. Her aşamayı adım adım tanımladıktan sonra, bu tasarımı yapay zekaya aktararak eksik kısımların belirlenmesini ve tamamlanmasını sağladım. Prompt engineering konusunda aldığım eğitim sayesinde, her ajan için amaç, görev ve istekler gibi unsurları içeren kendi prompt şablonlarımı (template) oluşturdum; eksik veya iyileştirilmesi gereken noktalar için yapay zekadan destek alarak bu şablonları optimize ettim. AI’den gelen geri bildirimler doğrultusunda şemayı ve kodun çalışma mantığını güncelleyerek daha sağlam bir proje mimarisi ortaya çıkardım. Geliştirme sürecinde proje kurulumunu ve önizleme ortamını kendim oluşturarak olası hata risklerini en aza indirdim. Ardından hazırladığım flowchart doğrultusunda klasör yapısını, .py dosyalarını ve her bir fonksiyonun şablonlarını tasarladım. Kodun hatasız ve verimli çalışması için özellikle try-except bloklarının oluşturulmasında ve bazı frontend geliştirmelerinde yapay zekadan destek alarak hem teknik altyapıyı hem de kullanıcı deneyimini optimize ettim.

## 🚀 Canlı Demo Linkleri

| Servis                | URL                                                    |
| :-------------------- | :----------------------------------------------------- |
| **Frontend (Arayüz)** | `[SENİN-FRONTEND-URL'Nİ-BURAYA-YAPIŞTIR (Vercel)]`     |
| **Backend (API)**     | `[SENİN-BACKEND-URL'Nİ-BURAYA-YAPIŞTIR (Render)]/docs` |

---

## ✨ Özellikler

- **PDF Yükleme:** Tek bir cevap anahtarı ve birden fazla öğrenci sınav kağıdını PDF formatında kabul eder.
- **Agentic Değerlendirme:** Her bir soru, modüler ve tekil sorumluluğa sahip otonom ajanlar tarafından değerlendirilir.
- **Canlı Sonuç Akışı:** WebSocket kullanılarak, her bir sorunun değerlendirme sonucu tamamlandığı anda arayüze canlı olarak yansıtılır.
- **Otomatik Düzeltme (Self-Correction):** `VerifierAgent`, `GraderAgent`'ın yaptığı mantıksal hataları (örn: puan/rubrik tutarsızlığı) tespit eder ve başka bir LLM çağrısı ile otomatik olarak düzeltmeye çalışır.
- **Sohbet Tabanlı Takip Soruları:** Kullanıcılar, her bir not kartı üzerinden "Neden tam puan alamadım?" gibi sorular sorabilir ve ajan, sohbet geçmişini hatırlayarak bağlama uygun cevaplar verir.
- **Detaylı Raporlama:** Her öğrenci için, güçlü ve zayıf yönlerini analiz eden, aksiyon odaklı tavsiyeler içeren bir özet rapor oluşturulur.

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

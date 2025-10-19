# Agentic System Architecture

## Genel Bakış

Bu sistem, tekil sorumluluk ilkesine göre tasarlanmış bir dizi bağımsız ajanın (agent) orkestrasyonuyla çalışan, uçtan uca sınav değerlendirme çözümüdür. Backend FastAPI ile, frontend Next.js (App Router) ile geliştirilmiştir. Gerçek zamanlı sonuç iletimi WebSocket üzerinden yapılır. LLM çağrıları OpenAI Chat Completions API ile gerçekleştirilir.

## Bileşenler ve Sorumluluklar

- OrchestratorAgent (`backend/app/orchestrator.py`)

  - İş (job) oluşturur, yüklenen dosyaları kaydeder, ajansal akışı sırayla tetikler.
  - PDFParser -> Grader -> Verifier -> Feedback zincirini yürütür; öğrenci tamamlandığında Summary üretir.
  - Sonuçları `ConnectionManager` aracılığıyla WebSocket ile frontend'e iletir.

- PDFParserAgent (`backend/app/agents/pdf_parser_agent.py`)

  - Cevap anahtarı ve öğrenci PDF'lerini `pdfplumber` kullanarak metne çevirir.
  - `NormalizerAgent` ile metni standardize eder.
  - `QuestionObject[]` ve `StudentAnswerObject[]` üretir. Soru ayırımı basit regex ("Soru N:") ile yapılır.

- NormalizerAgent (`backend/app/agents/normalizer_agent.py`)

  - Metindeki fazla boşlukları ve satır sonlarını normalize eder.

- GraderAgent (`backend/app/agents/grader_agent.py`)

  - LLM'e rubrik ve beklenen cevapla birlikte öğrenci cevabını verir; JSON biçiminde notlandırma döndürür.
  - Çıktı `GradingResult` olarak standardize edilir (audit için prompt ve ham yanıt saklanır).

- VerifierAgent (`backend/app/agents/verifier_agent.py`)

  - `rubric_breakdown` toplamı ile `score` tutarlılığını, aralık kontrollerini ve açıklama uzunluğunu doğrular.
  - Geçersiz sonuçlarda self-correction için LLM'e düzeltme denemesi yapar.

- FeedbackAgent (`backend/app/agents/feedback_agent.py`)

  - Onaylanmış not ve gerekçeden öğrenci-dostu bir geri bildirim metni üretir.

- SummaryAgent (`backend/app/agents/summary_agent.py`)

  - Bir öğrencinin tüm soru sonuçlarından kısa bir özet rapor üretir.

- FollowUpAgent (`backend/app/agents/follow_up_agent.py`)

  - Kullanıcıdan gelen takip sorularını, ilgili soru bağlamı ve geçmiş konuşma ile yanıtlar.

- StorageAgent (`backend/app/agents/storage_agent.py`)

  - Bellek içi (in-memory) sonuç ve sohbet geçmişi depoları sağlar. Kalıcı depolama için adaptör eklenebilir.

- ConnectionManager (`backend/app/services/connection_manager.py`)
  - Her job için tek bir WebSocket bağlantısını yönetir; event'leri JSON olarak gönderir.

## Veri Modelleri (Schemas)

- `QuestionObject { question_id, question_text, expected_answer, max_score, rubric, metadata }`
- `StudentAnswerObject { student_id, question_id, student_answer_text, metadata }`
- `GradingResult { job_id, student_id, question_id, score, max_score, rubric_breakdown, justification, advice_for_full_marks, llm_prompt, llm_raw_response, model, model_params, timestamp, verifier_status }`
- `StreamEvent { event: 'job_started'|'partial_result'|'student_summary'|'job_done'|'error', data: any }`
- `JobStatus { job_id, status }`

Bu modeller `backend/app/schemas.py` içinde Pydantic ile tanımlıdır ve frontend ile sözleşmeyi (contract) oluşturur.

## Akış (Yüksek Seviye)

1. Frontend'ten PDF yüklenir -> FastAPI `/api/jobs` endpoint'i dosyaları alır, job yaratır, arka planda işleme başlatır.
2. Orchestrator dosyaları `temp_uploads/{job_id}` altına yazar, anahtar ve öğrenci PDF'lerini parser'a gönderir.
3. Her öğrenci ve her soru için: Grader -> Verifier -> Feedback çalışır; `partial_result` eventi WebSocket ile gönderilir ve Storage'a kaydedilir.
4. Öğrenci bazında tüm sorular bitince `student_summary` eventi yayımlanır.
5. Tüm öğrenciler tamamlanınca `job_done` eventi yayımlanır.

## Sekans Diyagramı (Mermaid)

```mermaid
sequenceDiagram
        participant FE as Frontend (Next.js)
        participant API as FastAPI Backend
        participant ORC as OrchestratorAgent
        participant PAR as PDFParserAgent
        participant GRD as GraderAgent
        participant VER as VerifierAgent
        participant FB as FeedbackAgent
        participant SUM as SummaryAgent
        participant WS as ConnectionManager (WebSocket)
        participant ST as StorageAgent

        FE->>API: POST /api/jobs (answer_key, student_sheets)
        API->>ORC: create_job + save_uploaded_files
        ORC->>PAR: parse_answer_key + parse_student_answers
        loop For each student/question
                ORC->>GRD: grade_question()
                GRD-->>ORC: GradingResult
                ORC->>VER: verify_grading_result()
                VER-->>ORC: Verified GradingResult
                ORC->>FB: generate_feedback_for_question()
                FB-->>ORC: friendly_feedback
                ORC->>WS: send partial_result
                ORC->>ST: save_result()
        end
        ORC->>SUM: generate_summary_report()
        SUM-->>ORC: summary
        ORC->>WS: send student_summary, then job_done
```

## API Yüzeyi (Özet)

- `POST /api/jobs` — PDF yükleme ve değerlendirmeyi başlatma. Dönüş: `JobStatus`.
- `GET /api/dev/start-sample-job` — Örnek PDF'lerle hızlı başlatma (development).
- `WS /api/jobs/{job_id}/ws` — Gerçek zamanlı event akışı (JSON metin mesajları).
- `POST /api/followup/{job_id}/{student_id}/{question_id}` — Takip soruları (body: `{ query: string }`).

## Notlar ve Tasarım Tercihleri

- Streaming: Proje, SSE yerine WebSocket kullanır (tek bağlantı/iş). `ConnectionManager` job_id -> websocket eşlemesi tutar.
- Dayanıklılık: Şu an sonuç ve sohbet geçmişi RAM'de tutulur. Persistans için dosya/DB adaptörleri eklenebilir.
- Prompts: `backend/prompts/` altında; Grader/Verifier/Feedback/Summary/FollowUp için ayrı şablonlar.
- Güvenlik: `OPENAI_API_KEY` `.env` ile okunur (bkz. `backend/app/config.py`).

## Gelecek Geliştirmeler

- Kalıcı depolama (PostgreSQL veya S3 benzeri) için `StorageAgent` adaptörü.
- Çoklu model desteği ve akıllı retry/backoff.
- Çok kullanıcılı oturum ve yetkilendirme.

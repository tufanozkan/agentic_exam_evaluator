# Agentic System Architecture

## Genel Bakış

Bu sistem, "tek bir monolitik uygulama" yerine, her biri belirli ve izole bir göreve odaklanmış bağımsız ajanların (agents) bir araya gelerek bir iş akışını tamamladığı **agentic bir mimari** üzerine kurulmuştur. Bu yaklaşım; modülerlik, test edilebilirlik, değiştirilebilirlik ve ölçeklenebilirlik sağlar.

## Agent Kataloğu

1.  **PDFParserAgent** — Ham PDF dosyalarını, sonraki ajanların anlayabileceği yapısal `QuestionObject[]` veri formatına dönüştürür.
2.  **NormalizerAgent** — OCR'dan gelen metni temizler, standartlaştırır ve güvenilirlik skoru üretir.
3.  **QuestionEvaluatorAgent (GraderAgent)** — Her bir (soru, öğrenci cevabı) çiftini LLM kullanarak puanlar ve yapılandırılmış bir JSON çıktısı üretir.
4.  **VerifierAgent** — `GraderAgent`'ın çıktısının tutarlılığını (örneğin, rubrik toplamı puana eşit mi?) ve kalitesini kontrol eder. Hatalı veya düşük güvenilirlikli sonuçları işaretler.
5.  **FeedbackGeneratorAgent (ExplainerAgent)** — Onaylanmış notu, öğrenciye yönelik yapıcı ve rubriğe dayalı geri bildirime dönüştürür.
6.  **SummaryReportAgent** — Bir öğrencinin tüm notlarını analiz ederek güçlü/zayıf yönlerini ve konu eksikliklerini özetleyen bir rapor oluşturur.
7.  **FollowUpQueryAgent** — "Neden X puan aldım?" gibi kullanıcı sorularını, ilgili sorunun değerlendirme bağlamını kullanarak cevaplar.
8.  **StreamerAgent** — Tamamlanan her ara sonucu (örneğin, bir sorunun notu) frontend'e canlı olarak (SSE/WebSocket) yayınlar.
9.  **StorageAgent** — Tüm girdileri, istemleri (prompts), LLM yanıtlarını ve nihai sonuçları denetim (audit trail) amacıyla kaydeder.
10. **OrchestratorAgent (Coordinator)** — Tüm iş akışını yönetir, ajanları doğru sırada tetikler, yeniden denemeleri (retries) ve hata yönetimini üstlenir.

## Mimari Akış Şeması (Mermaid)

Bu şema, bir değerlendirme işinin sistem içinde nasıl aktığını gösterir.

```mermaid
graph TD
    A[Frontend: PDF'leri Yükle] --> B(OrchestratorAgent: İşi Başlat);
    B --> C{PDFParserAgent};
    C -->|Cevap Anahtarı| D[Structured Answer Key];
    C -->|Öğrenci Kağıtları| E[Structured Student Answers];

    subgraph Değerlendirme Döngüsü (Her Öğrenci/Soru İçin)
        B --> F(GraderAgent);
        D --> F;
        E --> F;
        F -->|Ham Not JSON| G(VerifierAgent);
        G -->|Onaylandı/İşaretlendi| H(FeedbackGeneratorAgent);
    end

    H --> I(StorageAgent: Sonucu Kaydet);
    H --> J(StreamerAgent: Sonucu Yayınla);
    J --> K[Frontend: Canlı Sonucu Göster];

    subgraph İş Sonu
        B -- Tüm sorular bitince --> L(SummaryReportAgent);
        I -- Tüm sonuçları oku --> L;
        L --> I;
        L --> J;
    end

    M[Frontend: Takip Sorusu Sor] --> N(FollowUpQueryAgent);
    I -- İlgili sonucu getir --> N;
    N --> M;
```

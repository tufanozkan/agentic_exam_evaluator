# AI-Driven Exam Evaluator Agent

Akıllı, açıklanabilir ve gerçek zamanlı sonuç akışıyla yazılı sınav değerlendirmesi yapan agentic mimaride bir sistem.

## AI Araç Kullanımı

Projeye başlamadan önce tüm süreci zihnimde kurgulayıp kağıt üzerinde detaylı bir şekilde planladım ve mimari tasarımı oluşturdum. Her aşamayı adım adım tanımladıktan sonra, bu tasarımı yapay zekaya aktararak eksik kısımların belirlenmesini ve tamamlanmasını sağladım. Prompt engineering konusunda aldığım eğitim sayesinde, her ajan için amaç, görev ve istekler gibi unsurları içeren kendi prompt şablonlarımı (template) oluşturdum; eksik veya iyileştirilmesi gereken noktalar için yapay zekadan destek alarak bu şablonları optimize ettim. AI’den gelen geri bildirimler doğrultusunda şemayı ve kodun çalışma mantığını güncelleyerek daha sağlam bir proje mimarisi ortaya çıkardım. Geliştirme sürecinde proje kurulumunu ve önizleme ortamını kendim oluşturarak olası hata risklerini en aza indirdim. Ardından hazırladığım flowchart doğrultusunda klasör yapısını, .py dosyalarını ve her bir fonksiyonun şablonlarını tasarladım. Kodun hatasız ve verimli çalışması için özellikle try-except bloklarının oluşturulmasında ve bazı frontend geliştirmelerinde yapay zekadan destek alarak hem teknik altyapıyı hem de kullanıcı deneyimini optimize ettim.

## 🚀 Canlı Demo Linkleri

| Servis                | URL                                                           |
| :-------------------- | :------------------------------------------------------------ |
| **Frontend (Arayüz)** | `[https://agentic-exam-evaluator.vercel.app/ (Vercel)]`       |
| **Backend (API)**     | `[https://agentic-exam-evaluator.onrender.com (Render)]/docs` |

---

## ✨ Özellikler

- **PDF Yükleme:** Tek bir cevap anahtarı ve birden fazla öğrenci sınav kağıdını PDF formatında kabul eder.
- **Agentic Değerlendirme:** Her bir soru, modüler ve tekil sorumluluğa sahip otonom ajanlar tarafından değerlendirilir.
- **Canlı Sonuç Akışı:** WebSocket kullanılarak, her bir sorunun değerlendirme sonucu tamamlandığı anda arayüze canlı olarak yansıtılır.
- **Otomatik Düzeltme (Self-Correction):** `VerifierAgent`, `GraderAgent`'ın yaptığı mantıksal hataları (örn: puan/rubrik tutarsızlığı) tespit eder ve başka bir LLM çağrısı ile otomatik olarak düzeltmeye çalışır.
- **Sohbet Tabanlı Takip Soruları:** Kullanıcılar, her bir not kartı üzerinden "Neden tam puan alamadım?" gibi sorular sorabilir ve ajan, sohbet geçmişini hatırlayarak bağlama uygun cevaplar verir.
- **Detaylı Raporlama:** Her öğrenci için, güçlü ve zayıf yönlerini analiz eden, aksiyon odaklı tavsiyeler içeren bir özet rapor oluşturulur.

---

## 🏛️ Mimari ve Ajanlar

Sistem, her biri belirli bir göreve odaklanmış otonom ajanların bir orkestratör tarafından yönetildiği modüler bir mimari üzerine kurulmuştur. Bu yapı, sistemin esnekliğini, test edilebilirliğini ve genişletilebilirliğini artırır.

### Akış Şeması
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
        G -- "Geçersizse Düzeltmeyi Dene" --> F;
        G -- "Geçerliyse" --> H(FeedbackGeneratorAgent);
    end

    H --> I(StorageAgent: Sonucu Kaydet);
    H --> J(ConnectionManager: Sonucu Yayınla);
    J --> K[Frontend: Canlı Sonucu Göster];

    subgraph İş Sonu
        B -- "Tüm sorular bitince" --> L(SummaryReportAgent);
        I -- "Tüm sonuçları oku" --> L;
        L --> I;
        L --> J;
    end
    
    M[Frontend: Takip Sorusu Sor] --> N(FollowUpQueryAgent);
    I -- "İlgili sonucu getir" --> N;
    N --> M;
```

### Ajan Kataloğu
- **`PDFParserAgent`**: Ham PDF dosyalarını yapısal metin nesnelerine dönüştürür.
- **`NormalizerAgent`**: Metinleri temizler ve standartlaştırır.
- **`GraderAgent`**: Her bir soruyu, rubriğe göre LLM kullanarak notlandırır ve detaylı bir JSON çıktısı üretir.
- **`VerifierAgent`**: `GraderAgent`'ın çıktısını kural tabanlı olarak kontrol eder. Hata bulursa, `Corrector` prompt'u ile hatayı düzelttirmeye çalışır.
- **`FeedbackAgent`**: Notu, öğrenciye yönelik yapıcı ve pedagojik bir geri bildirime dönüştürür.
- **`SummaryAgent`**: Bir öğrencinin tüm sınav performansını analiz ederek bütünsel bir rapor oluşturur.
- **`FollowUpQueryAgent`**: Bir soruya özel olarak sorulan takip sorularını, sohbet geçmişini hatırlayarak cevaplar.
- **`StorageAgent`**: Tüm sonuçları ve sohbet geçmişlerini, hafızada (in-memory) saklayarak sistemin "hafızası" görevini görür.
- **`OrchestratorAgent`**: Tüm bu ajanları doğru sırada çağıran, iş akışını yöneten ana şeftir.
- **`ConnectionManager` (Servis)**: WebSocket bağlantılarını yönetir ve `Orchestrator`'dan gelen anlık sonuçları doğru kullanıcıya iletir.

---

## 🧠 Mantık ve Akışın Açıklaması

Sistem, değerlendirme sürecini birkaç temel mantık üzerine kurmuştur:

#### Derecelendirme ve Geri Bildirim Mantığı
Her bir soru, `GraderAgent`'a sunulur. Bu ajan, "Düşünce Zinciri" (Chain-of-Thought) adı verilen bir prompt tekniği kullanır. Notu doğrudan vermek yerine, önce her bir rubrik maddesini ayrı ayrı değerlendirir ve bu adımları bir `reasoning_steps` dizisine kaydeder. Nihai puan, bu adımların toplamından elde edilir. Bu yaklaşım, notlandırmanın tutarlılığını ve şeffaflığını en üst düzeye çıkarır.

Not verildikten sonra, `FeedbackAgent` devreye girer. Bu ajan, "pedagojik bir sınav koçu" personasına bürünür ve ham notu, öğrenciye yönelik `Onaylama -> Açıklama -> Yol Gösterme` adımlarını izleyen, yapıcı ve motive edici bir geri bildirim metnine dönüştürür.

#### Otomatik Düzeltme Mantığı
`GraderAgent`'tan gelen sonuç, `VerifierAgent`'a gönderilir. Bu ajan, puan ile rubrik toplamı arasında bir tutarsızlık gibi kural tabanlı hataları kontrol eder. Bir hata bulursa, sistemi durdurmak yerine, hatayı ve orijinal çıktıyı başka bir LLM çağrısı ile "düzeltici" bir prompt'a gönderir. LLM'den gelen düzeltilmiş sonucu alarak akışa devam eder ve bu durumu "was_corrected: true" olarak işaretler. Bu, sistemin otonom ve kendi kendini iyileştiren bir yapıya sahip olduğunu gösterir.

#### Takip Sorularının Ele Alınışı
Bir kullanıcı bir soru kartı üzerinden takip sorusu sorduğunda, `FollowUpQueryAgent` devreye girer. Bu ajan, `StorageAgent`'ı kullanarak sadece o sorunun ilk değerlendirme bağlamını değil, aynı zamanda o soru için yapılmış **tüm önceki sohbet geçmişini** de alır. Tüm bu bilgiyi (ilk not + sohbet geçmişi + yeni soru) LLM'e tek bir prompt içinde sunarak, sohbetin devamlılığını ve bağlama uygunluğunu sağlar. Bu sayede her soru kartı, kendi hafızası olan küçük bir sohbet botuna dönüşür.

---

## 💻 Teknoloji Yığını

- **Backend:** FastAPI, Python 3.10+, Pydantic, aiofiles, WebSockets
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS
- **AI/LLM:** OpenAI Chat Completions (gpt-4o-mini)
- **PDF:** pdfplumber
- **Deployment:** Render (Backend), Vercel (Frontend)

---

## 🛠️ Hızlı Başlangıç (Yerelde Çalıştırma)

1.  **Repo'yu Klonlayın:**
    ```bash
    git clone cd exam-evaluator-agent
    ```

2.  **Backend Kurulumu:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    # .env.example dosyasını .env olarak kopyalayıp kendi OpenAI API anahtarınızı girin
    uvicorn app.main:app --reload
    ```

3.  **Frontend Kurulumu (Yeni bir terminalde):**
    ```bash
    cd frontend
    npm install
    # .env.local.example dosyasını .env.local olarak kopyalayın
    npm run dev
    ```
    Uygulama `http://localhost:3000` adresinde çalışacaktır.

---

Schema detayları için `backend/app/schemas.py`.

## ⚖️ Bilinen Sınırlamalar ve Varsayımlar

- **PDF Formatı:** Mevcut parser, sadece metin tabanlı PDF'leri desteklemektedir. Taranmış veya resim içeren PDF'lerdeki metinleri okuyamaz.
- **Kalıcı Depolama:** `StorageAgent` şu an için tüm verileri sunucu hafızasında (in-memory) tutmaktadır. Sunucu yeniden başladığında değerlendirme sonuçları ve sohbet geçmişleri kaybolur.
- **Prompt Bağımlılığı:** Sistemin kalitesi, `backend/prompts/` klasöründeki prompt şablonlarının kalitesine doğrudan bağlıdır. Farklı sınav türleri (örn: matematik) için bu prompt'ların özelleştirilmesi gerekebilir.

---

## Sorun Giderme

- 401/403 veya LLM hataları: `OPENAI_API_KEY` doğru ve backend ortamında yüklü mü?
- PDF metin çıkarma başarısız: `pdfplumber` bazı PDF’lerde sınırlı olabilir; OCR entegrasyonu gerekebilir.
- WebSocket bağlanmıyor: Backend 127.0.0.1:8000’de çalışıyor mu? CORS/Firewall?

## Lisans

Bu depo, proje sahibinin şartları doğrultusunda kullanılmaktadır.

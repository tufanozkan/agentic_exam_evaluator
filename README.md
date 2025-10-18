# AI-Driven Exam Evaluator Agent

## Genel Bakış

Bu proje, yazılı sınav kağıtlarını sağlanan bir cevap anahtarına göre otomatik olarak değerlendiren, yapay zeka tabanlı bir agentic sistemdir. Sistemin temel amacı sadece notlandırma yapmak değil, aynı zamanda her bir not için şeffaf, açıklanabilir ve denetlenebilir bir süreç sunmaktır.

## Temel Özellikler

- **PDF Yükleme:** Cevap anahtarı ve çoklu öğrenci kağıtlarını PDF formatında kabul eder.
- **Agentic Değerlendirme:** Her soru, modüler ve tekil sorumluluğa sahip ajanlar tarafından işlenir.
- **Aşamalı Sonuç Yayını:** Sonuçlar, değerlendirme tamamlandıkça (her soru için) arayüze canlı olarak yansıtılır.
- **Açıklanabilir Puanlama (Explainability):** Her puanın arkasındaki mantığı ve tam puan için ne yapılması gerektiğini açıklar.
- **Takip Soruları:** Kullanıcıların "Neden bu sorudan 8 aldım?" gibi sorular sormasına ve bağlama duyarlı cevaplar almasına olanak tanır.

## Mimari

Sistemin detaylı mimarisi, ajanların sorumlulukları ve aralarındaki etkileşim için lütfen [ARCHITECTURE.md](ARCHITECTURE.md) dosyasına göz atın.

## Teknoloji Stack'i

- **Backend:** Python 3.10+, FastAPI
- **Frontend:** Streamlit (Hızlı prototipleme için)
- **AI/LLM:** OpenAI API (veya benzeri)
- **PDF İşleme:** `pdfplumber`

## Kurulum ve Çalıştırma

... (Bu bölümü daha sonra dolduracağız) ...

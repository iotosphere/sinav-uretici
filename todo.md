### 🎯 Proje Hedefi

Öğretmenlerin yüklediği PDF ders notlarından, kurumsal formata uygun ve çoklu LLM (OpenAI, Anthropic, Gemini) destekli sınav kağıtları oluşturmak.

### 🌟 Faz 1: Altyapı ve Çekirdek Fonksiyonellik (Hemen Başlanmalı)


| **Durum** | **Görev**                                     | **Öncelik** | **Atanan** | **Tahmini Süre** | **Notlar**                                                                                                                                                     |
| --------- | ---------------------------------------------- | ------------ | ---------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ☐        | **Geliştirme Ortamı Kurulumu**               | Yüksek      | DevOps     | 0.5 gün          | `venv`,`requirements.txt`(tüm paketler),`.env`(API key şablonları) ayarları.                                                                               |
| ☐        | **`app.py`İskeleti**                          | Yüksek      | Frontend   | 1 gün            | Streamlit sayfa yapılandırması, Sidebar (API Key girişi) ve Metadata (Okul, Ders, Sınıf) girişlerini tamamla.                                           |
| ☐        | **`PDF Parser`Entegrasyonu**                   | Yüksek      | Backend    | 1 gün            | `extract_text_from_pdf`(pypdf) ve`get_module_chunks`(basit kelime bazlı bölme) fonksiyonlarını`app.py`içine al.                                           |
| ☐        | **`AI Generator`(JSON Çıktısı) Tamamlama** | Kritik       | Backend    | 2 gün            | `soru_uret`fonksiyonunu,**OpenAI**,**Anthropic**ve**Gemini 2.0 Flash**için JSON çıktı zorlaması yaparak tamamla. Hata yönetimi (`try/except`) eklenmeli. |

---

### 🛠️ Faz 2: Çıktı ve Kullanıcı Akışı Geliştirme (Faz 1 Tamamlandıktan Sonra)


| **Durum** | **Görev**                           | **Öncelik** | **Atanan** | **Tahmini Süre** | **Notlar**                                                                                                                                                                      |
| --------- | ------------------------------------ | ------------ | ---------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ☐        | **Kurumsal DOCX Builder (Tablolar)** | Kritik       | Backend    | 2 gün            | `build_docx_exam`fonksiyonunu, PRD'de belirtilen**karmaşık tablo tabanlı**sınav başlığı ve puanlama formatına uygun hale getir. Cevap anahtarı ayrı sayfada olmalı. |
| ☐        | **Modül Seçimi Mantığı**        | Yüksek      | Frontend   | 0.5 gün          | `st.multiselect`ile kullanıcının seçtiği modül metinlerini birleştirerek`soru_uret`fonksiyonuna gönderme mantığını bağla.                                          |
| ☐        | **Hata ve Yükleme Bildirimleri**    | Orta         | Frontend   | 0.5 gün          | `st.spinner`(Yükleniyor) ve`st.success`/`st.error`(API/PDF hataları) mesajlarını kullanıcı dostu şekilde entegre et.                                                     |
| ☐        | **İndirme Mekanizması**            | Yüksek      | Frontend   | 0.5 gün          | Word çıktısı hazırlandığında`st.download_button`'ı doğru`mime`tipiyle (application/vnd.openxmlformats-officedocument.wordprocessingml.document) bağla.               |

---

### 🐛 Faz 3: Test ve Optimizasyon


| **Durum** | **Görev**                            | **Öncelik** | **Atanan** | **Tahmini Süre** | **Notlar**                                                                                                                                                                 |
| --------- | ------------------------------------- | ------------ | ---------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ☐        | **Uçtan Uca Test (E2E)**             | Yüksek      | QA         | 1 gün            | Her LLM sağlayıcısı ile farklı PDF'ler kullanılarak test et. Özellikle JSON çıktısının bozulup bozulmadığını kontrol et.                                   |
| ☐        | **PDF Chunking Optimizasyonu**        | Orta         | Backend    | 0.5 gün          | Basit kelime tabanlı bölme yerine, sayfa numarası veya başlık (heading) algılama gibi daha akıllı bölme yöntemlerini değerlendir (Gelecek faz için opsiyonel). |
| ☐        | **Kod İyileştirmesi ve Temizliği** | Düşük     | Backend    | 0.5 gün          | Tüm kod boyunca PEP 8 standartlarına uyulduğunu ve gereksiz yorum/kod kalmadığını kontrol et.                                                                       |

### 🛑 Engeller (Blockers)

* **API Anahtarları:** Projenin çalışması için her üç AI sağlayıcısının (Gemini, GPT, Claude) geçerli bir API anahtarına erişim sağlanmalıdır.
* **JSON Çıktı Kalitesi:** AI'ların zorlu metinlerde bile her zaman %100 temiz JSON döndüreceği garanti edilmelidir. (Gerektiğinde `response_mime_type` gibi teknik ayarlar kullanılmalıdır.)

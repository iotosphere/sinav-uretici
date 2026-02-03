# 🤖 AI Destekli Sınav Hazırlama Botu

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Türkiye'de öğretmenler için geliştirilmiş, modern eğitim standartlarına uygun, açık uçlu sınav soruları üreten yapay zeka destekli uygulama.**

## ✨ Özellikler

- 🤖 **4 Farklı AI Modeli**: OpenAI (GPT-4o), Google (Gemini 2.0), DeepSeek (V3), MiniMax (M2.1)
- 📝 **Açık Uçlu Sorular**: Çağdaş eğitim yaklaşımlarına uygun, üst düzey düşünme becerisi gerektiren sorular
- 📊 **Bloom Taksonomisi**: Hatırlama, Anlama, Uygulama, Analiz, Değerlendirme seviyelerinde dengeli dağılım
- 📄 **Word Çıktısı**: Kurumsal sınav kağıdı formatında DOCX dosyası
- 🔍 **Akıllı RAG Sistemi**: Büyük PDF'lerde semantik arama ile en ilgili içeriği bulma
- 📈 **Otomatik Puanlama**: Her soru için kriter tabanlı değerlendirme sistemi
- 🎯 **Kazanım Odaklı**: Öğrenme hedeflerine uygun soru üretimi

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.9 veya üzeri
- 4 GB RAM (önerilen: 8 GB)
- İnternet bağlantısı (API çağrıları için)

### Kurulum

1. **Projeyi klonlayın:**
```bash
git clone https://github.com/kullaniciadi/sinav-uretici.git
cd sinav-uretici
```

2. **Sanal ortam oluşturun:**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Ortam değişkenlerini ayarlayın (.env dosyası oluşturun):**
```bash
# .env dosyası içeriği (isteğe bağlı - UI'dan da girilebilir)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=sk-...
MINIMAX_API_KEY=...
```

### Çalıştırma

```bash
streamlit run app.py
```

Uygulama varsayılan olarak `http://localhost:8501` adresinde çalışacaktır.

## 📖 Kullanım Kılavuzu

### 1. API Anahtarı Alma

#### 🔑 OpenAI (GPT-4o)
1. [OpenAI Platform](https://platform.openai.com) adresine gidin
2. Kaydolun ve API anahtarı oluşturun
3. Ödeme yöntemi ekleyin (ücretsiz kredi ile başlayabilirsiniz)

#### 🔑 Google Gemini
1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresine gidin
2. API anahtarı oluşturun
3. Ücretsiz katman: Günde 60 istek

#### 🔑 DeepSeek
1. [DeepSeek Platform](https://platform.deepseek.com) adresine gidin
2. Kaydolun ve API anahtarı oluşturun
3. Yüksek performanslı ve uygun fiyatlı

#### 🔑 MiniMax
1. [MiniMax Platform](https://www.minimaxi.com/platform) adresine gidin
2. API anahtarı alın
3. Not: Token limiti nedeniyle max 5 soru önerilir

### 2. Sınav Oluşturma Adımları

1. **PDF Yükleyin**: Ders notlarınızı veya ders içeriği dokümanınızı yükleyin
2. **Modül Seçin**: İçerik otomatik modüllere ayrılacak, istediklerinizi seçin
3. **Soru Sayısı**: 3-20 arası soru sayısı seçin (MiniMax için max 5)
4. **AI Modeli**: Kullanmak istediğiniz modeli seçin
5. **RAG Sistemi**: Büyük PDF'ler için önerilir
6. **Oluştur**: "Soruları Oluştur" butonuna tıklayın
7. **İndirin**: Word dosyasını indirin

### 3. Çıktı Formatı

**Öğrenci Kağıdı:**
- Sınav başlık bilgileri (okul, ders, öğretmen)
- Soru numaraları ve puan değerleri (toplam 100 puan)
- Açık uçlu sorular ve geniş cevap alanları

**Cevap Anahtarı (Öğretmen İçin):**
- Beklenen model cevaplar
- Puanlama kriterleri
- Bloom seviyesi bilgisi

## 🛠️ Teknik Detaylar

### Mimarisi

```
sinav-uretici/
├── app.py                    # Ana Streamlit uygulaması
├── utils/
│   ├── ai_generator.py       # AI modelleri entegrasyonu
│   ├── docx_builder.py         # Word dosyası oluşturma
│   ├── pdf_parser.py           # PDF metin çıkarma
│   └── rag.py                  # RAG (Retrieval-Augmented Generation)
├── requirements.txt
├── .env.example
└── README.md
```

### AI Modelleri Karşılaştırması

| Model | Ücretsiz Limit | Hız | Kalite | Önerilen Soru Sayısı |
|-------|----------------|-----|--------|---------------------|
| OpenAI GPT-4o | Kredi tabanlı | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 10-20 |
| Google Gemini | 60 istek/gün | ⚡⚡⚡ | ⭐⭐⭐⭐ | 10-20 |
| DeepSeek V3 | Uygun fiyatlı | ⚡⚡ | ⭐⭐⭐⭐⭐ | 10-20 |
| MiniMax M2.1 | Token limitli | ⚡⚡ | ⭐⭐⭐⭐ | Max 5 |

### RAG Sistemi

Büyük PDF dosyalarında (100+ sayfa):
- Metni otomatik modüllere ayırma
- Semantik vektör araması
- En ilgili içeriği AI'a aktarma
- Token optimizasyonu

## 📝 Örnek Soru Yapısı

```json
{
  "sorular": [
    {
      "no": 1,
      "soru_metni": "Ohm Kanunu'nun matematiksel ifadesini yazın ve gerilim, akım, direnç arasındaki ilişkiyi açıklayın.",
      "soru_tipi": "Kavramsal-Açık Uçlu",
      "zorluk": "Orta",
      "bloom_seviyesi": "Anlama",
      "kazanım": "Elektrik devrelerinde temel kavramları açıklama",
      "beklenen_cozum": "V = I × R formülü ile ifade edilir. Gerilim akımla doğru, dirençle ters orantılıdır.",
      "puanlama_kriterleri": "5 puan: Formül doğru\n5 puan: Gerilim-akım ilişkisi\n5 puan: Gerilim-direnç ilişkisi\n5 puan: Açıklama tam",
      "ipucu": "Birimleri düşünün: Volt, Amper, Ohm"
    }
  ]
}
```

## 🎓 Eğitim Kullanımı

### Çağdaş Eğitim Yaklaşımları

Bu uygulama, modern eğitim metodolojilerine uygun olarak tasarlanmıştır:

- ✅ Açık uçlu soru formatı (Yapılandırılmış grid sistemine uygun)
- ✅ Üst düzey düşünme becerileri (Bloom Taksonomisi)
- ✅ Öğrenme hedeflerine uygunluk
- ✅ Çoklu zeka teorisi gözetimi
- ✅ Öğrenci merkezli değerlendirme
- ✅ Kriter bazlı puanlama

### Tavsiye Edilen Kullanım

- **Haftalık Değerlendirme**: 5 soru, 20 dakika
- **Ara Sınav**: 10 soru, 40 dakika  
- **Dönem Sonu**: 15-20 soru, 60 dakika

## 🔧 Sorun Giderme

### Sık Karşılaşılan Hatalar

**1. "JSON format hatası"**
- Soru sayısını azaltın (MiniMax için max 5)
- Daha kısa bir PDF bölümü seçin
- Başka bir AI modeli deneyin

**2. "API kotası aşıldı"**
- Google Gemini: 60 istek/gün limiti
- Ücretsiz katmanı kontrol edin
- Farklı bir API anahtarı deneyin

**3. "PDF okunamadı"**
- Taralı (image) PDF'ler desteklenmiyor
- OCR gerektiren dosyalar için önce metne çevirin

**4. "Türkçe karakter hatası"**
- MiniMax'te otomatik düzeltiliyor (ı→i, ş→s)
- Diğer modellerde sorun olmamalı

### İletişim & Destek

Sorularınız veya önerileriniz için:
- GitHub Issues: [Issues sekmesi](https://github.com/kullaniciadi/sinav-uretici/issues)
- E-posta: sizin@epostaniz.com

## 🤝 Katkıda Bulunma

1. Bu projeyi fork edin
2. Yeni bir branch oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: X'`)
4. Branch'inizi push edin (`git push origin yeni-ozellik`)
5. Pull Request açın

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Özgürce kullanabilir, değiştirebilir ve dağıtabilirsiniz.

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynak projelerini kullanmaktadır:
- [Streamlit](https://streamlit.io/) - Web arayüzü
- [OpenAI](https://openai.com/) / [Google](https://ai.google.dev/) / [DeepSeek](https://deepseek.com/) / [MiniMax](https://www.minimaxi.com/) - AI modelleri
- [python-docx](https://python-docx.readthedocs.io/) - Word dosyası oluşturma
- [ChromaDB](https://www.trychroma.com/) - Vektör veritabanı

---

**Not:** Bu uygulama eğitim amaçlı geliştirilmiştir. Üretilen soruların ders içeriğine uygunluğunu kontrol etmek kullanıcının sorumluluğundadır.

⭐ **Projeyi beğendiyseniz GitHub'da yıldız vermeyi unutmayın!** ⭐
import google.generativeai as genai
import json

def create_system_prompt(metin_icerigi, soru_sayisi, ders_adi="Ders"):
    """AI için gelişmiş soru oluşturma prompt'unu hazırlar - GÜNCELLENMİŞ VE SADELEŞTİRİLMİŞ"""
    
    # Soru sayısına göre dağılım hesapla
    hatirlama = max(1, soru_sayisi // 4)
    anlama = max(1, soru_sayisi // 4)
    uygulama = max(1, soru_sayisi // 4)
    analiz = max(1, soru_sayisi // 4)
    degerlendirme = max(1, soru_sayisi // 5) if soru_sayisi >= 5 else 0
    
    # Fazla hesaplananları düzelt
    toplam_bloom = hatirlama + anlama + uygulama + analiz + degerlendirme
    if toplam_bloom > soru_sayisi:
        hatirlama = max(1, hatirlama - 1)
    
    kolay = max(1, soru_sayisi // 4)
    orta = soru_sayisi // 2
    zor = soru_sayisi - kolay - orta
    
    # Her sorunun puan değeri (toplam 100 puan için)
    puan_per_soru = 100 // soru_sayisi
    kalan_puan = 100 - (puan_per_soru * soru_sayisi)
    
    prompt = f"""Sen Türkiye'de MEB müfredatına hakim bir ölçme uzmanısın. Aşağıdaki içerikten {soru_sayisi} adet kaliteli AÇIK UÇLU sınav sorusu ve detaylı çözümü üret.

DERS: {ders_adi}

METİN İÇERİĞİ:
{metin_icerigi}

📊 SINAV YAPISI:
• Toplam {soru_sayisi} soru
• Toplam puan: 100
• Her soru: {puan_per_soru} puan (bazıları {puan_per_soru+1} puan olabilir dağılım için)

📊 BLOOM DAĞILIMI:
• Hatırlama: {hatirlama} soru (temel kavramlar)
• Anlama: {anlama} soru (açıklama, sınıflandırma)
• Uygulama: {uygulama} soru (problem çözme)
• Analiz: {analiz} soru (karşılaştırma, ilişkiler)
• Değerlendirme: {degerlendirme} soru (yargılama)

Zorluk: Kolay={kolay}, Orta={orta}, Zor={zor}

📝 AÇIK UÇLU SORU KURALLARI:
1. Her soru net ve anlaşılır olmalı
2. Öğrenci kendi cümleleriyle cevap yazabilmeli (seçenek YOK)
3. Akademik Türkçe kullan
4. Metinde olan bilgilerden sor
5. Sorular üst düzey düşünme becerisi gerektirmeli (hatırlama değil, anlama/uygulama/analiz)

📝 ÇÖZÜM VE PUANLAMA FORMATI:
Her soru için şunları içeren detaylı çözüm yaz:
- BEKLENEN ÇÖZÜM: Öğretmenin beklediği detaylı model cevap
- PUANLAMA KRİTERLERİ: Bu soru {puan_per_soru} puan değerindedir. Kriterler:
  * {puan_per_soru//4} puan: ... (kriter 1)
  * {puan_per_soru//4} puan: ... (kriter 2)
  * {puan_per_soru//4} puan: ... (kriter 3)
  * {puan_per_soru - 3*(puan_per_soru//4)} puan: ... (kriter 4)
- YAYGIN HATALAR: Öğrencilerin sık yaptığı hatalar

📋 ÖRNEK (5 soru için - her biri 20 puan):
{{
  "no": 1,
  "soru_metni": "Bir elektrik devresinde gerilim, akım ve direnç arasındaki ilişkiyi açıklayın. Ohm Kanunu'nu kullanarak bu ilişkiyi matematiksel olarak ifade edin.",
  "soru_tipi": "Kavramsal-Açık Uçlu",
  "zorluk": "Orta",
  "bloom_seviyesi": "Anlama",
  "kazanım": "Elektrik devrelerinde temel kavramları açıklama",
  "beklenen_cozum": "Ohm Kanunu'na göre bir devrede gerilim (V), akım (I) ve direnç (R) arasında V = I × R ilişkisi vardır. Gerilim, akımla doğru orantılı, dirençle ters orantılıdır. Birimi Volt'tur. Akım birimi Amper, direnç birimi Ohm'dur.",
  "puanlama_kriterleri": "5 puan: Gerilim tanımı doğru\n5 puan: Akım tanımı doğru\n5 puan: Direnç tanımı doğru\n5 puan: V=I×R formülü doğru",
  "yaygin_hatalar": ["Formülü ters yazma", "Birimleri karıştırma", "Orantıyı ters kurma"],
  "ipucu": "Üç temel büyüklüğü tanımlayın",
  "kaynak": "Metin: Elektrik Devreleri Bölümü"
}}

📋 GEREKLİLER:
1. TÜM {soru_sayisi} soruyu üret
2. Her soru {puan_per_soru} puan değerinde (toplam 100 puan)
3. JSON formatında tek bir obje döndür
4. "sorular" array'i içinde tüm sorular olsun
5. Türkçe karakterleri doğru kullan (ışğüöç)
6. JSON dışında hiçbir metin yazma
7. Kesinlikle SEÇENEK (A,B,C,D,E) kullanma - açık uçlu soru!

Şimdi {soru_sayisi} adet AÇIK UÇLU soruyu (toplam 100 puan) JSON formatında üret."""
    
    return prompt


def create_quality_check_prompt(sorular_json):
    """Üretilen soruların kalitesini kontrol eden prompt."""
    return f"""
    Ölçme ve değerlendirme uzmanı olarak aşağıdaki soruları pedagojik kalite açısından değerlendir:
    
    {sorular_json}
    
    DEĞERLENDİRME KRİTERLERİ:
    1. **Anlaşılırlık:** Soru metni açık mı? Belirsiz ifade var mı?
    2. **Akademik Dil:** Dil düzeyi uygun mu? Gramer hataları var mı?
    3. **Bloom Uygunluğu:** Belirtilen seviyeye uygun mu?
    4. **Tek Doğruluk:** Sadece bir doğru cevap var mı?
    5. **Çözüm Kalitesi:** Çözüm adımları yeterli mi?
    
    JSON formatında değerlendirme döndür:
    {{
        "genel_degerlendirme": "Mükemmel/İyi/Orta/Düşük",
        "puan": 85,
        "soru_degerlendirmeleri": [
            {{
                "soru_no": 1,
                "anlasilirlik": 10,
                "akademik_dil": 9,
                "bloom_uygunlugu": 8,
                "tek_dogruluk": 10,
                "cozum_kalitesi": 9,
                "oneri": "..."
            }}
        ],
        "genel_oneriler": ["..."]
    }}
    """

def kalite_kontrolu_yap(provider, api_key, sorular_json, gemini_endpoint=None):
    """
    Üretilen soruların kalitesini kontrol eder ve gerekirse yeniden üretir.
    
    Args:
        provider: AI sağlayıcısı
        api_key: API anahtarı
        sorular_json: Kontrol edilecek sorular (JSON formatında)
        gemini_endpoint: Gemini için özel endpoint
        
    Returns:
        tuple: (kalite_puani, oneriler)
    """
    try:
        quality_prompt = create_quality_check_prompt(sorular_json)
        
        if "Google" in provider:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            response = model.generate_content(
                quality_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 2000,
                    "response_mime_type": "application/json",
                }
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
                response_text = response_text.strip()
            
            quality_data = json.loads(response_text)
            return quality_data.get("puan", 0), quality_data.get("genel_oneriler", [])
        
        elif "DeepSeek" in provider:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Sen bir ölçme ve değerlendirme uzmanısın."},
                    {"role": "user", "content": quality_prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            quality_data = json.loads(response.choices[0].message.content.strip())
            return quality_data.get("puan", 0), quality_data.get("genel_oneriler", [])
            
        return 0, ["Kalite kontrolü yapılamadı"]
        
    except Exception as e:
        print(f"Kalite kontrolü hatası: {e}")
        return 0, [f"Kalite kontrolü sırasında hata: {str(e)}"]


def soru_uret(provider, api_key, metin_icerigi, gemini_endpoint=None, soru_sayisi=10, max_deneme=3, ders_adi="Ders"):
    """
    Verilen metin içeriğinden AI kullanarak kaliteli soru üretir.
    Çok aşamalı kalite kontrolü ile birlikte çalışır.
    
    Args:
        provider: AI sağlayıcısı ("Google", "OpenAI", vb.)
        api_key: API anahtarı
        metin_icerigi: Soru üretilecek metin
        gemini_endpoint: Gemini için özel endpoint (opsiyonel)
        soru_sayisi: Üretilecek soru sayısı
        max_deneme: Maksimum deneme sayısı
        ders_adi: Ders adı (prompt kalitesi için)
        
    Returns:
        str: JSON formatında sorular
    """
    
    en_iyi_sonuc = None
    en_yuksek_puan = 0
    en_iyi_sorular = []
    
    for deneme in range(max_deneme):
        print(f"🔄 Soru üretimi deneme {deneme + 1}/{max_deneme}")
        
        # Prompt oluştur (ders_adi parametresini ekle)
        prompt = create_system_prompt(metin_icerigi, soru_sayisi, ders_adi)
        
        # Soruları üret (metin_icerigi ve soru_sayisi'ni de geçir - MiniMax için gerekli)
        sorular_json = generate_questions_with_provider(provider, api_key, prompt, gemini_endpoint, metin_icerigi, soru_sayisi)
        
        # Hata kontrolü
        try:
            sorular_data = json.loads(sorular_json)
            if "error" in sorular_data:
                print(f"❌ Hata: {sorular_data['error']}")
                continue
            
            # Soru listesini al
            sorular_list = sorular_data.get("sorular", [])
            
            if not sorular_list:
                print("❌ Soru listesi boş")
                continue
            
            print(f"📝 {len(sorular_list)} soru üretildi")
            
            # Kapsamlı kalite kontrolü yap
            kalite_raporu = kapsamli_kalite_kontrolu(sorular_list, metin_icerigi)
            kalite_puani = kalite_raporu.get("toplam_puan", 0)
            
            print(f"📊 Kalite puanı: {kalite_puani}/100")
            print(f"📋 Bloom dağılımı uyumu: {kalite_raporu.get('bloom_uyumu', 'Bilinmiyor')}")
            
            # Sorunları ve önerileri göster
            if kalite_raporu.get("sorunlar"):
                print(f"⚠️ Tespit edilen sorunlar: {', '.join(kalite_raporu['sorunlar'][:3])}")
            
            # En iyi sonucu sakla
            if kalite_puani > en_yuksek_puan:
                en_yuksek_puan = kalite_puani
                en_iyi_sonuc = sorular_json
                en_iyi_sorular = sorular_list
            
            # Kalite yeterli ise döngüden çık (EŞİK DEĞERLER DÜŞÜRÜLDÜ)
            if kalite_puani >= 70:  # 80'den 70'e düşürüldü
                print(f"✅ Yüksek kalite seviyesine ulaşıldı: {kalite_puani}")
                return sorular_json
            elif kalite_puani >= 55:  # 65'den 55'e düşürüldü
                print(f"✅ Kabul edilebilir kalite: {kalite_puani}")
                # Düşük puanlı soruları elemeye çalış
                filtrelenmis_sorular = sorular_filtrele_ve_zenginleştir(sorular_list, kalite_raporu, metin_icerigi)
                if len(filtrelenmis_sorular) >= soru_sayisi * 0.6:  # 0.7'den 0.6'ya düşürüldü
                    sorular_data["sorular"] = filtrelenmis_sorular[:soru_sayisi]
                    return json.dumps(sorular_data, ensure_ascii=False, indent=2)
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON format hatası: {e}")
            continue
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
            continue
    
    # Tüm denemeler bittiğinde en iyi sonucu döndür
    if en_iyi_sonuc:
        print(f"⚠️ En yüksek kalite: {en_yuksek_puan}/100 (Hedef: 80+)")
        return en_iyi_sonuc
    else:
        return json.dumps({
            "error": "Tüm denemeler başarısız oldu.",
            "oneri": "Lütfen metni kısaltın, soru sayısını azaltın veya farklı bir AI sağlayıcısı deneyin."
        }, ensure_ascii=False)


def kapsamli_kalite_kontrolu(sorular, metin_icerigi):
    """
    Üretilen soruların kapsamlı kalite analizini yapar - DAHALENİENT
    
    Args:
        sorular: Soru listesi
        metin_icerigi: Kaynak metin
        
    Returns:
        dict: Kalite raporu
    """
    rapor = {
        "toplam_puan": 0,
        "sorunlar": [],
        "oneri": [],
        "bloom_uyumu": "Bilinmiyor",
        "zorluk_dagilimi": "Uygun",
        "soru_kaliteleri": []
    }
    
    if not sorular:
        rapor["sorunlar"].append("Soru listesi boş")
        return rapor
    
    # Metinden anahtar kelimeleri çıkar (basit yöntem)
    metin_kelimeler = set(metin_icerigi.lower().split())
    metin_kelimeler = {k for k in metin_kelimeler if len(k) > 3}
    
    toplam_puan = 0
    soru_puanlari = []
    kritik_hatali_soru_sayisi = 0
    
    for i, soru in enumerate(sorular):
        soru_puan = 100
        soru_hatalari = []
        kritik_hata_var = False
        
        # 1. Temel alan kontrolü (KRİTİK ALANLAR)
        kritik_fields = ["soru_metni", "dogru_cevap"]
        for field in kritik_fields:
            if field not in soru or not soru.get(field):
                soru_puan -= 25
                kritik_hata_var = True
                soru_hatalari.append(f"KRİTİK Eksik: {field}")
        
        # Opsiyonel alanlar (daha az puan)
        optional_fields = ["zorluk", "bloom_seviyesi", "soru_tipi"]
        for field in optional_fields:
            if field not in soru or not soru.get(field):
                soru_puan -= 5
                soru_hatalari.append(f"Eksik: {field}")
        
        # 2. Soru metni kalitesi
        soru_metni = soru.get("soru_metni", "")
        if len(soru_metni) < 10:
            soru_puan -= 30
            kritik_hata_var = True
            soru_hatalari.append("Soru metni çok kısa")
        elif len(soru_metni) < 20:
            soru_puan -= 10
            soru_hatalari.append("Soru metni kısa")
        
        # 3. Seçenek kontrolü (Daha esnek)
        secenekler = soru.get("secenekler", [])
        if secenekler:
            if len(secenekler) < 4:
                soru_puan -= 15
                soru_hatalari.append(f"Yetersiz seçenek: {len(secenekler)}")
            elif len(secenekler) > 6:
                soru_puan -= 10
                soru_hatalari.append(f"Fazla seçenek: {len(secenekler)}")
        else:
            # Seçenek yoksa açık uçlu soru varsayalım (daha az ceza)
            soru_puan -= 5
            soru_hatalari.append("Seçenek yok (açık uçlu)")
        
        # 4. Çözüm kalitesi (Daha esnek)
        cozum = soru.get("detayli_cozum", "")
        cevap_aciklamasi = soru.get("cevap_açıklaması", "")
        
        if len(cozum) < 20 and len(cevap_aciklamasi) < 10:
            soru_puan -= 15
            soru_hatalari.append("Çözüm/açıklama çok kısa")
        
        # Çözüm adımlarını kontrol et (daha esnek)
        gerekli_adimlar = ["VERİLENLER", "İSTENEN", "SONUÇ"]
        eksik_adimlar = [a for a in gerekli_adimlar if a not in cozum.upper()]
        if len(eksik_adimlar) >= 2:
            soru_puan -= 8
            soru_hatalari.append(f"Çözüm yapısı eksik")
        
        # 5. Metin referansı kontrolü (Daha esnek)
        if len(soru_metni) > 20:
            soru_kelimeler = set(soru_metni.lower().split())
            ortak = metin_kelimeler & soru_kelimeler
            if len(ortak) < 2:
                soru_puan -= 8
                soru_hatalari.append("Metin bağlantısı zayıf")
        
        # Kritik hata varsa say
        if kritik_hata_var:
            kritik_hatali_soru_sayisi += 1
        
        # Minimum puan koruması
        soru_puan = max(20, soru_puan)
        soru_puanlari.append(soru_puan)
        toplam_puan += soru_puan
        
        rapor["soru_kaliteleri"].append({
            "soru_no": soru.get("no", i+1),
            "puan": soru_puan,
            "hatalar": soru_hatalari,
            "kritik_hata": kritik_hata_var
        })
    
    # Toplam puan hesapla
    if soru_puanlari:
        ortalama_puan = sum(soru_puanlari) / len(soru_puanlari)
        
        # Kritik hata ağırlığı (eğer çok fazla kritik hata varsa puan düşür)
        kritik_oran = kritik_hatali_soru_sayisi / len(sorular) if sorular else 0
        if kritik_oran > 0.3:  # %30'dan fazlası kritik hatalıysa
            ortalama_puan *= 0.7  # %30 ceza
            rapor["oneri"].append(f"{int(kritik_oran*100)}% soruda kritik hata var")
        
        rapor["toplam_puan"] = int(ortalama_puan)
    
    # Genel sorunları topla (sadece önemli olanları)
    tum_hatalar = []
    for sq in rapor["soru_kaliteleri"]:
        for hata in sq.get("hatalar", []):
            if "KRİTİK" in hata or "Eksik" in hata:
                tum_hatalar.append(hata)
    
    # En sık görülen hatalar
    if tum_hatalar:
        hata_sayilari = {}
        for hata in tum_hatalar:
            hata_sayilari[hata] = hata_sayilari.get(hata, 0) + 1
        en_sik_hatalar = sorted(hata_sayilari.items(), key=lambda x: -x[1])[:3]
        rapor["sorunlar"] = [f"{h[0]} ({h[1]} kez)" for h in en_sik_hatalar]
    
    return rapor


def soru_filtrele_ve_zenginleştir(sorular, kalite_raporu, metin_icerigi):
    """
    Düşük kaliteli soruları filtreler ve mümkünse zenginleştirir.
    """
    filtrelenmis = []
    
    for soru in sorular:
        soru_no = soru.get("no", 0)
        soru_kalite = None
        
        for sq in kalite_raporu.get("soru_kaliteleri", []):
            if sq.get("soru_no") == soru_no:
                soru_kalite = sq
                break
        
        if soru_kalite and soru_kalite.get("puan", 0) >= 50:
            # Soruyu zenginleştir
            zengin_soru = soru_zenginleştir(soru, metin_icerigi)
            filtrelenmis.append(zengin_soru)
    
    return filtrelenmis


def soru_zenginleştir(soru, metin_icerigi):
    """
    Soruyu ek bilgilerle zenginleştirir.
    """
    # İpucu ekle
    if "ipucu" not in soru or not soru.get("ipucu"):
        soru["ipucu"] = f"Soru {soru.get('no', '')} için önce verilenleri ve istenenleri belirleyin."
    
    # Yaygın hatalar ekle
    if "yaygin_hatalar" not in soru or not soru.get("yaygin_hatalar"):
        soru["yaygin_hatalar"] = [
            "Formülü yanlış seçme",
            "Birim dönüşümlerinde hata",
            "Negatif/pozitif işaret hatası"
        ]
    
    # Kazanım ekle
    if "kazanım" not in soru or not soru.get("kazanım"):
        soru["kazanım"] = "Ders kazanımları ile ilgili temel beceriler"
    
    return soru


def generate_questions_with_provider(provider, api_key, prompt, gemini_endpoint=None, metin_icerigi=None, soru_sayisi=10):
    """
    Seçilen sağlayıcı ile soru üretir.
    """
    # --- Google (Gemini) Mantığı ---
    if "Google" in provider:
        try:
            # Gemini API yapılandırması
            genai.configure(api_key=api_key)
            # Gemini 2.0 Flash (Kullanıcının isteği üzerine geri alındı)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Retry mekanizması (429 hataları için - Güçlendirilmiş)
            import time
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Response'ı JSON formatında iste
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.5,
                            "top_p": 0.9,
                            "max_output_tokens": 16000,
                            "response_mime_type": "application/json",
                        }
                    )
                    break # Başarılı olursa döngüden çık
                except Exception as e:
                    # 429 (Resource Exhausted) veya 503 (Service Unavailable) hataları
                    error_str = str(e)
                    if ("429" in error_str or "503" in error_str) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10 # 10, 20, 30, 40 saniye bekle
                        print(f"⚠️ API Kotası dolu, {wait_time} saniye bekleniyor... (Deneme {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e # Son denemede de hata varsa veya başka bir hataysa fırlat
            
            # Response text'ini al
            response_text = response.text.strip()
            
            # Eğer markdown code block içinde JSON varsa çıkar
            if response_text.startswith("```"):
                # ```json ... ``` veya ``` ... ``` formatını temizle
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:].strip()
                response_text = response_text.strip()
            
            # JSON'un geçerli olduğunu doğrula ve gerekirse onar
            try:
                json.loads(response_text)
                return response_text
            except json.JSONDecodeError:
                # JSON onarma denemesi
                try:
                    # Son geçerli kapatma noktasını bul
                    last_brace = response_text.rfind("}")
                    last_bracket = response_text.rfind("]")
                    
                    if last_brace > last_bracket:
                        fixed = response_text[:last_brace+1]
                        if '"sorular":' in fixed:
                            fixed += "]}"
                    else:
                        fixed = response_text[:last_bracket+1] + "}"
                    
                    # Onarılmış JSON'u dene
                    json.loads(fixed)
                    print("✅ Gemini JSON onarıldı!")
                    return fixed
                except:
                    return json.dumps({
                        "error": "AI geçerli JSON döndürmedi", 
                        "detay": "JSON onarımı başarısız",
                        "ham_yanit_ozet": response_text[:300]
                    }, ensure_ascii=False)
            
        except Exception as e:
            error_message = f"Gemini API Hatası: {str(e)}"
            return json.dumps({"error": error_message})
    
    # --- OpenAI Mantığı ---
    elif "OpenAI" in provider:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sen Türkiye'de MEB müfredatına hakim, deneyimli bir ölçme ve değerlendirme uzmanısın. Verilen içerikten kaliteli sorular üret. JSON formatında cevap vermelisin."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=16000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSON doğrulama
            try:
                json.loads(response_text)
                return response_text
            except json.JSONDecodeError:
                return json.dumps({"error": f"OpenAI geçerli JSON döndürmedi. Ham yanıt: {response_text[:500]}"})
            
        except Exception as e:
            error_message = f"OpenAI API Hatası: {str(e)}"
            return json.dumps({"error": error_message})
    
    # --- DeepSeek Mantığı ---
    elif "DeepSeek" in provider:
        try:
            from openai import OpenAI
            
            # DeepSeek, OpenAI uyumlu API kullanır
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            
            response = client.chat.completions.create(
                # Mevcut modeller:
                # "deepseek-chat" -> V3 (hızlı, dengeli) - ÖNERİLEN
                # "deepseek-reasoner" -> R1 (reasoning odaklı, daha yavaş ama daha akıllı)
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Sen bir eğitim asistanısın. Verilen içerikten soru ve cevap oluşturuyorsun."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSON doğrulama ve Onarma - GELİŞTİRİLMİŞ
            try:
                json.loads(response_text)
                return response_text
            except json.JSONDecodeError as json_err:
                print(f"⚠️ JSON hatası, onarma deneniyor...")
                
                # Gelişmiş JSON onarma stratejisi
                fixed_text = response_text
                
                # 1. Markdown temizleme
                if fixed_text.startswith("```"):
                    parts = fixed_text.split("```")
                    if len(parts) >= 2:
                        fixed_text = parts[1]
                        if fixed_text.startswith("json"):
                            fixed_text = fixed_text[4:].strip()
                
                # 2. Yarım kalmış JSON düzeltme
                try:
                    # Son kapatılmış süslü parantezi bul
                    last_brace = fixed_text.rfind("}")
                    last_bracket = fixed_text.rfind("]")
                    
                    if last_brace > last_bracket:
                        # Süslü parantez kapanmış ama liste kapanmamış olabilir
                        fixed_text = fixed_text[:last_brace+1]
                        if "\"sorular\":" in fixed_text or '"sorular":' in fixed_text:
                            fixed_text += "]}"
                    elif last_bracket > last_brace:
                        # Liste kapanmış ama obje kapanmamış
                        fixed_text = fixed_text[:last_bracket+1] + "}"
                    
                    # Tekrar dene
                    json.loads(fixed_text)
                    print("✅ JSON başarıyla onarıldı!")
                    return fixed_text
                    
                except:
                    pass
                
                # 3. Sorular listesini tamamla
                try:
                    if '"sorular":[' in fixed_text or '"sorular": [' in fixed_text:
                        # Son tam soruyu bul ("}" veya "}") ile biten)
                        last_complete = max(
                            fixed_text.rfind("}\n}"),
                            fixed_text.rfind('}\n  }'),
                            fixed_text.rfind('},\n}"'),
                            fixed_text.rfind("},\n  }")
                        )
                        
                        if last_complete > 0:
                            fixed_text = fixed_text[:last_complete+1]
                            # Kalan yapıyı tamamla
                            fixed_text += "\n  ]\n}"
                            
                            # Test et
                            json.loads(fixed_text)
                            soru_sayisi = fixed_text.count('no":') + fixed_text.count('no": ')
                            print(f"✅ JSON soru listesi onarıldı! (Sorular: {soru_sayisi})")
                            return fixed_text
                except:
                    pass
                
                # 4. Son çare: Yarım yamalak JSON'u kabul et
                try:
                    # En az bir soru var mı kontrol et
                    if '"no":' in response_text and '"soru_metni":' in response_text:
                        print("⚠️ JSON onarılamadı ama sorular var. Ham veri gönderiliyor...")
                        return json.dumps({
                            "hata": "JSON format hatası",
                            "onarım_denemesi": "Başarısız",
                            "ham_veri_ozet": response_text[:1000]
                        }, ensure_ascii=False)
                except:
                    pass
                
                return json.dumps({
                    "error": f"DeepSeek JSON hatası: {str(json_err)}. Lütfen soru sayısını azaltın veya tekrar deneyin.",
                    "ham_yanit_ozet": response_text[:500]
                }, ensure_ascii=False)
                
        except Exception as e:
            error_message = f"DeepSeek API Hatası: {str(e)}"
            return json.dumps({"error": error_message})
    
    # --- Anthropic Mantığı ---
    elif "Anthropic" in provider:
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=api_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=16000,
                temperature=0.5,
                system="Sen Türkiye'de MEB müfredatına hakim, deneyimli bir ölçme ve değerlendirme uzmanısın. Verilen içerikten kaliteli sorular üret. JSON formatında cevap vermelisin.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text.strip()
            
            # Markdown JSON formatını temizle
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
                response_text = response_text.strip()
            
            # JSON doğrulama
            try:
                json.loads(response_text)
                return response_text
            except json.JSONDecodeError:
                return json.dumps({"error": f"Claude geçerli JSON döndürmedi. Ham yanıt: {response_text[:500]}"})
            
        except Exception as e:
            error_message = f"Anthropic API Hatası: {str(e)}"
            return json.dumps({"error": error_message})
    
    # --- MiniMax (M2.1) Mantığı ---
    elif "MiniMax" in provider:
        try:
            import requests
            import os
            
            # MiniMax API doğrudan kullanım (requests ile daha iyi encoding kontrolü)
            url = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Türkçe karakterleri ASCII'ye çevir
            def turkce_to_ascii(text):
                replacements = {
                    'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                    'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'
                }
                for tr, asc in replacements.items():
                    text = text.replace(tr, asc)
                return text
            
            # MiniMax icin kisitli token strategisi - AZ SORU, KISA METIN
            kisa_soru_sayisi = min(soru_sayisi, 5)  # MAX 5 SORU
            minimax_metin = turkce_to_ascii(metin_icerigi[:4000])  # COK KISA METIN
            
            # MiniMax icin ultra-basit prompt - ACIK UCLU SORU FORMATI
            minimax_prompt = f"""Sen Turkiye'de MEB mufredatina hakim bir olcme uzmanisin.

METIN:
{minimax_metin}

GOREV: Metinden {kisa_soru_sayisi} adet ACIK UCLU sinav sorusu uret.

KURALLAR:
1. Turkce karaktersiz yaz: i yerine i (noktasiz), s yerine s (noktasiz)
2. Sorular acik uclu olmali (ogrenci kendi cevabini yazacak)
3. Her soru icin: soru_metni + beklenen_cozum + puanlama_kriterleri
4. Cozum detayli olsun (ogretmen icin)

CIKTI FORMATI (JSON):
{{"sorular":[{{"no":1,"soru_metni":"Acik uclu soru metni...","beklenen_cozum":"Detayli cozum aciklamasi...","puanlama_kriterleri":"Tam puan icin gerekenler...","zorluk":"Orta","bloom_seviyesi":"Anlama","soru_tipi":"Acik Uclu"}},...]}}

KESINLIKLE tek bir JSON objesi dondur, birden fazla olmasin!"""
            
            payload = {
                "model": "MiniMax-M2.1",
                "messages": [
                    {"role": "system", "content": "Sen bir egitim uzmanisin. Sadece tek, tam ve gecerli JSON objesi dondurursun."},
                    {"role": "user", "content": minimax_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 6000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data["choices"][0]["message"]["content"].strip()
            
            print(f"📝 MiniMax yanit (ilk 300 karakter): {response_text[:300]}")
            
            # JSON parse et
            try:
                parsed = json.loads(response_text)
                if "sorular" in parsed:
                    print(f"✅ MiniMax JSON doğrulandı! ({len(parsed.get('sorular', []))} soru)")
                    return response_text
                else:
                    return json.dumps({"error": "MiniMax JSON formati yanlis (sorular eksik)"})
            except json.JSONDecodeError as json_err:
                error_msg = str(json_err)
                print(f"⚠️ MiniMax JSON hatasi: {error_msg[:100]}...")
                
                fixed_text = response_text
                
                # Markdown temizle
                if "```" in fixed_text:
                    parts = fixed_text.split("```")
                    for part in parts:
                        if "sorular" in part and "{" in part:
                            fixed_text = part.replace("json", "").strip()
                            break
                
                # BIRDEN FAZLA JSON OBJESI KONTROLU
                # Eger "Extra data" hatasi varsa, birden fazla JSON objesi vardir
                if "Extra data" in error_msg:
                    print("⚠️ Birden fazla JSON objesi tespit edildi, ilk obje aliniyor...")
                    # İlk JSON objesinin sonunu bul
                    first_obj_end = fixed_text.find("\n}\n{")
                    if first_obj_end > 0:
                        fixed_text = fixed_text[:first_obj_end+2]
                
                # SON KAPATMA ISARETLERINI EKLE
                try:
                    # Son gecerli kapanma noktasini bul
                    # Bir soru objesinin sonu: } + virgul/parantez
                    patterns = [
                        '"detayli_cozum":', '"detayli_cozum" :',
                        '"dogru_cevap":', '"dogru_cevap" :',
                        '"sonuc":', '"sonuc" :'
                    ]
                    
                    last_valid_pos = -1
                    for pattern in patterns:
                        pos = fixed_text.rfind(pattern)
                        if pos > last_valid_pos:
                            # Bu pattern'den sonraki ilk }" veya }'i bul
                            after_pattern = fixed_text[pos:pos+500]
                            end_quote = after_pattern.find('"\n')
                            end_brace = after_pattern.find('}\n')
                            if end_quote > 0 and end_brace > 0:
                                last_valid_pos = pos + min(end_quote + 2, end_brace + 2)
                            elif end_brace > 0:
                                last_valid_pos = pos + end_brace + 2
                    
                    if last_valid_pos > 0:
                        fixed = fixed_text[:last_valid_pos]
                        # Yapıyı tamamla
                        if not fixed.rstrip().endswith('}'):
                            fixed += '}'
                        if not fixed.rstrip().endswith(']'):
                            fixed += '\n  ]'
                        if not fixed.rstrip().endswith('}'):
                            fixed += '\n}'
                    else:
                        # Basit yöntem - son }]
                        fixed = fixed_text[:fixed_text.rfind("}")+1]
                        if not fixed.endswith("]}"):
                            fixed += "]}"
                    
                    # Test et
                    test_parsed = json.loads(fixed)
                    soru_sayisi_bulunan = len(test_parsed.get("sorular", []))
                    
                    if soru_sayisi_bulunan > 0:
                        print(f"✅ MiniMax JSON onarildi! ({soru_sayisi_bulunan} soru)")
                        return fixed
                    else:
                        raise Exception("Soru listesi bos")
                    
                except Exception as fix_err:
                    print(f"❌ MiniMax onarma basarisiz: {fix_err}")
                    no_count = response_text.count('no":')
                    return json.dumps({
                        "error": f"MiniMax JSON yapisi bozuk. Lutfen 3-4 soru deneyin.",
                        "bulunan_soru_sayisi": no_count,
                        "detay": f"Hata: {str(fix_err)[:100]}"
                    }, ensure_ascii=False)
            
        except Exception as e:
            error_message = f"MiniMax API Hatası: {str(e)}"
            return json.dumps({"error": error_message})
    
    # Desteklenmeyen sağlayıcı
    else:
        return json.dumps({"error": f"Desteklenmeyen AI sağlayıcısı: {provider}"})

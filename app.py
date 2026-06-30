import streamlit as st
import os
import io
import base64
from dotenv import load_dotenv

# Hata giderme adımları sonrası artık bu importlar çalışmalıdır:
from utils.pdf_parser import extract_text_from_pdf, get_module_chunks
from utils.ai_generator import soru_uret
from utils.docx_builder import build_docx_exam
from utils.infographic_builder import build_exam_infographic, build_exam_pdf
from utils.rag import RAGSystem

# .env dosyasındaki değişkenleri yükle
load_dotenv() 

# ----------------------------------------------------
# 1. SAYFA YAPILANDIRMASI
# ----------------------------------------------------

st.set_page_config(
    page_title=os.getenv("SINAV", "AI Sınav Hazırlayıcı"), # SINAV env değişkenini kullanır
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📝 AI Destekli Sınav Hazırlama Botu")
st.markdown("Ders notlarınızı yükleyin, modülleri seçin ve anında kurumsal sınav kağıdınızı alın.")

# ----------------------------------------------------
# 2. KENAR ÇUBUĞU (CONFIG/AYARLAR)
# ----------------------------------------------------

with st.sidebar:
    st.header("⚙️ Yapılandırma ve Anahtarlar")
    
    # AI Model Seçimi
    ai_provider = st.selectbox(
        "Yapay Zeka Modelini Seçiniz:",
        ("OpenAI (GPT-4o)", "Anthropic (Claude 3.5 Sonnet)", "Google (Gemini 2.0 Flash)", "DeepSeek (V3)", "MiniMax (M2.1)")
    )

    # API Key Girişi
    provider_name = ai_provider.split(' ')[0].upper()
    default_key = os.getenv(f"{provider_name}_API_KEY")
    
    api_key = st.text_input(
        f"{provider_name} API Key",
        value=default_key or "",
        type="password",
        help="Seçtiğiniz sağlayıcıdan aldığınız API anahtarını buraya yapıştırın."
    )
    
    # Koşullu Endpoint Girişi (Sadece Google seçildiğinde)
    gemini_endpoint = None
    if "Google" in ai_provider:
        gemini_endpoint = st.text_input(
            "Gemini Özel Endpoint (Opsiyonel)",
            value="",
            help="Vertex AI gibi özel bir uç nokta kullanıyorsanız giriniz."
        )
    
    # RAG Sistemi Açma/Kapama
    st.divider()
    st.subheader("🧠 RAG Sistemi")
    use_rag = st.toggle(
        "RAG'i Aktif Et",
        value=False,
        help="Büyük PDF'ler için önerilir. Semantik arama ile en ilgili içeriği bulur."
    )
    
    
    if use_rag:
        st.info("✅ RAG aktif - Sistem en ilgili içeriği akıllıca seçecek")
        if "Google" in ai_provider or "Gemini" in ai_provider:
            st.warning("⚠️ Gemini embedding kotası doluysa otomatik olarak basit embedding kullanılır")
        elif "DeepSeek" in ai_provider or "Anthropic" in ai_provider:
            st.info("ℹ️ Default embedding kullanılıyor (hızlı ve ücretsiz)")
    else:
        st.warning("⚠️ RAG kapalı - Tüm metin AI'ya gönderilecek")




# ----------------------------------------------------
# 3. METADATA GİRİŞİ (Sınav Formatı)
# ----------------------------------------------------

st.header("📋 Sınav Bilgileri")
col1, col2, col3, col4 = st.columns(4)

with col1:
    okul_adi = st.text_input("Okul Adı", value="", placeholder="Örn: Atatürk Anadolu Lisesi")
with col2:
    ders_adi = st.text_input("Ders Adı", value="", placeholder="Ders adını girin")
with col3:
    ogretmen_adi = st.text_input("Öğretmen Adı", value="", placeholder="Ad Soyad")
with col4:
    sinav_no = st.selectbox("Sınav No", ["1. Sınav", "2. Sınav", "3. Sınav"])

# Okul amblemi / logo (opsiyonel — PNG / JPG / SVG)
school_logo = st.file_uploader(
    "🏫 Okul Amblemi / Logo (opsiyonel — PNG / JPG / SVG)",
    type=["png", "jpg", "jpeg", "svg"],
    key="school_logo",
    help="Sınav kağıdının sol üstünde görünecek. Boş bırakırsan varsayılan 🏫 ikonu kullanılır."
)

# ----------------------------------------------------
# 4. PDF YÜKLEME VE MODÜL SEÇİMİ
# ----------------------------------------------------

st.header("📖 Ders Notları ve Kapsam")
uploaded_file = st.file_uploader("Ders Notlarını Yükle (PDF)", type=["pdf"])

# İş akışını başlatma koşulları
is_ready = uploaded_file and api_key

if is_ready:
    
    # Dosya okuma işlemi
    pdf_bytes = uploaded_file.read()
    
    # Dosya içeriğine göre benzersiz bir anahtar oluştur (cache için)
    import hashlib
    file_hash = hashlib.md5(pdf_bytes).hexdigest()
    
    # Her yeni dosya için temiz bir başlangıç
    file_io = io.BytesIO(pdf_bytes)
    
    # 1. Tüm metni çıkar
    with st.spinner("PDF içeriği okunuyor..."):
        full_text = extract_text_from_pdf(file_io)
    
    if full_text:
        st.success(f"PDF okundu. Toplam **{len(full_text.split())}** kelime tespit edildi.")
        st.info(f"📄 Dosya ID: `{file_hash[:8]}...` (Her PDF için benzersiz)")
        
        # 2. Metni modüllere (parçalara) ayır
        module_dict = get_module_chunks(full_text)
        
        # 3. Kullanıcıya modülleri seçtir
        st.subheader("Kapsam Modülleri")
        
        selected_module_names = st.multiselect(
            "Soruların çıkmasını istediğiniz modülleri seçiniz:",
            options=list(module_dict.keys()),
            default=list(module_dict.keys())
        )
        
        # Soru sayısı ayarı - session_state kullanarak
        col1, col2 = st.columns(2)
        with col1:
            # MiniMax için özel limit
            is_minimax = "MiniMax" in ai_provider
            max_soru = 5 if is_minimax else 10
            default_soru = 5 if is_minimax else 8
            
            if is_minimax:
                st.warning("⚠️ MiniMax için max 5 soru önerilir (token limiti)")
            
            question_count = st.slider(
                "📝 Soru Sayısı",
                min_value=3,
                max_value=max_soru,
                value=min(st.session_state.get('question_count', default_soru), max_soru),
                key='question_count_slider',
                help=f"Üretilecek soru sayısını seçin.{' MiniMax için max 5 önerilir.' if is_minimax else ''}"
            )
            # Değeri session'a kaydet
            st.session_state['question_count'] = question_count
            st.info(f"✅ **{question_count} soru** üretilecek")
        
        # Seçilen modüller hakkında anlık bilgi göster
        if selected_module_names:
            selected_context = "\n\n".join([module_dict[name] for name in selected_module_names])
            word_count = len(selected_context.split())
            
            # Bilgi paneli
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📚 **Seçilen Modül Sayısı:** {len(selected_module_names)}/{len(module_dict)}")
            with col2:
                st.info(f"📝 **Toplam Kelime Sayısı:** {word_count:,}")

        # ----------------------------------------------------
        # 5. SINAV OLUŞTURMA BUTONU
        # ----------------------------------------------------
        
        if selected_module_names:
            
            selected_context = "\n\n".join([module_dict[name] for name in selected_module_names])
            
            # Soru sayısını session'dan al
            question_count = st.session_state.get('question_count', 10)
            
            # Buton metnini dinamik yap
            button_text = f"🚀 {question_count} Soru Oluştur ve Word Dosyası Hazırla"
            
            if st.button(button_text, type="primary", key=f"btn_{question_count}"):
                
                with st.spinner("Yapay Zeka soruları analiz ediyor ve hazırlıyor..."):
                    
                    # RAG kullanılacaksa, önce içeriği vektörleştir
                    if use_rag:
                        with st.spinner("🧠 RAG sistemi içeriği analiz ediyor..."):
                            # Sağlayıcıya göre provider belirle
                            if "Google" in ai_provider or "Gemini" in ai_provider:
                                rag_provider = "gemini"
                            elif "OpenAI" in ai_provider:
                                rag_provider = "openai"
                            else:
                                rag_provider = "default"
                            
                            try:
                                # RAG sistemini başlat
                                rag = RAGSystem(
                                    collection_name=f"exam_{file_hash}",
                                    api_key=api_key if rag_provider != "default" else None,
                                    provider=rag_provider
                                )
                                
                                # Seçilen modülleri vektör veritabanına ekle
                                for module_name, module_content in module_dict.items():
                                    if module_name in selected_module_names:
                                        rag.add_document(
                                            text=module_content,
                                            document_id=module_name,
                                            metadata={"module": module_name}
                                        )
                            
                            except Exception as rag_err:
                                # Kota hatası kontrolü (ResourceExhausted / 429)
                                err_str = str(rag_err)
                                if "ResourceExhausted" in err_str or "429" in err_str or "quota" in err_str.lower():
                                    st.warning(f"⚠️ API Kotası aşıldı. Yerel embedding modeline (ücretsiz) geçiliyor...")
                                    
                                    # Fallback: Default provider ile yeniden dene
                                    rag = RAGSystem(
                                        collection_name=f"exam_{file_hash}",
                                        provider="default"
                                    )
                                    
                                    for module_name, module_content in module_dict.items():
                                        if module_name in selected_module_names:
                                            rag.add_document(
                                                text=module_content,
                                                document_id=module_name,
                                                metadata={"module": module_name}
                                            )
                                else:
                                    # Başka bir hata ise fırlat
                                    raise rag_err
                            
                            # Akıllı sorgu oluştur
                            intelligent_query = rag.create_intelligent_query(
                                ders_adi=ders_adi,
                                selected_modules=selected_module_names,
                                question_types=["kavramsal", "işlemsel", "analiz"]
                            )
                            
                            # En ilgili içeriği getir (EŞİK DEĞERİ DÜŞÜRÜLDÜ)
                            relevant_chunks = rag.retrieve(
                                query=intelligent_query, 
                                n_results=20,
                                min_relevance_threshold=0.45
                            )
                            
                            # Kontekst uzunluğunu optimize et
                            selected_context = rag.optimize_context_length(
                                contexts=relevant_chunks,
                                max_tokens=12000  # Soru üretimi için daha fazla token
                            )
                            
                             # RAG sonuçlarını göster
                            if relevant_chunks:
                                st.success(f"✅ RAG ile {len(relevant_chunks)} ilgili bölüm bulundu (Kalite kontrolü yapıldı)")
                                with st.expander("🔍 Bulunan İçerikleri Göster"):
                                    for i, chunk in enumerate(relevant_chunks[:5]):
                                        st.markdown(f"**Bölüm {i+1}:**")
                                        st.text(chunk[:300] + "..." if len(chunk) > 300 else chunk)
                                
                                # Optimize edilmiş kontekst kullan
                                selected_context = rag.optimize_context_for_questions(
                                    relevant_chunks,
                                    soru_tipleri=["kavramsal", "işlemsel", "analiz"],
                                    max_tokens=15000
                                )
                            else:
                                st.warning("⚠️ Yeterli ilgili içerik bulunamadı, orijinal metin kullanılıyor")
                    
                    # 1. AI'dan soruları JSON olarak al
                    questions_json = soru_uret(
                        provider=ai_provider, 
                        api_key=api_key, 
                        metin_icerigi=selected_context, 
                        soru_sayisi=question_count,
                        gemini_endpoint=gemini_endpoint,
                        ders_adi=ders_adi
                    )
                    
                    # AI'dan dönen veriyi kontrol et
                    try:
                        import json
                        parsed_data = json.loads(questions_json)
                        if "error" in parsed_data:
                            st.error(f"❌ AI Hatası: {parsed_data['error']}")
                        else:
                            st.success("✅ Sorular başarıyla oluşturuldu! Word dosyası hazırlanıyor...")
                            
                            # 1.5. Görsel Oluşturma (Varsa)
                            from utils.visualizer import create_visual_for_question
                            from utils.visual_detector import detect_visual_data

                            # Soruları işle ve gerekirse görsel ekle
                            processed_questions = []
                            if isinstance(parsed_data, dict) and 'sorular' in parsed_data:
                                q_list = parsed_data['sorular']
                            elif isinstance(parsed_data, list):
                                q_list = parsed_data
                            else:
                                q_list = []

                            auto_visual_count = 0
                            for q in q_list:
                                # AI visual_data üretti mi?
                                if 'visual_data' in q and q['visual_data']:
                                    pass  # AI'ın ürettiğini kullan
                                else:
                                    # AI üretmedi — soru metninden otomatik tespit et
                                    auto_vd = detect_visual_data(q.get('soru_metni', ''))
                                    if auto_vd:
                                        q['visual_data'] = auto_vd
                                        auto_visual_count += 1

                                # Görsel verisi varsa matplotlib fallback (eski akış — geriye dönük)
                                if 'visual_data' in q and q['visual_data']:
                                    with st.spinner(f"{q.get('no', '')}. soru için şekil çiziliyor..."):
                                        img_stream = create_visual_for_question(q['visual_data'])
                                        if img_stream:
                                            q['image_stream'] = img_stream
                                processed_questions.append(q)

                            if auto_visual_count:
                                st.info(f"🎨 {auto_visual_count} soruya otomatik infografik şekil eklendi (soru metninden tespit).")
                            
                            # Güncellenmiş listeyi kullan (resim stream'leri eklenmiş halde)
                            # JSON string yerine doğrudan listeyi gönderiyoruz, docx_builder bunu desteklemeli
                            # Ancak docx_builder şu an string bekliyor olabilir, onu da güncelledik mi?
                            # docx_builder.py içindeki parse fonksiyonu listeyi de kabul ediyor.
                            # O yüzden direkt listeyi JSON string'e çevirip gönderelim ya da fonksiyonu güncelleyelim.
                            # En temizi: questions_json argümanı yerine questions_list gönderelim ama
                            # mevcut fonksiyon imzasını bozmamak için JSON string'e geri çevirelim,
                            # FAKAT image_stream (bytesIO) JSON'a serileştirilemez!
                            # Bu yüzden build_docx_exam fonksiyonunu güncellememiz lazım.
                            # Şimdilik build_docx_exam'e "questions_data" diye yeni bir parametre ekleyelim veya
                            # mevcut parametreyi esnek yapalım.
                            
                            # Hızlı çözüm: build_docx_exam fonksiyonunu "questions_json" yerine "questions_data" alacak şekilde
                            # çağırmak daha doğru ama imza değişikliği riskli.
                            # docx_builder.py'de parse_questions_from_ai_response fonksiyonu zaten listeyi kabul ediyor.
                            # O yüzden questions_json parametresine direkt listeyi (processed_questions) verebiliriz.
                            
                            # 2. JSON verisini DOCX'e dönüştür
                            try:
                                # build_docx_exam fonksiyonunu kullanarak Word dosyasını bellekte oluşturuyoruz
                                docx_bytes = build_docx_exam(
                                    metadata={
                                        "okul": okul_adi,
                                        "ders": ders_adi,
                                        "ogretmen": ogretmen_adi,
                                        "sinav_no": sinav_no
                                    },
                                    questions_json=processed_questions
                                )

                                # 3. İndirme düğmesi
                                file_name = f"{ders_adi.replace(' ', '_')}_{sinav_no.replace('.', '')}_Sinavi.docx"
                                st.download_button(
                                    label="✅ Sınav Kağıdını İndir (.docx)",
                                    data=docx_bytes.getvalue(),
                                    file_name=file_name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )

                            except Exception as docx_err:
                                st.error(f"❌ Word dosyası oluşturulurken kritik bir hata oluştu: {docx_err}")
                                st.subheader("🔍 Yapay Zekadan Gelen Ham Veri (Hata Ayıklama İçin):")

                                # Ham veriyi güvenli bir şekilde göstermek için
                                st.code(questions_json, language="json")

                            # 4. PNG İnfografi (NotebookLM tarzı) — DOCX'den bağımsız
                            try:
                                # Okul logosunu base64 data URI'ye çevir
                                logo_data_uri = None
                                if school_logo is not None:
                                    try:
                                        school_logo.seek(0)
                                        img_bytes = school_logo.read()
                                        img_b64 = base64.b64encode(img_bytes).decode()
                                        mime = school_logo.type or "image/png"
                                        logo_data_uri = f"data:{mime};base64,{img_b64}"
                                    except Exception as logo_err:
                                        logo_data_uri = None
                                        st.warning(f"⚠️ Logo okunamadı, varsayılan kullanılacak: {logo_err}")

                                with st.spinner("🎨 İnfografi (PNG) hazırlanıyor..."):
                                    png_bytes = build_exam_infographic(
                                        metadata={
                                            "okul": okul_adi,
                                            "ders": ders_adi,
                                            "ogretmen": ogretmen_adi,
                                            "sinav_no": sinav_no,
                                            "logo": logo_data_uri,
                                        },
                                        questions=processed_questions
                                    )
                                png_file_name = f"{ders_adi.replace(' ', '_')}_{sinav_no.replace('.', '')}_Sinavi.png"
                                st.download_button(
                                    label="🎨 İnfografi İndir (.png — A4)",
                                    data=png_bytes.getvalue(),
                                    file_name=png_file_name,
                                    mime="image/png"
                                )
                            except Exception as png_err:
                                st.warning(
                                    f"⚠️ İnfografi oluşturulamadı: {png_err}\n\n"
                                    "Çözüm: terminalde `~/SINAV/sinav/bin/playwright install chromium` çalıştırın."
                                )

                            # 5. PDF (A4, çoklu sayfa otomatik) — PNG'den bağımsız
                            try:
                                with st.spinner("📄 PDF (A4) hazırlanıyor..."):
                                    pdf_bytes = build_exam_pdf(
                                        metadata={
                                            "okul": okul_adi,
                                            "ders": ders_adi,
                                            "ogretmen": ogretmen_adi,
                                            "sinav_no": sinav_no,
                                            "logo": logo_data_uri,
                                        },
                                        questions=processed_questions
                                    )
                                pdf_file_name = f"{ders_adi.replace(' ', '_')}_{sinav_no.replace('.', '')}_Sinavi.pdf"
                                st.download_button(
                                    label="📄 Sınav Kağıdını İndir (.pdf — A4)",
                                    data=pdf_bytes.getvalue(),
                                    file_name=pdf_file_name,
                                    mime="application/pdf"
                                )
                            except Exception as pdf_err:
                                st.warning(
                                    f"⚠️ PDF oluşturulamadı: {pdf_err}\n\n"
                                    "Çözüm: terminalde `~/SINAV/sinav/bin/playwright install chromium` çalıştırın."
                                )
                                
                    except json.JSONDecodeError as json_err:
                        st.error(f"❌ AI geçerli JSON formatında veri döndürmedi: {json_err}")
                        st.subheader("🔍 Yapay Zekadan Gelen Ham Veri (Hata Ayıklama İçin):")
                        st.text_area("Ham Yanıt", questions_json, height=300)
    elif uploaded_file:
        st.error("PDF'ten metin çıkarılamadı. Dosya taranmış bir görüntü (OCR gerektirir) veya bozuk olabilir.")

elif uploaded_file and not api_key:
    st.warning("Lütfen sol kenar çubuğundan **API Anahtarınızı** giriniz.")

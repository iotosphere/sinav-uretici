import io
from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file: io.BytesIO) -> str:
    """
    Streamlit üzerinden yüklenen PDF dosyasını okur ve tüm metni tek bir dize olarak döndürür.

    Args:
        uploaded_file (io.BytesIO): Streamlit'ten gelen dosya objesi.

    Returns:
        str: PDF'in tamamının metin içeriği.
    """
    try:
        # Streamlit'ten gelen dosyayı io.BytesIO olarak alıyoruz
        pdf_reader = PdfReader(uploaded_file)
        full_text = ""

        # Tüm sayfalardaki metni döngü ile birleştirme
        for page in pdf_reader.pages:
            full_text += (
                page.extract_text() + "\n\n"
            )  # Sayfa sonlarına ayırıcı ekliyoruz

        # Çok fazla boşluğu temizleme (çıktı kalitesini artırır)
        return " ".join(full_text.split())

    except Exception as e:
        print(f"PDF okuma hatası: {e}")
        return ""


def get_module_chunks(full_text: str, chunk_size: int = 5000) -> dict:
    """
    Metni öğrenme birimlerine göre ayırır. Eğer 'Öğrenme Birimi', 'Ünite' gibi
    başlıklar bulamazsa, eşit parçalara böler.

    Args:
        full_text (str): PDF'ten çıkarılan tüm metin.
        chunk_size (int): Her parçanın yaklaşık karakter uzunluğu (başlık bulunamazsa).

    Returns:
        dict: Anahtarı öğrenme birimi adı olan ve değeri ilgili metin parçası olan bir sözlük.
    """
    import re
    
    # Öğrenme birimi başlıklarını tespit et
    # Örnek: "ÖĞRENMEBİRİMİ1", "Öğrenme Birimi 2", "ÜNİTE 1", "BÖLÜM 1" vb.
    patterns = [
        r'(?:ÖĞRENMEBİRİMİ|ÖĞRENME BİRİMİ|Öğrenme Birimi)\s*[:\-]?\s*(\d+)',
        r'(?:ÜNİTE|Ünite)\s*[:\-]?\s*(\d+)',
        r'(?:BÖLÜM|Bölüm)\s*[:\-]?\s*(\d+)',
    ]
    
    units = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
        if matches:
            # Başlık bulundu, metni bu başlıklara göre böl
            for i, match in enumerate(matches):
                start_pos = match.start()
                # Bir sonraki başlığın başlangıcını bul
                end_pos = matches[i+1].start() if i+1 < len(matches) else len(full_text)
                
                unit_number = match.group(1)
                unit_title = match.group(0)
                unit_content = full_text[start_pos:end_pos].strip()
                
                units.append({
                    'title': f"Öğrenme Birimi {unit_number}",
                    'content': unit_content
                })
            
            # Başlık bulunduysa döngüden çık
            if units:
                break
    
    # Eğer hiç başlık bulunamadıysa, eski yöntemi kullan (eşit parçalara böl)
    if not units:
        words = full_text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i : i + chunk_size]))
        
        module_dict = {
            f"Modül {i + 1} (Yaklaşık {len(chunk.split())} kelime)": chunk
            for i, chunk in enumerate(chunks)
        }
        return module_dict
    
    # Öğrenme birimlerini dict formatında döndür
    module_dict = {
        unit['title']: unit['content']
        for unit in units
    }
    
    return module_dict

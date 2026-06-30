import chromadb
from chromadb.utils import embedding_functions
import hashlib
from typing import List, Dict
import os

class RAGSystem:
    """
    Retrieval-Augmented Generation sistemi.
    PDF içeriğini vektörleştirir ve semantik arama yapar.
    """
    
    def __init__(self, collection_name: str = "exam_documents", api_key: str = None, provider: str = "openai"):
        """
        RAG sistemini başlatır.
        
        Args:
            collection_name: ChromaDB koleksiyon adı
            api_key: API key (OpenAI, Gemini vb.)
            provider: AI sağlayıcısı ("openai", "gemini", "default")
        """
        try:
            # ChromaDB client (EphemeralClient - daha stabil)
            self.client = chromadb.EphemeralClient()
            
            # Sağlayıcıya göre embedding seç
            if api_key and "gemini" in provider.lower():
                # Google Gemini embedding (kota doluysa default'a düşer)
                try:
                    self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                        api_key=api_key,
                        model_name="models/embedding-001"
                    )
                except Exception as gemini_err:
                    print(f"⚠️ Gemini embedding hatası (kota dolmuş olabilir): {gemini_err}")
                    print("ℹ️ Default embedding kullanılıyor...")
                    self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            elif api_key and "openai" in provider.lower():
                # OpenAI embedding
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name="text-embedding-3-small"
                )
            else:
                # Fallback: Default embedding (basit ama çalışır)
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Koleksiyon oluştur (Varsa hata vermemesi için önce silmeyi dene)
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass # Koleksiyon yoksa devam et
            
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"RAG başlatma hatası: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Metni anlamlı parçalara böler (overlap ile).
        
        Args:
            text: Bölünecek metin
            chunk_size: Her parçanın kelime sayısı
            overlap: Parçalar arası örtüşme (kelime)
            
        Returns:
            Metin parçaları listesi
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.split()) > 50:  # Çok küçük parçaları atla
                chunks.append(chunk)
        
        return chunks
    
    def add_document(self, text: str, document_id: str, metadata: Dict = None):
        """
        Dokümanı vektör veritabanına ekler.
        
        Args:
            text: Doküman metni
            document_id: Benzersiz doküman ID'si
            metadata: Ek bilgiler (ders adı, öğrenme birimi vb.)
        """
        # Metni parçalara böl
        chunks = self.chunk_text(text)
        
        # Her parça için ID ve metadata oluştur
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": i,
                **(metadata or {})
            }
            for i in range(len(chunks))
        ]
        
        # Vektör veritabanına ekle
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
    
    def retrieve(self, query: str, n_results: int = 5, min_relevance_threshold: float = 0.7) -> List[str]:
        """
        Sorguya en yakın metin parçalarını getirir (gelişmiş versiyon).
        
        Args:
            query: Arama sorgusu (örn: "elektrik devresi soruları")
            n_results: Getirilecek parça sayısı
            min_relevance_threshold: Minimum relevans skoru
            
        Returns:
            En ilgili metin parçaları
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2  # Daha fazla sonuç al, sonra filtrele
            )
            
            if not results['documents']:
                return []
            
            documents = results['documents'][0]
            distances = results['distances'][0] if 'distances' in results else None
            
            # Relevans skorlarına göre filtreleme
            filtered_docs = []
            if distances:
                for i, (doc, distance) in enumerate(zip(documents, distances)):
                    # Cosine distance'i similarity'e çevir (1 - distance)
                    similarity = 1 - distance
                    if similarity >= min_relevance_threshold:
                        filtered_docs.append(doc)
                        print(f"📊 Doküman {i+1}: Relevans = {similarity:.3f} (✓)")
                    else:
                        print(f"📊 Doküman {i+1}: Relevans = {similarity:.3f} (✗ düşük)")
            else:
                filtered_docs = documents[:n_results]
            
            # Eğer yeterli ilgili doküman yoksa, en iyileri al (EŞİK DÜŞÜRÜLDÜ)
            min_required = max(3, n_results // 3)  # En az 3 veya n_results/3
            if len(filtered_docs) < min_required:
                print(f"⚠️ Yeterli ilgili doküman bulunamadı, en iyi {n_results} sonuç kullanılıyor")
                return documents[:n_results]
            
            return filtered_docs[:n_results]
            
        except Exception as e:
            print(f"RAG arama hatası: {e}")
            return []
    
    def create_intelligent_query(self, ders_adi: str, selected_modules: List[str], question_types: List[str] = None) -> str:
        """
        Akıllı RAG sorgusu oluşturur - Soru üretimi için optimize edilmiş.
        
        Args:
            ders_adi: Ders adı
            selected_modules: Seçilen modüller
            question_types: İstenen soru tipleri
            
        Returns:
            Optimize edilmiş arama sorgusu
        """
        import random
        
        # Modül isimlerinden konu çıkarma
        konular = []
        for modül in selected_modules:
            # Parantez içi ve gereksiz karakterleri temizle
            temiz_modul = modül.split('(')[0].strip() if '(' in modül else modül
            konular.append(temiz_modul)
        
        # Soru tipi bazlı anahtar kelimeler
        tip_anahtarlari = {
            "kavramsal": "tanım, açıklama, kavram, ilke, prensipler, temel bilgi",
            "işlemsel": "hesaplama, formül, problem, çözüm, uygulama, işlem",
            "analiz": "karşılaştırma, ilişki, neden-sonuç, ayırt etme, parçala",
            "değerlendirme": "yargılama, kanıt, eleştiri, karar, değerlendir",
            "grafik": "grafik, tablo, şema, görsel, veri, yorumlama",
            "senaryo": "örnek, durum, uygulama, gerçek hayat, pratik"
        }
        
        # Rastgele çeşitlilik için soru tipi seç
        aktif_tipler = question_types or ["kavramsal", "işlemsel"]
        
        # Ana sorguyu oluştur
        sorgu_parcalari = []
        
        # 1. Ders ve konu bilgisi
        if konular:
            konu_str = ", ".join(konular[:3])
            sorgu_parcalari.append(f"{ders_adi} dersi {konu_str} konuları")
        
        # 2. Soru tipi spesifik anahtar kelimeler
        anahtar_kelimeler = []
        for tip in aktif_tipler[:2]:
            if tip in tip_anahtarlari:
                anahtar_kelimeler.extend(tip_anahtarlari[tip].split(', '))
        
        if anahtar_kelimeler:
            # En çok 6 anahtar kelime seç
            secili_kelimeler = anahtar_kelimeler[:6]
            sorgu_parcalari.append(" ".join([f'"{kw.strip()}"' for kw in secili_kelimeler]))
        
        # 3. Eğitimsel öğeler
        sorgu_parcalari.append("lise müfredat kazanımları, önemli noktalar, sınav sorusu olabilecek bilgiler")
        
        # 4. Çözüm için gerekli bilgiler
        sorgu_parcalari.append("tanımlar, formüller, örnekler, açıklamalar")
        
        return " | ".join(sorgu_parcalari)
    
    def optimize_context_for_questions(self, contexts: List[str], soru_tipleri: List[str] = None, max_tokens: int = 15000) -> str:
        """
        Soru üretimi için içeriği optimize eder.
        
        - Her soru tipi için ayrı bölümler işaretle
        - Önemli kavramları vurgula
        - Token sınırına uygun
        
        Args:
            contexts: Metin parçaları
            soru_tipleri: Hedef soru tipleri
            max_tokens: Maksimum token
            
        Returns:
            Optimize edilmiş içerik
        """
        # Önce parçaları kaliteye göre sırala (basit heuristik)
        onemli_parcalar = []
        
        for i, ctx in enumerate(contexts):
            onem_puani = 0
            
            # Uzunluk kontrolü (ne çok kısa ne çok uzun)
            if 200 <= len(ctx) <= 2000:
                onem_puani += 2
            
            # Soru kelimeleri içeriyor mu?
            soru_kelimeleri = ["nedir", "tanım", "örnek", "formül", "kurallar", "ilke"]
            for kelime in soru_kelimeleri:
                if kelime.lower() in ctx.lower():
                    onem_puani += 1
            
            # Sayısal içerik (işlemsel sorular için)
            if any(c.isdigit() for c in ctx):
                onem_puani += 1
            
            if onem_puani >= 2:
                onemli_parcalar.append((ctx, onem_puani, i))
        
        # Önem sırasına göre sırala
        onemli_parcalar.sort(key=lambda x: -x[1])
        
        # Token sınırına göre birleştir
        max_chars = max_tokens * 4  # 1 token ≈ 4 karakter
        birlesik = ""
        toplam_char = 0
        
        for ctx, _, _ in onemli_parcalar:
            ctx_len = len(ctx)
            if toplam_char + ctx_len <= max_chars:
                birlesik += ctx + "\n\n---\n\n"
                toplam_char += ctx_len + 10
            else:
                # Kalan alan varsa ekle
                kalan = max_chars - toplam_char
                if kalan > 300:
                    birlesik += ctx[:kalan] + "... [devamı kesildi]"
                break
        
        return birlesik.strip()
    
    def optimize_context_length(self, contexts: List[str], max_tokens: int = 8000) -> str:
        """
        Kontekst uzunluğunu optimize eder.
        
        Args:
            contexts: Metin parçaları
            max_tokens: Maksimum token sayısı
            
        Returns:
            Optimize edilmiş birleşik metin
        """
        # Yaklaşık token hesaplama (1 token ≈ 4 karakter)
        max_chars = max_tokens * 4
        
        combined_text = ""
        total_chars = 0
        
        for context in contexts:
            context_chars = len(context)
            if total_chars + context_chars <= max_chars:
                combined_text += context + "\n\n"
                total_chars += context_chars
            else:
                # Kalan alan için kırp
                remaining_chars = max_chars - total_chars
                if remaining_chars > 500:  # Minimum 500 karakter bırak
                    truncated = context[:remaining_chars-10] + "..."
                    combined_text += truncated + "\n\n"
                break
        
        return combined_text.strip()
    
    def clear(self):
        """Tüm vektörleri temizler."""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.create_collection(
                name=self.collection.name,
                embedding_function=self.embedding_function
            )
        except:
            pass

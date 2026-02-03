import matplotlib.pyplot as plt
import io

def draw_coulomb_diagram(q1_label, q2_label, distance_label):
    """
    İki yük ve aralarındaki mesafeyi gösteren detaylı bir şema çizer.
    
    Args:
        q1_label (str): Birinci yükün etiketi (örn: "q1=+2C")
        q2_label (str): İkinci yükün etiketi (örn: "q2=-5C")
        distance_label (str): Mesafe etiketi (örn: "d=2m")
        
    Returns:
        io.BytesIO: Çizilen resmin bellekteki bayt verisi.
    """
    fig, ax = plt.subplots(figsize=(8, 3))
    
    # Eksenleri ve çerçeveyi kapat
    ax.axis('off')
    ax.set_xlim(-2, 12)
    ax.set_ylim(-1, 3)
    
    # Yüklerin konumları
    x1, y1 = 0, 1.5
    x2, y2 = 10, 1.5
    
    # Yük işaretlerini belirle (+ veya -)
    q1_sign = '+' if '+' in q1_label else '-'
    q2_sign = '+' if '+' in q2_label else '-'
    
    # Yükleri çiz (Daireler)
    # q1 (Sol)
    q1_color = '#3498db' if q1_sign == '+' else '#e74c3c'
    circle1 = plt.Circle((x1, y1), 0.7, color=q1_color, ec='black', linewidth=2, zorder=10)
    ax.add_patch(circle1)
    
    # Yük işareti (büyük)
    ax.text(x1, y1+0.1, q1_sign, ha='center', va='center', color='white', 
            fontweight='bold', fontsize=24)
    # Yük değeri (altta)
    ax.text(x1, y1-1.2, q1_label, ha='center', va='center', 
            fontsize=11, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # q2 (Sağ)
    q2_color = '#3498db' if q2_sign == '+' else '#e74c3c'
    circle2 = plt.Circle((x2, y2), 0.7, color=q2_color, ec='black', linewidth=2, zorder=10)
    ax.add_patch(circle2)
    
    # Yük işareti (büyük)
    ax.text(x2, y2+0.1, q2_sign, ha='center', va='center', color='white', 
            fontweight='bold', fontsize=24)
    # Yük değeri (altta)
    ax.text(x2, y2-1.2, q2_label, ha='center', va='center', 
            fontsize=11, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Aradaki mesafe çizgisi (Çift yönlü ok)
    ax.annotate(
        '', xy=(x1+0.7, 0.3), xytext=(x2-0.7, 0.3),
        arrowprops=dict(arrowstyle='<->', lw=2, color='black')
    )
    
    # Mesafe yazısı (ortada, kutucuk içinde)
    ax.text((x1+x2)/2, 0.5, distance_label, ha='center', va='bottom', 
            fontsize=12, fontweight='bold', 
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9, edgecolor='black'))
    
    # Kuvvet vektörleri (itme veya çekme)
    # Aynı işaretse itme, farklıysa çekme
    if q1_sign == q2_sign:
        # İtme kuvveti (dışa doğru oklar)
        ax.annotate('', xy=(x1-1.2, y1), xytext=(x1-0.2, y1),
                   arrowprops=dict(arrowstyle='->', lw=2.5, color='red'))
        ax.annotate('', xy=(x2+1.2, y2), xytext=(x2+0.2, y2),
                   arrowprops=dict(arrowstyle='->', lw=2.5, color='red'))
        ax.text(x1-1.5, y1+0.5, 'F', fontsize=12, color='red', fontweight='bold')
        ax.text(x2+1.5, y2+0.5, 'F', fontsize=12, color='red', fontweight='bold')
    else:
        # Çekme kuvveti (içe doğru oklar)
        ax.annotate('', xy=(x1+0.2, y1), xytext=(x1+1.2, y1),
                   arrowprops=dict(arrowstyle='->', lw=2.5, color='green'))
        ax.annotate('', xy=(x2-0.2, y2), xytext=(x2-1.2, y2),
                   arrowprops=dict(arrowstyle='->', lw=2.5, color='green'))
        ax.text(x1+1.5, y1+0.5, 'F', fontsize=12, color='green', fontweight='bold')
        ax.text(x2-1.5, y2+0.5, 'F', fontsize=12, color='green', fontweight='bold')
    
    # Resmi belleğe kaydet
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=200)
    plt.close(fig)
    buf.seek(0)
    
    return buf

def create_visual_for_question(visual_data):
    """
    AI'dan gelen visual_data tipine göre uygun çizim fonksiyonunu çağırır.
    """
    if not visual_data:
        return None
        
    v_type = visual_data.get('type')
    
    if v_type == 'coulomb':
        return draw_coulomb_diagram(
            q1_label=visual_data.get('q1', 'q1'),
            q2_label=visual_data.get('q2', 'q2'),
            distance_label=visual_data.get('d', 'd')
        )
    
    # İleride başka tipler eklenebilir (devre, optik vb.)
    
    return None

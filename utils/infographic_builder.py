"""
utils/infographic_builder.py

NotebookLM tarzı renkli sınav kağıdını PNG olarak üretir.
HTML + CSS şablonu, Playwright (headless Chromium) ile render edilir.

Kullanım:
    from utils.infographic_builder import build_exam_infographic
    png_buf = build_exam_infographic(metadata, questions_list)
"""

import io
import base64
import datetime
from playwright.sync_api import sync_playwright


# ---- 10 renk paleti (soru sayısı 10'a kadar döngüsel) ----
COLORS = [
    {"main": "#1B3A57", "soft": "#E5ECF1"},   # navy
    {"main": "#E67E50", "soft": "#FCE5D6"},   # orange
    {"main": "#F2C265", "soft": "#FAEBC8"},   # yellow (koyu metin gerekir)
    {"main": "#5BA3B0", "soft": "#DAEDF0"},   # teal
    {"main": "#A04545", "soft": "#F2D9D9"},   # rose
    {"main": "#6B5B95", "soft": "#E5DFEF"},   # purple
    {"main": "#4A7C59", "soft": "#DBEAE0"},   # green
    {"main": "#8B5E3C", "soft": "#EADBC8"},   # brown
    {"main": "#5D6D7E", "soft": "#DDE4EA"},   # slate
    {"main": "#4B5F8A", "soft": "#D8DEEC"},   # indigo
]


def _generate_color_css():
    """10 soru için renkli CSS sınıfları üret."""
    lines = []
    for i, c in enumerate(COLORS, 1):
        text_dark = "color: #5b4019;" if i == 3 else "color: white;"
        right_bg = "rgba(91,64,25,0.18); color: #5b4019;" if i == 3 else "background: rgba(255,255,255,0.22);"
        top_color = "#5b4019" if i == 3 else "white"

        lines.append(
            f".q-card.c{i} .q-head {{ background: linear-gradient(135deg, {c['main']}, {c['main']}); {text_dark} }}"
        )
        lines.append(
            f".q-card.c{i} .q-head .right {{ {right_bg} }}"
        )
        lines.append(
            f".score-cell.c{i} .top {{ background: {c['main']}; color: {top_color}; }}"
        )
    return "\n".join(lines)


# ---- HTML ŞABLONU (renkler Python'dan inject edilir) ----
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Yazılı Sınav Kağıdı</title>
<style>
  :root {
    --navy:       #1B3A57;
    --navy-2:     #2D5573;
    --navy-soft:  #E5ECF1;
    --orange:     #E67E50;
    --orange-2:   #F4A47A;
    --orange-soft:#FCE5D6;
    --cream:      #F5F1E8;
    --paper:      #FBF9F4;
    --card:       #FFFFFF;
    --ink:        #1F2937;
    --ink-soft:   #6B7280;
    --border:     #D8D2C5;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1180px;
    min-height: 1700px;
    background: var(--cream);
    background-image:
      radial-gradient(circle at 8% 6%, rgba(230,126,80,0.04) 0, transparent 40%),
      radial-gradient(circle at 92% 94%, rgba(27,58,87,0.05) 0, transparent 45%);
    font-family: -apple-system, "Segoe UI", "Helvetica Neue", system-ui, sans-serif;
    color: var(--ink);
    padding: 30px;
  }

  /* ===== OKUL BAŞLIK ŞERİDİ ===== */
  .school-bar {
    display: flex; align-items: stretch; gap: 0;
    border-radius: 16px; overflow: hidden;
    box-shadow: 0 4px 0 var(--orange), 0 6px 18px rgba(0,0,0,0.08);
    margin-bottom: 20px;
  }
  .school-logo {
    width: 130px; background: var(--cream);
    display: flex; align-items: center; justify-content: center;
    padding: 14px; border-right: 3px solid var(--orange);
  }
  .school-logo svg, .school-logo img { width: 78px; height: 78px; object-fit: contain; }
  .school-name {
    flex: 1; background: var(--navy); color: white;
    padding: 18px 28px; display: flex; flex-direction: column;
    justify-content: center; position: relative;
  }
  .school-name::after {
    content: ""; position: absolute; right: -1px; top: 0; bottom: 0;
    width: 6px; background: var(--orange);
  }
  .school-name h1 {
    font-size: 26px; font-weight: 800; letter-spacing: -0.3px;
    color: var(--orange-2);
  }
  .school-name h2 {
    font-size: 12px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; margin-top: 6px;
    color: rgba(255,255,255,0.85);
  }
  .school-year {
    width: 200px; background: var(--navy-2); color: white;
    padding: 18px 16px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; text-align: center;
  }
  .school-year .label {
    font-size: 9px; text-transform: uppercase; letter-spacing: 1.3px;
    color: var(--orange-2); margin-bottom: 4px; font-weight: 700;
  }
  .school-year .value { font-size: 13px; font-weight: 700; }
  .school-year .small { font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 2px; }

  /* ===== DERS + SINAV ŞERİDİ ===== */
  .meta-strip { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 18px; }
  .meta-card {
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 12px; padding: 12px 18px;
    display: flex; align-items: center; gap: 12px;
  }
  .meta-card .icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    background: var(--orange-soft); color: var(--orange);
  }
  .meta-card .text { display: flex; flex-direction: column; }
  .meta-card .label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 1.3px;
    color: var(--ink-soft); font-weight: 700;
  }
  .meta-card .value { font-size: 15px; font-weight: 700; color: var(--ink); }

  /* ===== KİMLİK + TOPLAM PUAN ===== */
  .identity-row { display: grid; grid-template-columns: 1fr 200px; gap: 16px; margin-bottom: 20px; }
  .identity-card {
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 14px; padding: 16px 20px;
  }
  .identity-card .head {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;
    font-weight: 800; color: var(--navy); margin-bottom: 12px;
    text-align: center; background: var(--navy-soft);
    padding: 6px; border-radius: 6px;
  }
  .identity-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 18px; }
  .identity-field {
    display: flex; align-items: center; gap: 8px;
    border-bottom: 1.5px dashed var(--border); padding: 6px 0;
  }
  .identity-field .icon {
    width: 26px; height: 26px; border-radius: 6px;
    background: var(--orange-soft); color: var(--orange);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .identity-field .label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
    font-weight: 700; color: var(--ink-soft); margin-right: 4px;
  }
  .identity-field .line { flex: 1; border-bottom: 1px dotted var(--border); min-height: 18px; }

  .total-score {
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 14px; padding: 14px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
  }
  .total-score .label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px;
    color: var(--ink-soft); font-weight: 700;
  }
  .total-circle {
    width: 110px; height: 110px; border-radius: 50%;
    background: var(--cream);
    color: var(--ink-soft); display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    border: 3px dashed var(--orange);
  }
  .total-circle .num { font-size: 24px; font-weight: 300; line-height: 1; color: var(--ink-soft); }
  .total-circle .sub { font-size: 9px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; margin-top: 4px; }
  .total-score .tag {
    font-size: 9px; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700;
  }

  /* ===== PUAN DAĞILIMI ===== */
  .score-dist {
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 22px;
  }
  .score-dist .head {
    text-align: center; font-size: 11px; text-transform: uppercase;
    letter-spacing: 1.5px; font-weight: 800; color: var(--navy);
    background: var(--navy-soft); padding: 6px; border-radius: 6px; margin-bottom: 12px;
  }
  .score-cells { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
  .score-cell { border-radius: 10px; overflow: hidden; border: 1.5px solid var(--border); }
  .score-cell .top {
    padding: 6px; text-align: center;
    font-size: 14px; font-weight: 800; color: white;
  }
  .score-cell .bot {
    padding: 8px 6px; text-align: center; background: white;
    font-size: 10px; color: var(--ink-soft); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.8px;
  }
  .score-cell .bot .puan-degeri {
    color: var(--ink); font-size: 13px; font-weight: 800;
    display: block; margin-top: 2px; letter-spacing: 0;
    border-bottom: 1.5px dotted var(--border);
    min-height: 18px;
  }

  /* ===== SORU KARTLARI ===== */
  .questions-title {
    text-align: center; margin: 8px 0 18px;
    font-size: 13px; text-transform: uppercase; letter-spacing: 2px;
    font-weight: 800; color: var(--navy); position: relative;
  }
  .questions-title::before, .questions-title::after {
    content: ""; display: inline-block;
    width: 60px; height: 2px; background: var(--orange);
    vertical-align: middle; margin: 0 16px;
  }

  .q-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
  .q-card {
    background: var(--card); border: 1.5px solid var(--border);
    border-radius: 14px; overflow: hidden;
    box-shadow: 0 1px 0 rgba(0,0,0,0.02);
    display: flex; flex-direction: column;
  }
  .q-head {
    padding: 10px 16px; color: white;
    display: flex; justify-content: space-between; align-items: center;
    font-weight: 800; letter-spacing: 0.5px;
  }
  .q-head .left { font-size: 14px; }
  .q-head .right {
    font-size: 11px; padding: 3px 9px; border-radius: 999px;
    background: rgba(255,255,255,0.22); font-weight: 700;
    min-width: 70px; text-align: center;
  }
  .q-head .right.empty { background: rgba(255,255,255,0.5); color: inherit; font-weight: 600; }
  .q-body { padding: 14px 16px; flex: 1; display: flex; flex-direction: column; }
  .q-text {
    font-size: 13.5px; line-height: 1.55; color: var(--ink);
    font-weight: 600; margin-bottom: 12px;
  }
  .q-text code {
    background: #F5F1E8; padding: 1px 6px; border-radius: 4px;
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 12.5px; color: var(--navy);
  }
  .q-figure {
    background: var(--cream); border: 1px dashed var(--border);
    border-radius: 10px; padding: 10px; margin-bottom: 12px; text-align: center;
  }
  .q-figure img, .q-figure svg { max-width: 100%; height: auto; }
  .q-figure .caption {
    font-size: 10.5px; color: var(--ink-soft);
    margin-top: 6px; font-style: italic;
  }

  .answer-area {
    border-top: 1.5px solid var(--border);
    padding-top: 10px; margin-top: auto;
  }
  .answer-area .label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 1.2px;
    color: var(--ink-soft); font-weight: 800; margin-bottom: 6px;
  }
  .answer-area .lines { display: flex; flex-direction: column; gap: 14px; padding-top: 4px; }
  .answer-area .line { border-bottom: 1px dotted var(--border); height: 18px; }

  /* ===== ALT BİLGİ ===== */
  .footer {
    margin-top: 22px; padding-top: 14px;
    border-top: 1.5px dashed var(--border);
    display: flex; justify-content: space-between; align-items: center;
    font-size: 11px; color: var(--ink-soft);
  }
  .footer .left strong { color: var(--navy); }
  .footer .right { display: flex; gap: 24px; }
  .footer .sign { display: flex; align-items: center; gap: 8px; }
  .footer .sign .line { width: 140px; border-bottom: 1px solid var(--ink-soft); }

  /* ===== A4 SAYFALAMA =====
     İlk .q-grid dışındaki her q-grid yeni A4 sayfasında başlar. */
  @page { size: A4 portrait; margin: 0; }
  .q-grid + .q-grid { page-break-before: always; }
  .q-grid { page-break-inside: auto; }

  /* ---- 10 renk için Python'dan inject ---- */
  __COLOR_CSS__
</style>
</head>
<body>

<!-- OKUL BAŞLIK -->
<div class="school-bar">
  <div class="school-logo">
    __LOGO_HTML__
  </div>
  <div class="school-name">
    <h1>__SCHOOL__</h1>
    <h2>__SCHOOL_YEAR__ EĞİTİM-ÖĞRETİM YILI · YAZILI SINAV KAĞIDI</h2>
  </div>
  <div class="school-year">
    <div class="label">Dönem</div>
    <div class="value">__SINAV_NO__</div>
    <div class="small">Yazılı Sınav</div>
  </div>
</div>

<!-- DERS + SINAV ŞERİDİ -->
<div class="meta-strip">
  <div class="meta-card">
    <div class="icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M2 3h20a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>
        <path d="M8 21V8l4-3 4 3v13"/>
      </svg>
    </div>
    <div class="text">
      <div class="label">Ders Adı</div>
      <div class="value">__DERS__</div>
    </div>
  </div>
  <div class="meta-card">
    <div class="icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <rect x="3" y="4" width="18" height="18" rx="2"/>
        <path d="M16 2v4M8 2v4M3 10h18"/>
      </svg>
    </div>
    <div class="text">
      <div class="label">Öğretmen</div>
      <div class="value">__OGRETMEN__</div>
    </div>
  </div>
</div>

<!-- KİMLİK + TOPLAM PUAN -->
<div class="identity-row">
  <div class="identity-card">
    <div class="head">ÖĞRENCİ KİMLİK BİLGİLERİ</div>
    <div class="identity-grid">
      <div class="identity-field">
        <div class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
          </svg>
        </div>
        <span class="label">AD:</span>
        <span class="line"></span>
      </div>
      <div class="identity-field">
        <div class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
          </svg>
        </div>
        <span class="label">SOYAD:</span>
        <span class="line"></span>
      </div>
      <div class="identity-field">
        <div class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
            <path d="M6 12v5c3 3 9 3 12 0v-5"/>
          </svg>
        </div>
        <span class="label">SINIF:</span>
        <span class="line"></span>
      </div>
      <div class="identity-field">
        <div class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <rect x="5" y="2" width="14" height="20" rx="2"/>
            <path d="M9 6h6M9 10h6M9 14h6M9 18h4"/>
          </svg>
        </div>
        <span class="label">OKUL NO:</span>
        <span class="line"></span>
      </div>
    </div>
  </div>
  <div class="total-score">
    <div class="label">TOPLAM PUAN</div>
    <div class="total-circle">
      <div class="num">—</div>
      <div class="sub">puan</div>
    </div>
    <div class="tag">Değerlendirme</div>
  </div>
</div>

<!-- PUAN DAĞILIMI -->
<div class="score-dist">
  <div class="head">EŞİT PUANLI __SORU_SAYISI__ SORU DÜZENİ &amp; PUAN DAĞILIMI</div>
  <div class="score-cells">
    __SCORE_CELLS__
  </div>
</div>

<div class="questions-title">SORULAR</div>

<!-- SORU KARTLARI (sayfalara bölünmüş, her grup bir A4 sayfası) -->
__Q_GRIDS__

<!-- ALT BİLGİ -->
<div class="footer">
  <div class="left"><strong>İnfografi Sınav Botu</strong> · v0.1</div>
  <div class="right">
    <div class="sign">Öğretmen İmza<span class="line"></span></div>
    <div class="sign">Tarih<span class="line"></span></div>
  </div>
</div>

</body>
</html>"""


def _html_escape(text):
    """Basit HTML escape (soru metni için)."""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


# Default okul logosu (kullanıcı logo yüklemediğinde kullanılır)
_DEFAULT_LOGO_SVG = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="46" fill="#1B3A57" stroke="#E67E50" stroke-width="3"/>
      <path d="M30 65 L50 25 L70 65 Z" fill="#F2C265"/>
      <rect x="38" y="55" width="24" height="20" fill="#F5F1E8"/>
      <rect x="44" y="62" width="12" height="13" fill="#1B3A57"/>
      <circle cx="50" cy="20" r="3" fill="#E67E50"/>
    </svg>"""


def _logo_html(logo_data_uri):
    """Logo varsa <img>, yoksa varsayılan SVG."""
    if logo_data_uri:
        # SVG ise object-fit: contain ile küçük harf düzeltmesi
        return f'<img src="{logo_data_uri}" alt="Okul Logosu" />'
    return _DEFAULT_LOGO_SVG


# ============================================================
# SORU GÖRSELLERİ (İnfografik SVG şablonları)
# ============================================================

def _generate_figure_svg(visual_data):
    """AI'ın verdiği visual_data tipine göre SVG üret."""
    if not visual_data:
        return ""
    v_type = (visual_data.get("type") or "").lower()
    if v_type == "coulomb":
        return _coulomb_svg(visual_data)
    if v_type == "ohm":
        return _ohm_svg(visual_data)
    if v_type == "seri":
        return _seri_svg(visual_data)
    if v_type == "paralel":
        return _paralel_svg(visual_data)
    if v_type == "kirchhoff":
        return _kirchhoff_svg(visual_data)
    if v_type == "elektrik_alan":
        return _elektrik_alan_svg(visual_data)
    return ""


def _coulomb_svg(vd):
    """İki noktasal yük + mesafe + Coulomb kuvveti."""
    q1 = vd.get("q1", "q₁")
    q2 = vd.get("q2", "q₂")
    d = vd.get("d", "r")
    q1_sign = "+" if "+" in q1 else ("−" if "−" in q1 or "-" in q1 else "+")
    q2_sign = "+" if "+" in q2 else ("−" if "−" in q2 or "-" in q2 else "+")
    q1_color = "#3498db" if q1_sign == "+" else "#e74c3c"
    q2_color = "#3498db" if q2_sign == "+" else "#e74c3c"
    is_attractive = q1_sign != q2_sign

    if is_attractive:
        force_color = "#4A7C59"
        force_text = "F (çekim)"
        # içe doğru oklar
        f1 = '<line x1="105" y1="50" x2="155" y2="50" stroke="#4A7C59" stroke-width="2.5"/><polygon points="155,50 145,45 145,55" fill="#4A7C59"/>'
        f2 = '<line x1="245" y1="50" x2="295" y2="50" stroke="#4A7C59" stroke-width="2.5"/><polygon points="245,50 255,45 255,55" fill="#4A7C59"/>'
    else:
        force_color = "#A04545"
        force_text = "F (itme)"
        f1 = '<line x1="65" y1="50" x2="115" y2="50" stroke="#A04545" stroke-width="2.5"/><polygon points="115,50 105,45 105,55" fill="#A04545"/>'
        f2 = '<line x1="285" y1="50" x2="335" y2="50" stroke="#A04545" stroke-width="2.5"/><polygon points="285,50 295,45 295,55" fill="#A04545"/>'

    return f'''
    <svg viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg">
      <!-- zemin -->
      <line x1="20" y1="125" x2="380" y2="125" stroke="#A04545" stroke-width="1.5" stroke-dasharray="4 3"/>
      <!-- mesafe oku -->
      <line x1="130" y1="115" x2="270" y2="115" stroke="#1B3A57" stroke-width="1.5"/>
      <polygon points="130,115 140,110 140,120" fill="#1B3A57"/>
      <polygon points="270,115 260,110 260,120" fill="#1B3A57"/>
      <text x="200" y="108" text-anchor="middle" font-size="13" font-weight="700" fill="#1B3A57">{_html_escape(d)}</text>
      <!-- q1 -->
      <circle cx="130" cy="85" r="32" fill="{q1_color}" stroke="#1B3A57" stroke-width="2"/>
      <text x="130" y="95" text-anchor="middle" font-size="36" font-weight="900" fill="white">{q1_sign}</text>
      <text x="130" y="160" text-anchor="middle" font-size="13" font-weight="700" fill="#1F2937">{_html_escape(q1)}</text>
      <!-- q2 -->
      <circle cx="270" cy="85" r="32" fill="{q2_color}" stroke="#1B3A57" stroke-width="2"/>
      <text x="270" y="95" text-anchor="middle" font-size="36" font-weight="900" fill="white">{q2_sign}</text>
      <text x="270" y="160" text-anchor="middle" font-size="13" font-weight="700" fill="#1F2937">{_html_escape(q2)}</text>
      <!-- kuvvet -->
      {f1}
      {f2}
      <text x="200" y="42" text-anchor="middle" font-size="12" font-weight="700" fill="{force_color}">{force_text}</text>
    </svg>'''


def _ohm_svg(vd):
    """Basit DC devre: pil + direnç + ampermetre + voltmetre."""
    v = vd.get("v", "V")
    r = vd.get("r", "R")
    i = vd.get("i", "I")
    return f'''
    <svg viewBox="0 0 420 200" xmlns="http://www.w3.org/2000/svg">
      <!-- ana devre çerçevesi -->
      <rect x="20" y="40" width="380" height="120" fill="none" stroke="#1F2937" stroke-width="1.5" stroke-dasharray="3 3" rx="8"/>
      <!-- kablolar -->
      <line x1="60" y1="100" x2="160" y2="100" stroke="#1F2937" stroke-width="2.5"/>
      <line x1="240" y1="100" x2="320" y2="100" stroke="#1F2937" stroke-width="2.5"/>
      <!-- pil (V kaynağı) -->
      <rect x="40" y="70" width="40" height="60" fill="#F2C265" stroke="#1B3A57" stroke-width="2" rx="3"/>
      <line x1="50" y1="80" x2="70" y2="80" stroke="#1B3A57" stroke-width="3"/>
      <line x1="55" y1="90" x2="65" y2="90" stroke="#1B3A57" stroke-width="2"/>
      <line x1="50" y1="110" x2="70" y2="110" stroke="#1B3A57" stroke-width="3"/>
      <line x1="55" y1="120" x2="65" y2="120" stroke="#1B3A57" stroke-width="2"/>
      <text x="40" y="148" text-anchor="middle" font-size="12" font-weight="700" fill="#1B3A57">{_html_escape(v)}</text>
      <!-- direnç (zigzag) -->
      <polyline points="160,100 168,88 176,112 184,88 192,112 200,88 208,112 216,88 224,100 240,100"
                fill="none" stroke="#E67E50" stroke-width="2.5"/>
      <text x="200" y="78" text-anchor="middle" font-size="12" font-weight="700" fill="#E67E50">{_html_escape(r)}</text>
      <!-- ampermetre (A) -->
      <circle cx="350" cy="100" r="22" fill="#5BA3B0" stroke="#1B3A57" stroke-width="2"/>
      <text x="350" y="106" text-anchor="middle" font-size="16" font-weight="800" fill="white">A</text>
      <text x="350" y="148" text-anchor="middle" font-size="12" font-weight="700" fill="#1B3A57">{_html_escape(i)}</text>
      <!-- akım yönü oku -->
      <polygon points="120,100 130,94 130,106" fill="#4A7C59"/>
      <text x="100" y="85" font-size="11" font-weight="700" fill="#4A7C59">I</text>
      <!-- formül -->
      <text x="210" y="180" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">V = I · R</text>
    </svg>'''


def _seri_svg(vd):
    """Art arda bağlı dirençler."""
    n = max(2, min(int(vd.get("n", 3)), 4))
    labels = vd.get("labels") or [f"R<sub>{i+1}</sub>" for i in range(n)]
    while len(labels) < n:
        labels.append(f"R<sub>{len(labels)+1}</sub>")
    v_label = vd.get("v", "V")

    cell_w = 60
    gap = 12
    total_w = n * cell_w + (n - 1) * gap + 60
    start_x = (400 - total_w) // 2 + 30
    y = 75

    parts = []
    # Sol kablo
    parts.append(f'<line x1="20" y1="{y+15}" x2="{start_x}" y2="{y+15}" stroke="#1F2937" stroke-width="2.5"/>')
    # Her direnç
    for i in range(n):
        x = start_x + i * (cell_w + gap)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell_w}" height="30" fill="white" stroke="#1B3A57" stroke-width="2" rx="4"/>'
        )
        parts.append(
            f'<text x="{x + cell_w/2}" y="{y + 20}" text-anchor="middle" font-size="13" font-weight="700" fill="#1B3A57">{labels[i]}</text>'
        )
        # ara bağlantı
        if i < n - 1:
            cx = x + cell_w
            parts.append(f'<line x1="{cx}" y1="{y+15}" x2="{cx + gap}" y2="{y+15}" stroke="#1F2937" stroke-width="2.5"/>')
    # Sağ kablo
    end_x = start_x + n * cell_w + (n - 1) * gap
    parts.append(f'<line x1="{end_x}" y1="{y+15}" x2="380" y2="{y+15}" stroke="#1F2937" stroke-width="2.5"/>')
    # V etiketi
    parts.append(f'<text x="30" y="{y+50}" font-size="13" font-weight="800" fill="#1B3A57">{_html_escape(v_label)}</text>')
    parts.append(f'<polygon points="62,{y+45} 55,{y+38} 55,{y+52}" fill="#1B3A57"/>')
    # Formül
    parts.append(f'<text x="200" y="160" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">R<tspan font-size="10" baseline-shift="sub">eş</tspan> = R₁ + R₂ + R₃ + …</text>')

    return f'<svg viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def _paralel_svg(vd):
    """Yan yana bağlı dirençler."""
    n = max(2, min(int(vd.get("n", 3)), 4))
    labels = vd.get("labels") or [f"R<sub>{i+1}</sub>" for i in range(n)]
    while len(labels) < n:
        labels.append(f"R<sub>{len(labels)+1}</sub>")
    v_label = vd.get("v", "V")

    cell_w = 50
    cell_h = 24
    gap = 16
    rail_top_y = 50
    rail_bot_y = 150
    cols_x = [120 + i * (cell_w + gap) for i in range(n)]
    total_w = n * cell_w + (n - 1) * gap
    start_x = (400 - total_w) // 2

    parts = []
    # Üst ve alt ana raylar
    parts.append(f'<line x1="20" y1="{rail_top_y}" x2="380" y2="{rail_top_y}" stroke="#1F2937" stroke-width="2.5"/>')
    parts.append(f'<line x1="20" y1="{rail_bot_y}" x2="380" y2="{rail_bot_y}" stroke="#1F2937" stroke-width="2.5"/>')
    # V kaynağı (sol)
    parts.append(f'<rect x="40" y="{rail_top_y - 25}" width="40" height="50" fill="#F2C265" stroke="#1B3A57" stroke-width="2" rx="3"/>')
    parts.append(f'<line x1="50" y1="{rail_top_y - 15}" x2="70" y2="{rail_top_y - 15}" stroke="#1B3A57" stroke-width="3"/>')
    parts.append(f'<line x1="50" y1="{rail_bot_y + 15}" x2="70" y2="{rail_bot_y + 15}" stroke="#1B3A57" stroke-width="3"/>')
    parts.append(f'<text x="60" y="100" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">{_html_escape(v_label)}</text>')
    # Her direnç kolu
    for i in range(n):
        x = start_x + i * (cell_w + gap)
        # dikey bağlantı
        parts.append(f'<line x1="{x + cell_w/2}" y1="{rail_top_y}" x2="{x + cell_w/2}" y2="{rail_bot_y}" stroke="#1F2937" stroke-width="2"/>')
        # direnç kutusu (ortada)
        cy = (rail_top_y + rail_bot_y) / 2
        parts.append(
            f'<rect x="{x}" y="{cy - cell_h/2}" width="{cell_w}" height="{cell_h}" fill="white" stroke="#1B3A57" stroke-width="2" rx="4"/>'
        )
        parts.append(
            f'<text x="{x + cell_w/2}" y="{cy + 4}" text-anchor="middle" font-size="12" font-weight="700" fill="#1B3A57">{labels[i]}</text>'
        )
    # Formül
    parts.append(f'<text x="200" y="180" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">1/R<tspan font-size="10" baseline-shift="sub">eş</tspan> = 1/R₁ + 1/R₂ + 1/R₃ + …</text>')

    return f'<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def _kirchhoff_svg(vd):
    """Düğüm noktası + giren/çıkan akımlar."""
    giren = vd.get("giren", [])  # [{"label": "I₁", "value": "3 A", "direction": "left"}, ...]
    cikan = vd.get("cikan", [])
    if not giren and not cikan:
        giren = [{"label": "I₁", "value": "3 A"}, {"label": "I₂", "value": "5 A"}]
        cikan = [{"label": "I₃", "value": "?"}]

    cx, cy = 200, 110
    parts = []
    # Düğüm noktası
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="#1B3A57" stroke="#F2C265" stroke-width="3"/>')
    parts.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-size="13" font-weight="800" fill="white">N</text>')

    # Giren akımlar (sol ve üst yarı)
    positions_in = [(80, cy, cx - 22, cy), (cx, 30, cx, cy - 22)]
    color_in = "#4A7C59"
    for i, akim in enumerate(giren[:2]):
        if i >= len(positions_in):
            break
        x1, y1, x2, y2 = positions_in[i]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color_in}" stroke-width="3"/>')
        parts.append(f'<polygon points="{x2},{y2} {x2-8 if x1<x2 else x2+8},{y2-5} {x2-8 if x1<x2 else x2+8},{y2+5}" fill="{color_in}"/>')
        # Etiket (orta noktada)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        parts.append(f'<text x="{mx}" y="{my - 8}" text-anchor="middle" font-size="13" font-weight="800" fill="{color_in}">{_html_escape(akim.get("label", "I?"))} = {_html_escape(akim.get("value", ""))}</text>')

    # Çıkan akımlar (sağ ve alt yarı)
    positions_out = [(320, cy, cx + 22, cy), (cx, 190, cx, cy + 22)]
    color_out = "#A04545"
    for i, akim in enumerate(cikan[:2]):
        if i >= len(positions_out):
            break
        x1, y1, x2, y2 = positions_out[i]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color_out}" stroke-width="3"/>')
        parts.append(f'<polygon points="{x2},{y2} {x2-8 if x1<x2 else x2+8},{y2-5} {x2-8 if x1<x2 else x2+8},{y2+5}" fill="{color_out}"/>')
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        parts.append(f'<text x="{mx}" y="{my + 18}" text-anchor="middle" font-size="13" font-weight="800" fill="{color_out}">{_html_escape(akim.get("label", "I?"))} = {_html_escape(akim.get("value", ""))}</text>')

    # Formül
    parts.append(f'<text x="200" y="220" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">ΣI<tspan font-size="10" baseline-shift="sub">giren</tspan> = ΣI<tspan font-size="10" baseline-shift="sub">çıkan</tspan></text>')

    return f'<svg viewBox="0 0 400 240" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def _elektrik_alan_svg(vd):
    """Tek yük + elektrik alan çizgileri (radyal)."""
    q = vd.get("q", "Q")
    sign = "+" if "+" in q else "−"
    color = "#3498db" if sign == "+" else "#e74c3c"
    cx, cy = 200, 110

    parts = []
    # Radyal alan çizgileri (giren veya çıkan)
    import math
    n_lines = 8
    r_inner = 35
    r_outer = 90
    for i in range(n_lines):
        angle = 2 * math.pi * i / n_lines
        x1 = cx + r_inner * math.cos(angle)
        y1 = cy + r_inner * math.sin(angle)
        x2 = cx + r_outer * math.cos(angle)
        y2 = cy + r_outer * math.sin(angle)
        # Ok yönü: pozitif yükten dışarı, negatif yükten içeri
        if sign == "+":
            sx1, sy1, sx2, sy2 = x1, y1, x2, y2
        else:
            sx1, sy1, sx2, sy2 = x2, y2, x1, y1
        parts.append(f'<line x1="{sx1}" y1="{sy1}" x2="{sx2}" y2="{sy2}" stroke="{color}" stroke-width="2"/>')
        # Ok ucu
        ang2 = math.atan2(sy2 - sy1, sx2 - sx1)
        ax = sx2 - 8 * math.cos(ang2)
        ay = sy2 - 8 * math.sin(ang2)
        p1x = ax - 6 * math.cos(ang2 - 0.4)
        p1y = ay - 6 * math.sin(ang2 - 0.4)
        p2x = ax - 6 * math.cos(ang2 + 0.4)
        p2y = ay - 6 * math.sin(ang2 + 0.4)
        parts.append(f'<polygon points="{sx2},{sy2} {p1x},{p1y} {p2x},{p2y}" fill="{color}"/>')

    # Yük
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="28" fill="{color}" stroke="#1B3A57" stroke-width="2"/>')
    parts.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="32" font-weight="900" fill="white">{sign}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 60}" text-anchor="middle" font-size="13" font-weight="700" fill="#1F2937">{_html_escape(q)}</text>')
    # Formül
    parts.append(f'<text x="200" y="220" text-anchor="middle" font-size="14" font-weight="800" fill="#1B3A57">E = k·Q / r²</text>')

    return f'<svg viewBox="0 0 400 240" xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'


def _score_cell_html(i, puan):
    cls = f"c{i+1}"
    return f'''
    <div class="score-cell {cls}">
      <div class="top">{i+1}</div>
      <div class="bot">
        Puan Değeri
        <span class="puan-degeri">&nbsp;</span>
      </div>
    </div>'''


def _q_card_html(i, q, soru_puan):
    cls = f"c{i+1}"
    soru_metni = q.get("soru_metni") or q.get("soru") or ""
    soru_metni_html = _html_escape(soru_metni)

    # Görsel: önce visual_data (SVG), yoksa image_stream (base64 PNG, geriye dönük uyumluluk)
    img_html = ""
    if q.get("visual_data"):
        svg = _generate_figure_svg(q["visual_data"])
        if svg:
            caption = q["visual_data"].get("caption") or f"Şekil {i+1}.1"
            img_html = (
                f'<div class="q-figure">'
                f'{svg}'
                f'<div class="caption">{_html_escape(caption)}</div>'
                f'</div>'
            )
    elif q.get("image_stream"):
        try:
            img_stream = q["image_stream"]
            img_stream.seek(0)
            b64 = base64.b64encode(img_stream.read()).decode()
            img_html = (
                f'<div class="q-figure">'
                f'<img src="data:image/png;base64,{b64}" alt="Şekil"/>'
                f'<div class="caption">Şekil {i+1}.1 — Soruya ait görsel</div>'
                f'</div>'
            )
        except Exception:
            img_html = ""

    return f'''
    <div class="q-card {cls}">
      <div class="q-head">
        <span class="left">SORU – {i+1}</span>
        <span class="right empty">…… Puan</span>
      </div>
      <div class="q-body">
        <div class="q-text">{soru_metni_html}</div>
        {img_html}
        <div class="answer-area">
          <div class="label">CEVAP:</div>
          <div class="lines">
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
            <div class="line"></div>
          </div>
        </div>
      </div>
    </div>'''


def build_exam_infographic(metadata, questions):
    """
    Sınav kağıdını PNG (NotebookLM tarzı infografi) olarak üretir.

    Args:
        metadata (dict): {"okul", "ders", "ogretmen", "sinav_no"}
        questions (list): [{"soru_metni": str, "image_stream"?: BytesIO, ...}]

    Returns:
        io.BytesIO: PNG dosyasının bellekteki bayt verisi.
    """
    school = metadata.get("okul") or "OKUL ADI"
    ders = metadata.get("ders") or "Ders"
    ogretmen = metadata.get("ogretmen") or "Öğretmen Adı"
    sinav_no = metadata.get("sinav_no") or "1. Sınav"

    # Eğitim-öğretim yılı (Türkiye: Eylül-Haziran, Temmuz-Ağustos bir sonraki yıla geçiş)
    import datetime
    now = datetime.datetime.now()
    school_year_start = now.year if now.month >= 9 else now.year - 1
    school_year_end = school_year_start + 1
    school_year = f"{school_year_start}–{school_year_end}"

    soru_sayisi = max(len(questions), 1)
    puan_per = 100 // soru_sayisi
    kalan = 100 - puan_per * soru_sayisi

    def soru_puan(i):
        return puan_per + (1 if i >= (soru_sayisi - kalan) else 0)

    # Puan dağılımı hücreleri
    score_cells = "".join(_score_cell_html(i, soru_puan(i)) for i in range(soru_sayisi))

    # Soru kartları — A4 sayfalama için 4'erli gruplara bölünür
    q_grids_html = _build_q_grids(questions, soru_puan)

    # HTML'i doldur
    color_css = _generate_color_css()
    html = (HTML_TEMPLATE
            .replace("__COLOR_CSS__", color_css)
            .replace("__LOGO_HTML__", _logo_html(metadata.get("logo")))
            .replace("__SCHOOL__", _html_escape(school))
            .replace("__SCHOOL_YEAR__", school_year)
            .replace("__DERS__", _html_escape(ders))
            .replace("__OGRETMEN__", _html_escape(ogretmen))
            .replace("__SINAV_NO__", _html_escape(sinav_no))
            .replace("__SORU_SAYISI__", str(soru_sayisi))
            .replace("__SCORE_CELLS__", score_cells)
            .replace("__Q_GRIDS__", q_grids_html))

    # Playwright ile PNG render
    png_bytes = _render_html_to_png(html)
    buf = io.BytesIO(png_bytes)
    buf.seek(0)
    return buf


def build_exam_pdf(metadata, questions):
    """
    Sınav kağıdını A4 formatında PDF olarak üretir.
    Çoklu sayfa otomatik: 5+ soru için her 4 soruda bir yeni sayfa.

    Args:
        metadata (dict): {"okul", "ders", "ogretmen", "sinav_no", "logo"}
        questions (list): [{"soru_metni", "visual_data"?, ...}]

    Returns:
        io.BytesIO: PDF dosyasının bellekteki bayt verisi.
    """
    school = metadata.get("okul") or "OKUL ADI"
    ders = metadata.get("ders") or "Ders"
    ogretmen = metadata.get("ogretmen") or "Öğretmen Adı"
    sinav_no = metadata.get("sinav_no") or "1. Sınav"

    _now = datetime.datetime.now()
    _sy_start = _now.year if _now.month >= 9 else _now.year - 1
    school_year = f"{_sy_start}–{_sy_start + 1}"

    soru_sayisi = max(len(questions), 1)
    puan_per = 100 // soru_sayisi
    kalan = 100 - puan_per * soru_sayisi

    def soru_puan(i):
        return puan_per + (1 if i >= (soru_sayisi - kalan) else 0)

    score_cells = "".join(_score_cell_html(i, soru_puan(i)) for i in range(soru_sayisi))
    q_grids_html = _build_q_grids(questions, soru_puan)

    color_css = _generate_color_css()
    html = (HTML_TEMPLATE
            .replace("__COLOR_CSS__", color_css)
            .replace("__LOGO_HTML__", _logo_html(metadata.get("logo")))
            .replace("__SCHOOL__", _html_escape(school))
            .replace("__SCHOOL_YEAR__", school_year)
            .replace("__DERS__", _html_escape(ders))
            .replace("__OGRETMEN__", _html_escape(ogretmen))
            .replace("__SINAV_NO__", _html_escape(sinav_no))
            .replace("__SORU_SAYISI__", str(soru_sayisi))
            .replace("__SCORE_CELLS__", score_cells)
            .replace("__Q_GRIDS__", q_grids_html))

    pdf_bytes = _render_html_to_pdf(html)
    buf = io.BytesIO(pdf_bytes)
    buf.seek(0)
    return buf


def _render_html_to_png(html, width=1240, height=1754):
    """
    Verilen HTML'i Chromium ile yükleyip A4 (1240x1754 @150 DPI) PNG döner.
    full_page=True ile içerik büyükse çoklu sayfa halinde tek PNG'de döner.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.set_content(html, wait_until="load")
            page.wait_for_load_state("networkidle", timeout=10000)
            png = page.screenshot(full_page=True, type="png")
        finally:
            browser.close()
    return png


def _render_html_to_pdf(html, width=1240, height=1754):
    """
    Verilen HTML'i A4 formatında PDF olarak döner.
    CSS @page A4 portrait + page-break ile çoklu sayfa otomatik.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.set_content(html, wait_until="load")
            page.wait_for_load_state("networkidle", timeout=10000)
            pdf = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                prefer_css_page_size=True,
            )
        finally:
            browser.close()
    return pdf


# A4 sayfa başına soru sayısı (ilk sayfa header yer kaplar)
QUESTIONS_PER_PAGE = 4


def _build_q_grids(questions, soru_puan_fn):
    """
    Soruları 4'erli gruplara bölerek çoklu <div class="q-grid"> üretir.
    CSS'teki `.q-grid + .q-grid { page-break-before: always; }` kuralı
    sayesinde her yeni grup yeni bir A4 sayfasında başlar (PDF'te).
    PNG'de ise tüm sayfalar full_page=True ile tek PNG'de alt alta dizilir.
    """
    if not questions:
        return '<div class="q-grid"></div>'

    grids = []
    n = len(questions)
    per_page = QUESTIONS_PER_PAGE
    for i in range(0, n, per_page):
        chunk = questions[i:i + per_page]
        offset = i
        cards = "".join(
            _q_card_html(offset + j, q, soru_puan_fn(offset + j))
            for j, q in enumerate(chunk)
        )
        grids.append(f'<div class="q-grid">{cards}</div>')

    return "\n".join(grids)
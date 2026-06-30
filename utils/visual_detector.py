"""
utils/visual_detector.py

Soru metninden otomatik görsel tipi tespit eder (AI'a bağımlı değil).
Eğer AI `visual_data` üretmediyse bu fallback devreye girer.

Desteklenen tipler: coulomb, ohm, seri, paralel, kirchhoff, elektrik_alan
"""
import re


def detect_visual_data(soru_metni):
    """
    Soru metninden uygun görsel tipi ve parametreleri tespit eder.

    Args:
        soru_metni (str): Soru metni (Türkçe).

    Returns:
        dict | None: visual_data dict veya tespit edilemediyse None.
    """
    if not soru_metni:
        return None

    t = soru_metni

    # 1) Coulomb Yasası — iki noktasal yük
    if re.search(r"coulomb|noktasal\s+y[üu]k", t, re.IGNORECASE):
        q1 = re.search(r"q[₁1]\s*=\s*([+\-−]?\s*\d+(?:[.,]\d+)?\s*[μuμ]?\s*C)", t)
        q2 = re.search(r"q[₂2]\s*=\s*([+\-−]?\s*\d+(?:[.,]\d+)?\s*[μuμ]?\s*C)", t)
        d = re.search(r"(?:r|mesafe|d)\s*=\s*(\d+(?:[.,]\d+)?\s*(?:cm|mm|m)?)", t)
        return {
            "type": "coulomb",
            "q1": q1.group(1).strip() if q1 else "q₁",
            "q2": q2.group(1).strip() if q2 else "q₂",
            "d": d.group(1).strip() if d else "r",
        }

    # 2) Kirchhoff — düğüm noktası / akımlar kanunu
    if re.search(
        r"kirchhoff|kirsof|k[ıi]r[sş]of|d[üu][ğg][üu]m\s+noktas|ak[ıi]mlar\s+kanunu|KCL",
        t, re.IGNORECASE
    ):
        # Giren/çıkan akımları basitçe çıkar
        giren = _extract_currents(t)
        cikan = _extract_question_mark_currents(t)
        return {"type": "kirchhoff", "giren": giren, "cikan": cikan}

    # 3) Seri bağlı dirençler (paralel'den önce — bazen ikisi bir arada olur)
    if re.search(r"seri\s+(ba[ğg]l[ıi]|diren[cç])|art\s+arda", t, re.IGNORECASE):
        n, labels = _extract_resistor_labels(t)
        return {"type": "seri", "n": n, "labels": labels, "v": "V"}

    # 4) Paralel bağlı dirençler
    if re.search(r"paralel\s+(ba[ğg]l[ıi]|diren[cç])|yan\s+yana", t, re.IGNORECASE):
        n, labels = _extract_resistor_labels(t)
        return {"type": "paralel", "n": n, "labels": labels, "v": "V"}

    # 5) Ohm Yasası — V= ve R= (ohm kelimesi varsa veya hesaplama sorusu)
    if re.search(
        r"ohm\s+(kanunu|yasas[ıi])|\bV\s*=\s*\d+|R\s*=\s*\d+\s*[oO]hm",
        t, re.IGNORECASE
    ):
        return {"type": "ohm", "v": "V", "r": "R", "i": "I"}

    # 6) Elektrik alan
    if re.search(r"elektrik\s+alan[ıi]?\s+([şs][ıi]ddet|yo[ğg]unlu[ğg]u)|E\s*=", t, re.IGNORECASE):
        return {"type": "elektrik_alan", "q": "Q"}

    return None


def _extract_resistor_labels(metin):
    """R₁=6 Ω, R2 = 12Ω gibi ifadelerden direnç etiketlerini çıkarır."""
    labels = []
    pattern = r"R\s*([₁2₃4]|\d+)\s*=\s*(\d+(?:[.,]\d+)?)\s*([oO]?hm|Ω)?"
    for m in re.finditer(pattern, metin):
        idx, val, unit = m.groups()
        sub = idx.replace("1", "₁").replace("2", "₂").replace("3", "₃").replace("4", "₄")
        u = unit or "Ω"
        if u.lower() == "ohm":
            u = "Ω"
        labels.append(f"R{sub} = {val} {u}".strip())
    if not labels:
        # R₁, R₂, R₃ ... varsa onları kullan
        for m in re.finditer(r"R\s*([₁2₃4\d]+)", metin):
            idx = m.group(1)
            sub = idx.replace("1", "₁").replace("2", "₂").replace("3", "₃").replace("4", "₄")
            labels.append(f"R{sub}")
    if not labels:
        labels = ["R₁", "R₂", "R₃"]
    n = max(2, min(len(labels), 4))
    labels = labels[:n]
    # En az 2 olsun
    while len(labels) < 2:
        labels.append(f"R{len(labels)+1}")
    return n, labels


def _extract_currents(metin):
    """'I₁ = 3 A', 'I2 = 5A' gibi giren akımları çıkarır."""
    items = []
    for m in re.finditer(r"I\s*([₁2₃4\d]+)\s*=\s*(\d+(?:[.,]\d+)?)\s*A", metin):
        idx = m.group(1)
        sub = idx.replace("1", "₁").replace("2", "₂").replace("3", "₃").replace("4", "₄")
        items.append({"label": f"I{sub}", "value": f"{m.group(2)} A"})
    return items[:2]


def _extract_question_mark_currents(metin):
    """'I₃ = ?' gibi bilinmeyen akımları çıkarır."""
    items = []
    for m in re.finditer(r"I\s*([₁2₃4\d]+)\s*=\s*\?", metin):
        idx = m.group(1)
        sub = idx.replace("1", "₁").replace("2", "₂").replace("3", "₃").replace("4", "₄")
        items.append({"label": f"I{sub}", "value": "?"})
    return items[:2]
# -*- coding: utf-8 -*-
"""동의서 점검용 문서 파서. PDF에서 라인 단위 문단 + 폰트 크기 추출."""


class Paragraph:
    def __init__(self, text="", style_name=None, font_size=None, bold=None):
        self.text = text
        self.style_name = style_name
        self.font_size = font_size
        self.bold = bold

    def full_text(self):
        return self.text


class ParsedDocument:
    def __init__(self, paragraphs):
        self.paragraphs = paragraphs


def _line_font_sizes(page):
    out = {}
    try:
        words = page.extract_words(extra_attrs=["size"]) if hasattr(page, "extract_words") else []
        lines = {}
        for w in words:
            top = round(w.get("top", 0))
            lines.setdefault(top, []).append(w.get("size"))
        for i, top in enumerate(sorted(lines.keys())):
            sizes = [s for s in lines[top] if s]
            if sizes:
                out[i] = round(sum(sizes) / len(sizes), 2)
    except Exception:
        pass
    return out


def load_pdf(path):
    """텍스트 레이어가 있는 PDF를 라인 단위 Paragraph로 변환."""
    import pdfplumber
    paras = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            sizes = _line_font_sizes(page)
            for idx, ln in enumerate(txt.split("\n")):
                if ln.strip():
                    paras.append(Paragraph(text=ln, font_size=sizes.get(idx)))
    return ParsedDocument(paras)

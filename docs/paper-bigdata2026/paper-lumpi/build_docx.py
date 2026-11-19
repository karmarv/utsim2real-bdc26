#!/usr/bin/env python
"""Build the Word versions of the two track reports, inside the IEEE conference template.

    python docs/paper-bigdata2026/paper-lumpi/build_docx.py                    # both tracks: report_lumpi.md, report_v2x.md -> OUTPUT
    python docs/paper-bigdata2026/paper-lumpi/build_docx.py --track lumpi      # one track
    python docs/paper-bigdata2026/paper-lumpi/build_docx.py --pdf              # also render a PDF with LibreOffice (preview only)

OUTPUT names follow the organizers' report title (Final Report - IEEE Big Data Cup 2026 - Track Name - Team Name):
Final_Report_IEEE_Big_Data_Cup_2026_LUMPI_Track_KarmaRV.docx and ..._V2X-Real_Track_KarmaRV.docx.

Standard library only (no new package in .venv_ut). The template (template/ieee-conference-template-letter.docx, the
IEEE letter-size conference template in Strict OOXML) supplies every style, the automatic numbering of headings
("I."), figure captions ("Fig. 1."), table heads ("TABLE I.") and references ("[1]"), the page geometry and the
first-page footer. The builder replaces only the body. report.md uses a small Markdown subset:

  # Title                                  paper title
  plain lines after the title              author block, one Author line each, up to the first blank line
  **Abstract**- text / **Keywords**- text  abstract and keywords; the label gets the IEEE en dash
  ## I. Heading / ### A. Heading           Heading 1 / Heading 2 (the numeral is kept as text and the style's list
                                           numbering is switched off, so a float cannot separate a number from its head)
  #### 1) Heading                          Heading 3
  ## Acknowledgment / ## References        unnumbered component heads (Heading 5)
  - item                                   bullet list
  Table: TABLE I. Caption                  table head, followed by a pipe table; a row with only its first cell
                                           filled is a group row spanning the table (e.g. | **Final phase** | | |)
  ![Fig. 1](figures/x.png) + *Fig. 1. Caption*   figure (column width) and its caption line
  <!-- wide --> / <!-- wide bottom -->     the next table or figure spans both columns, floated to the top / bottom of its page
  <!-- docx-skip --> ... <!-- /docx-skip -->   Markdown-only text
  [1] Reference                            entries under ## References
  **bold**, *italic*, `code`               inline formatting
Captions and references carry their numbers in Markdown; the builder checks them against the document order.
"""
import argparse
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template" / "ieee-conference-template-letter.docx"
OUTPUTS = {"lumpi": "Vishwakarma_BigDataCup2026_LUMPI.docx"}                 # paper build (2026-11-18): one track per folder
SOURCES = {"lumpi": "paper_lumpi.md"}
FOOTER = ""                                  # first-page footer; --footer sets the IEEE copyright line for camera-ready
R_NS = "http://purl.oclc.org/ooxml/officeDocument/relationships"
A_NS = "http://purl.oclc.org/ooxml/drawingml/main"
PIC_NS = "http://purl.oclc.org/ooxml/drawingml/picture"
IMG_REL = "http://purl.oclc.org/ooxml/officeDocument/relationships/image"
PAGE = '<w:pgSz w:w="612pt" w:h="792pt" w:code="1"/>'
MARGIN = '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" w:left="44.65pt" w:header="36pt" w:footer="36pt" w:gutter="0pt"/>'
COL_PT, FULL_PT = 252.0, 522.7              # one column and the full text width, in points
EMU_PER_PT = 12700
NONUM = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'   # switches a style's list numbering off
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11,
         "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20}


def sect(cols: int, first: bool = False) -> str:
    """A section-properties element; `first` = the title section with the template's first-page footer."""
    head = f'<w:footerReference w:type="first" r:id="rId8"/>' if first else ""
    typ = "" if first else '<w:type w:val="continuous"/>'
    col = '<w:cols w:num="2" w:space="18pt"/>' if cols == 2 else '<w:cols w:space="36pt"/>'
    return f"<w:sectPr>{head}{typ}{PAGE}{MARGIN}{col}{'<w:titlePg/>' if first else ''}<w:docGrid w:linePitch=\"360\"/></w:sectPr>"


def runs(text: str, size: int | None = None) -> str:
    """Inline Markdown (**bold**, *italic*, `code`) to w:r elements."""
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text):
        if not tok:
            continue
        rpr = []
        if tok.startswith("**") and tok.endswith("**"):
            tok, rpr = tok[2:-2], ["<w:b/><w:bCs/>"]
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            tok, rpr = tok[1:-1], ["<w:i/><w:iCs/>"]
        elif tok.startswith("`") and tok.endswith("`"):
            tok, rpr = tok[1:-1], ['<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>']
        if size:
            rpr.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
        pr = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""
        for k, piece in enumerate(tok.split("\u2011")):            # U+2011 -> Word non-breaking hyphen
            if k:
                out.append(f'<w:r>{pr}<w:noBreakHyphen/></w:r>')
            if piece:
                out.append(f'<w:r>{pr}<w:t xml:space="preserve">{escape(piece)}</w:t></w:r>')
    return "".join(out)


def para(style: str, text: str = "", extra_ppr: str = "", body: str | None = None) -> str:
    content = body if body is not None else runs(text)
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{extra_ppr}</w:pPr>{content}</w:p>'


def png_size(path: Path) -> tuple[int, int]:
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: only PNG figures are supported")
    return struct.unpack(">II", head[16:24])


class Builder:
    def __init__(self):
        self.body: list[str] = []
        self.images: list[tuple[str, Path]] = []        # (rId, file)
        self.fig_no = 0
        self.tab_no = 0
        self.ref_no = 0

    # -- elements ---------------------------------------------------------------------------------------------
    @staticmethod
    def float_block(inner: str, place: str = "top", column: bool = False) -> str:
        """A float: a borderless one-cell table anchored at the top (or bottom) of the page. Full width spans both
        columns without section breaks (the usual IEEE two-column layout); `column` floats at the top of its column."""
        width = COL_PT if column else FULL_PT
        horz = 'w:horzAnchor="text" w:tblpX="0"' if column else 'w:horzAnchor="margin" w:tblpXSpec="center"'
        return (f'<w:tbl><w:tblPr><w:tblpPr w:leftFromText="0" w:rightFromText="0" w:topFromText="0" w:bottomFromText="200" '
                f'w:vertAnchor="margin" {horz} w:tblpYSpec="{place}"/>'
                f'<w:tblOverlap w:val="never"/><w:tblW w:w="{width:.1f}pt" w:type="dxa"/><w:jc w:val="center"/>'
                f'<w:tblBorders><w:top w:val="nil"/><w:start w:val="nil"/><w:bottom w:val="nil"/><w:end w:val="nil"/>'
                f'<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders><w:tblLayout w:type="fixed"/>'
                f'<w:tblCellMar><w:top w:w="0pt" w:type="dxa"/><w:start w:w="0pt" w:type="dxa"/><w:bottom w:w="0pt" w:type="dxa"/>'
                f'<w:end w:w="0pt" w:type="dxa"/></w:tblCellMar><w:tblLook w:firstRow="0" w:lastRow="0" w:firstColumn="0" '
                f'w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr><w:tblGrid><w:gridCol w:w="{int(width * 20)}"/></w:tblGrid>'
                f'<w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:w="{width:.1f}pt" w:type="dxa"/></w:tcPr>{inner}</w:tc></w:tr></w:tbl>')

    def figure(self, caption: str, path: Path, wide: bool, place: str = "top"):
        m = re.match(r"Fig\.\s*(\d+)\.\s*(.*)", caption)
        if not m:
            raise SystemExit(f"figure caption must start with 'Fig. N.': {caption[:60]}")
        self.fig_no += 1
        if int(m.group(1)) != self.fig_no:
            raise SystemExit(f"figure numbered {m.group(1)} but it is figure {self.fig_no} in document order")
        w_px, h_px = png_size(path)
        width_pt = (FULL_PT if wide else COL_PT) - 2
        cx = int(width_pt * EMU_PER_PT)
        cy = int(cx * h_px / w_px)
        rid = f"rIdFig{len(self.images) + 1}"
        self.images.append((rid, path))
        n = len(self.images)
        drawing = (
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{100 + n}" name="Figure {n}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{A_NS}" noChangeAspect="1"/>'
            f'</wp:cNvGraphicFramePr><a:graphic xmlns:a="{A_NS}"><a:graphicData uri="{PIC_NS}"><pic:pic xmlns:pic="{PIC_NS}">'
            f'<pic:nvPicPr><pic:cNvPr id="{100 + n}" name="{escape(path.name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'</pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
        pic = f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="0pt" w:after="0pt"/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>'
        # literal "Fig. N." (list numbering is switched off): renderers number captions inside floats separately
        cap = para("figurecaption", f"Fig. {self.fig_no}.\u2003{m.group(2)}", extra_ppr=NONUM)
        if wide:
            self.body.append(self.float_block(pic + cap, place))
        elif place == "col":
            self.body.append(self.float_block(pic + cap, "top", column=True))
        else:
            self.body.append(pic.replace('w:before="0pt"', 'w:before="6pt"'))
            self.body.append(cap)

    def table(self, caption: str, rows: list[list[str]], wide: bool, place: str = "top"):
        m = re.match(r"TABLE\s+([IVX]+)\.\s*(.*)", caption)
        if not m:
            raise SystemExit(f"table caption must start with 'TABLE N.': {caption[:60]}")
        self.tab_no += 1
        if ROMAN.get(m.group(1)) != self.tab_no:
            raise SystemExit(f"table numbered {m.group(1)} but it is table {self.tab_no} in document order")
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        total = (FULL_PT if wide else COL_PT) - 4
        # column widths proportional to the longest cell text, with a floor
        plain = [[re.sub(r"[*`]", "", r[c]).strip() for c in range(ncol)] for r in rows]
        word = [max(max((len(w) for w in row[c].split()), default=1) for row in plain) for c in range(ncol)]
        minw = [min(4.3 * x + 7.0, total / 2) for x in word]                 # 8 pt text is about 4.3 pt per character
        weights = [max(6.0, min(float(max(len(row[c]) for row in plain)), 50.0)) for c in range(ncol)]
        rest = max(total - sum(minw), 0.0)
        # fit content first: each column gets up to its one-line width, in proportion to what it still needs;
        # any width left after that is shared by text length
        natural = [4.3 * max(len(row[c]) for row in plain) + 7.0 for c in range(ncol)]
        need = [max(n - mw, 0.0) for n, mw in zip(natural, minw)]
        if sum(need) <= rest:
            spare = rest - sum(need)
            widths = [mw + nd + spare * w / sum(weights) for mw, nd, w in zip(minw, need, weights)]
        else:
            widths = [mw + rest * nd / sum(need) for mw, nd in zip(minw, need)]
        if sum(widths) > total:                                               # too many columns: scale down
            widths = [w * total / sum(widths) for w in widths]
        grid = "".join(f'<w:gridCol w:w="{int(w * 20)}"/>' for w in widths)
        border = ('<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'      # schema order:
                  '<w:start w:val="single" w:sz="2" w:space="0" w:color="auto"/>'                    # top, start, bottom,
                  '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'                   # end, insideH, insideV
                  '<w:end w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
                  '<w:insideH w:val="single" w:sz="2" w:space="0" w:color="auto"/>'
                  '<w:insideV w:val="single" w:sz="2" w:space="0" w:color="auto"/></w:tblBorders>')
        cell_mar = '<w:tblCellMar><w:start w:w="2.5pt" w:type="dxa"/><w:end w:w="2.5pt" w:type="dxa"/></w:tblCellMar>'
        # a column is centred only when every body cell is short (numbers, short labels); text columns start-align
        short = [all(len(re.sub(r"[*`]", "", r[c]).strip()) <= 12 for r in rows[1:]) for c in range(ncol)]
        trs = []
        for i, r in enumerate(rows):
            header = i == 0
            last = i == len(rows) - 1
            if not header and r[0].strip() and not any(x.strip() for x in r[1:]):
                # a group row (only the first cell filled): one shaded cell across the table, e.g. a phase heading
                keep = "" if last else "<w:keepNext/>"
                tc = (f'<w:tc><w:tcPr><w:tcW w:w="{sum(widths):.1f}pt" w:type="dxa"/><w:gridSpan w:val="{ncol}"/>'
                      f'<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/><w:vAlign w:val="center"/></w:tcPr>'
                      f'<w:p><w:pPr><w:pStyle w:val="tablecopy"/>{keep}<w:spacing w:before="0pt" w:after="0pt"/>'
                      f'<w:jc w:val="start"/></w:pPr>{runs(r[0].strip())}</w:p></w:tc>')
                trs.append(f"<w:tr><w:trPr><w:cantSplit/></w:trPr>{tc}</w:tr>")
                continue
            tcs = []
            for c, (txt, w) in enumerate(zip(r, widths)):
                style = "tablecolhead" if header else "tablecopy"
                jc = '<w:jc w:val="center"/>' if (c > 0 and short[c]) else '<w:jc w:val="start"/>'
                shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if header else ""
                keep = "" if last else "<w:keepNext/>"            # keeps a column table in one piece
                tcs.append(f'<w:tc><w:tcPr><w:tcW w:w="{w:.1f}pt" w:type="dxa"/>{shade}<w:vAlign w:val="center"/></w:tcPr>'
                           f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{keep}<w:spacing w:before="0pt" w:after="0pt"/>{jc}</w:pPr>{runs(txt.strip())}</w:p></w:tc>')
            trpr = '<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if header else '<w:trPr><w:cantSplit/></w:trPr>'
            trs.append(f"<w:tr>{trpr}{''.join(tcs)}</w:tr>")
        tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{total:.1f}pt" w:type="dxa"/><w:jc w:val="center"/>{border}'
               f'<w:tblLayout w:type="fixed"/>{cell_mar}<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr>'
               f'<w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
        head = para("tablehead", f"TABLE {m.group(1)}.\u2003{m.group(2)}", extra_ppr="<w:keepNext/>" + NONUM)
        if wide:
            inner = head.replace(NONUM, NONUM + '<w:spacing w:before="0pt" w:after="4pt"/>', 1)   # spacing after numPr
            self.body.append(self.float_block(inner + tbl + '<w:p><w:pPr><w:spacing w:before="0pt" w:after="0pt"/></w:pPr></w:p>', place))
        elif place == "col":
            inner = head.replace(NONUM, NONUM + '<w:spacing w:before="0pt" w:after="4pt"/>', 1)
            self.body.append(self.float_block(inner + tbl + '<w:p><w:pPr><w:spacing w:before="0pt" w:after="0pt"/></w:pPr></w:p>', "top", column=True))
        else:
            self.body.append(head)
            self.body.append(tbl)
            self.body.append(para("BodyText", body="", extra_ppr='<w:spacing w:before="0pt" w:after="4pt"/>'))

    def reference(self, text: str):
        m = re.match(r"\[(\d+)\]\s*(.*)", text)
        self.ref_no += 1
        if not m or int(m.group(1)) != self.ref_no:
            raise SystemExit(f"reference {self.ref_no} out of order: {text[:60]}")
        self.body.append(para("references", m.group(2)))

    # -- document ---------------------------------------------------------------------------------------------
    def parse(self, md: str):
        lines = md.splitlines()
        i, n = 0, len(lines)
        skip = False
        wide_next = False
        place_next = "top"
        in_refs = False
        title_done = False
        authors: list[str] = []
        para_buf: list[str] = []

        def flush():
            if para_buf:
                text = " ".join(s.strip() for s in para_buf)
                if in_refs:
                    for ref in re.split(r"(?=\[\d+\]\s)", text):
                        if ref.strip():
                            self.reference(ref.strip())
                elif text.startswith("where "):                 # continues a display equation: no indent
                    self.body.append(para("BodyText", text, extra_ppr='<w:ind w:firstLine="0"/>'))
                else:
                    self.body.append(para("BodyText", text))
                para_buf.clear()

        while i < n:
            line = lines[i]
            s = line.strip()
            if s == "<!-- docx-skip -->":
                skip = True
            elif s == "<!-- /docx-skip -->":
                skip = False
            elif skip:
                pass
            elif s in ("<!-- wide -->", "<!-- wide top -->", "<!-- wide bottom -->"):
                flush()
                wide_next = True
                place_next = "bottom" if "bottom" in s else "top"
            elif s == "<!-- float -->":                       # column-width float at the top of its column
                flush()
                wide_next = False
                place_next = "col"
            elif s.startswith("<!--"):
                pass
            elif s.startswith("# ") and not title_done:
                self.body.append(para("papertitle", s[2:].strip()))
                title_done = True
                j = i + 1                                     # author block: the lines up to the first blank line
                while j < n and lines[j].strip() and not lines[j].strip().startswith(("<!--", "**Abstract**")):
                    authors.append(lines[j].strip().rstrip("\\").strip())
                    j += 1
                for k, a in enumerate(authors):
                    first = k == 0
                    ppr = '<w:spacing w:before="12pt" w:after="0pt"/>' if first else '<w:spacing w:before="0pt" w:after="0pt"/>'
                    if k == len(authors) - 1:
                        ppr = ppr.replace('w:after="0pt"', 'w:after="14pt"') + sect(1, first=True)
                    self.body.append(para("Author", a, extra_ppr=ppr))
                i = j
                continue
            elif s.startswith("**Abstract**") or s.startswith("**Keywords**"):
                flush()
                style = "Abstract" if s.startswith("**Abstract**") else "Keywords"
                label, rest = s[2:].split("**", 1)
                rest = rest.lstrip(" -\u2013\u2014:")
                body = f'<w:r><w:rPr><w:i/><w:iCs/></w:rPr><w:t xml:space="preserve">{label}\u2013</w:t></w:r>' + runs(rest)
                self.body.append(para(style, body=body))
            elif s.startswith("## "):
                flush()
                h = s[3:].strip()
                m = re.match(r"([IVX]+)\.\s+(.*)", h)
                if m:
                    self.body.append(para("Heading1", f"{m.group(1)}. {m.group(2)}", extra_ppr=NONUM))
                    in_refs = False
                else:
                    self.body.append(para("Heading5", h))
                    in_refs = h.lower().startswith("reference")
            elif s.startswith("### "):
                flush()
                self.body.append(para("Heading2", s[4:].strip(), extra_ppr=NONUM))
            elif s.startswith("#### "):
                flush()
                self.body.append(para("Heading3", s[5:].strip(), extra_ppr=NONUM))
            elif s.startswith("Table:"):
                flush()
                caption = s[len("Table:"):].strip()
                rows = []
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                while j < n and lines[j].strip().startswith("|"):
                    cells = [c for c in lines[j].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r"\s*:?-{2,}:?\s*", c) for c in cells):
                        rows.append(cells)
                    j += 1
                self.table(caption, rows, wide_next, place_next)
                wide_next = False
                place_next = "top"
                i = j
                continue
            elif re.match(r"!\[.*\]\(.*\)", s):
                flush()
                m = re.match(r"!\[(.*)\]\((.*)\)", s)
                caption = m.group(1)
                j = i + 1                                     # a visible caption line "*Fig. N. ...*" may follow
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and re.match(r"\*Fig\.\s*\d+\.", lines[j].strip()):
                    caption = lines[j].strip().strip("*")
                    i = j
                self.figure(caption, HERE / m.group(2), wide_next, place_next)
                wide_next = False
                place_next = "top"
            elif s.startswith("$$ "):
                # display equation: "$$ <equation> | (<n>)", centred in the column with its number flush right
                flush()
                eq, _, num = s[3:].rpartition("|")
                tab = '<w:r><w:tab/></w:r>'
                ppr = ('<w:keepNext/><w:tabs><w:tab w:val="clear" w:pos="14.40pt"/><w:tab w:val="center" w:pos="126pt"/><w:tab w:val="right" w:pos="251pt"/></w:tabs>'
                       '<w:spacing w:before="4pt" w:after="4pt"/><w:ind w:firstLine="0"/><w:jc w:val="start"/>')
                self.body.append(para("BodyText", extra_ppr=ppr, body=tab + runs(eq.strip()) + tab + runs(num.strip())))
            elif s.startswith("- "):
                flush()
                self.body.append(para("bulletlist", s[2:].strip()))
            elif not s:
                flush()
            else:
                para_buf.append(s)
            i += 1
        flush()

    def write(self, out: Path):
        with zipfile.ZipFile(TEMPLATE) as z:
            files = {name: z.read(name) for name in z.namelist() if not name.endswith("/")}
        doc = files["word/document.xml"].decode("utf8")
        start = doc.index("<w:body>") + len("<w:body>")
        end = doc.index("</w:body>")
        # balanced last page (IEEE): the two-column section ends with a continuous break, then an empty one-column section
        tiny = '<w:spacing w:before="0pt" w:after="0pt" w:line="1pt" w:lineRule="exact"/><w:rPr><w:sz w:val="2"/></w:rPr>'
        tail = f'<w:p><w:pPr>{tiny}{sect(2)}</w:pPr></w:p><w:p><w:pPr>{tiny}</w:pPr></w:p>'
        doc = doc[:start] + "".join(self.body) + tail + sect(1) + doc[end:]
        files["word/document.xml"] = doc.encode("utf8")
        meta = getattr(self, "meta", None)
        if meta:                                    # document properties: the PDF Title/Author come from here
            files["docProps/core.xml"] = core_xml(**meta).encode("utf8")
        rels = files["word/_rels/document.xml.rels"].decode("utf8")
        add = "".join(f'<Relationship Id="{rid}" Type="{IMG_REL}" Target="media/{p.name}"/>' for rid, p in self.images)
        files["word/_rels/document.xml.rels"] = rels.replace("</Relationships>", add + "</Relationships>").encode("utf8")
        ct = files["[Content_Types].xml"].decode("utf8")
        if 'Extension="png"' not in ct:
            ct = ct.replace("<Default Extension=\"xml\"", '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"', 1)
        files["[Content_Types].xml"] = ct.encode("utf8")
        # the template's first-page footer carries a placeholder copyright line: blank it until IEEE supplies it
        foot = files["word/footer1.xml"].decode("utf8")
        files["word/footer1.xml"] = foot.replace("XXX-X-XXXX-XXXX-X/XX/$XX.00 ©20XX IEEE", escape(FOOTER)).encode("utf8")
        for _, p in self.images:
            files[f"word/media/{p.name}"] = p.read_bytes()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            order = ["[Content_Types].xml"] + [k for k in files if k != "[Content_Types].xml"]
            for k in order:
                z.writestr(k, files[k])



def pdf_metadata(src: str) -> dict:
    """Title, author, subject and keywords for the document properties (and so the PDF metadata)."""
    first = src.splitlines()[0]
    title = first[2:].replace("\u2011", "-").replace("\u00a0", " ").strip()
    kw = re.search(r"^\*\*Keywords\*\*-\s*(.*)$", src, flags=re.M)
    track = "V2X-Real" if "V2X" in title else "LUMPI"
    return {"title": title, "author": "Rahul Vishwakarma",
            "subject": f"IEEE BigData 2026 Cup, UCF UrbanTwin Sim2Real LiDAR Challenge, {track} track",
            "keywords": ""}   # LibreOffice splits keyword phrases into single words, so none are set


def core_xml(title: str, author: str, subject: str, keywords: str) -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title)}</dc:title><dc:subject>{escape(subject)}</dc:subject>'
            f'<dc:creator>{escape(author)}</dc:creator><cp:keywords>{escape(keywords)}</cp:keywords>'
            f'<cp:lastModifiedBy>{escape(author)}</cp:lastModifiedBy><cp:revision>1</cp:revision>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--track", nargs="*", choices=sorted(OUTPUTS), default=sorted(OUTPUTS))
    ap.add_argument("--pdf", action="store_true", help="render a PDF next to the .docx with LibreOffice (soffice)")
    ap.add_argument("--footer", default="", help="first-page footer text, e.g. the IEEE copyright line of the camera-ready")
    ap.add_argument("--out", default=None, help="output .docx name (default: OUTPUTS)")
    a = ap.parse_args()
    global FOOTER
    FOOTER = a.footer
    for t in a.track:
        b = Builder()
        src = (HERE / SOURCES[t]).read_text(encoding="utf8")
        b.parse(src)
        b.meta = pdf_metadata(src)
        out = HERE / (a.out or OUTPUTS[t])
        b.write(out)
        print(f"{out.name}: {b.fig_no} figures, {b.tab_no} tables, {b.ref_no} references, {len(b.body)} body elements")
        if a.pdf:
            if not shutil.which("soffice"):
                sys.exit("soffice not found")
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out.parent), str(out)],
                           check=True, capture_output=True, timeout=600)
            print(out.with_suffix(".pdf").name)


if __name__ == "__main__":
    main()

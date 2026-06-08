import io
from datetime import datetime
from flask import make_response

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.platypus.flowables import HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ── Brand Colors ──────────────────────────────────────────────────────
C_PRIMARY   = colors.HexColor('#0D47A1')
C_SECONDARY = colors.HexColor('#E65100')
C_ACCENT    = colors.HexColor('#0288D1')
C_SUCCESS   = colors.HexColor('#2E7D32')
C_DANGER    = colors.HexColor('#C62828')
C_WARNING   = colors.HexColor('#F9A825')
C_TEXT      = colors.HexColor('#1A2634')
C_TEXT2     = colors.HexColor('#3D5166')
C_MUTED     = colors.HexColor('#6B7A90')
C_LIGHT     = colors.HexColor('#EEF2F7')
C_WHITE     = colors.white
C_BORDER    = colors.HexColor('#DDE3EA')
C_HEADER_BG = colors.HexColor('#0D47A1')
C_ALT_ROW   = colors.HexColor('#F5F7FA')


def generate_pdf_report(stats, suggestions, records):
    """Generate a professional PDF report using ReportLab and return a Flask response."""
    if not REPORTLAB_AVAILABLE:
        return generate_html_fallback(stats, suggestions, records)

    buffer = io.BytesIO()
    now    = datetime.now()
    report_id = f"PMTA-{now.strftime('%Y%m%d%H%M%S')}"

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
        title="Metro Bus Feedback Report",
        author="Punjab Mass Transit Authority",
        subject="Passenger Feedback Analysis Report",
    )

    W = A4[0] - 4.0 * cm  # usable width

    # ── Styles ────────────────────────────────────────────────────────
    SS = getSampleStyleSheet()

    def style(name, **kw):
        base = SS.get(name, SS['Normal'])
        return ParagraphStyle(name + '_custom', parent=base, **kw)

    sTitle     = style('Title',  fontName='Helvetica-Bold', fontSize=20,
                       textColor=C_WHITE,  alignment=TA_CENTER, spaceAfter=2)
    sSubTitle  = style('Normal', fontName='Helvetica',      fontSize=10,
                       textColor=colors.HexColor('#BDD0F5'), alignment=TA_CENTER, spaceAfter=2)
    sCaption   = style('Normal', fontName='Helvetica',      fontSize=9,
                       textColor=colors.HexColor('#90CAF9'), alignment=TA_CENTER)
    sSection   = style('Heading1', fontName='Helvetica-Bold', fontSize=12,
                       textColor=C_PRIMARY, spaceBefore=14, spaceAfter=6,
                       borderPadding=(0, 0, 4, 0))
    sBody      = style('Normal', fontName='Helvetica', fontSize=9.5,
                       textColor=C_TEXT2, leading=14, spaceAfter=4)
    sBodyBold  = style('Normal', fontName='Helvetica-Bold', fontSize=9.5,
                       textColor=C_TEXT,  leading=14)
    sCell      = style('Normal', fontName='Helvetica', fontSize=9,
                       textColor=C_TEXT2, leading=12)
    sCellBold  = style('Normal', fontName='Helvetica-Bold', fontSize=9,
                       textColor=C_TEXT,  leading=12)
    sCellCtr   = style('Normal', fontName='Helvetica', fontSize=9,
                       textColor=C_TEXT2, leading=12, alignment=TA_CENTER)
    sCellBoldW = style('Normal', fontName='Helvetica-Bold', fontSize=9,
                       textColor=C_WHITE, leading=12, alignment=TA_CENTER)
    sSug       = style('Normal', fontName='Helvetica', fontSize=9.5,
                       textColor=C_TEXT2, leading=14, leftIndent=10)
    sFooter    = style('Normal', fontName='Helvetica', fontSize=8,
                       textColor=C_MUTED, alignment=TA_CENTER)

    # ── Helpers ────────────────────────────────────────────────────────
    def section_header(title):
        return [
            Spacer(1, 6),
            HRFlowable(width=W, thickness=2, color=C_PRIMARY, spaceAfter=6),
            Paragraph(title.upper(), sSection),
        ]

    def stat_table(items):
        """items = [(label, value, color), ...]"""
        col_w = W / len(items)
        data  = [[Paragraph(str(v), style('Normal', fontName='Helvetica-Bold',
                                          fontSize=22, textColor=c, alignment=TA_CENTER))
                  for _, v, c in items],
                 [Paragraph(lbl.upper(), style('Normal', fontName='Helvetica',
                                       fontSize=8, textColor=C_MUTED, alignment=TA_CENTER))
                  for lbl, _, _ in items]]
        t = Table(data, colWidths=[col_w] * len(items), rowHeights=[36, 20])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_WHITE),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('LINEBELOW',  (0, 0), (-1, 0),  2,   C_PRIMARY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROUNDEDCORNERS', [6]),
        ]))
        return t

    def bar_table(rows_data, col_headers):
        """Generic styled table."""
        header_row = [Paragraph(h, sCellBoldW) for h in col_headers]
        body_rows  = []
        for i, row in enumerate(rows_data):
            bg = C_ALT_ROW if i % 2 == 0 else C_WHITE
            body_rows.append((row, bg))

        all_rows   = [header_row] + [r for r, _ in body_rows]
        col_w_def  = W / len(col_headers)
        t = Table(all_rows, colWidths=[col_w_def] * len(col_headers))
        style_cmds = [
            ('BACKGROUND',    (0, 0), (-1, 0),  C_PRIMARY),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0),  9),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  C_WHITE),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUND', (0, 1), (-1, -1), [r[1] for r in body_rows]),
            ('GRID',          (0, 0), (-1, -1), 0.4, C_BORDER),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        for i, (_, bg) in enumerate(body_rows, start=1):
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
        t.setStyle(TableStyle(style_cmds))
        return t

    # ══════════════════════════════════════════════════════════════════
    # BUILD STORY
    # ══════════════════════════════════════════════════════════════════
    story = []
    total     = stats.get('total',    0)
    pending   = stats.get('pending',  0)
    complete  = stats.get('complete', 0)
    on_hold   = stats.get('on_hold',  0)
    emotions  = stats.get('emotions', {})
    qualities = stats.get('qualities', {})
    routes    = stats.get('routes',   {})

    # ── COVER HEADER ──────────────────────────────────────────────────
    s_cap2 = style('Normal', fontName='Helvetica', fontSize=8,
                 textColor=colors.HexColor('#90CAF9'), alignment=TA_CENTER)
    header_data = [
        [Paragraph("METRO BUS PASSENGER FEEDBACK", sTitle)],
        [Paragraph("OFFICIAL ANALYSIS REPORT", sSubTitle)],
        [Paragraph("Punjab Mass Transit Authority  |  Pakistan", sCaption)],
        [Paragraph(f"Report ID: {report_id}  |  Generated: {now.strftime('%d %B %Y, %I:%M %p')}", s_cap2)],
    ]
    header_tbl = Table(header_data, colWidths=[W])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, -1), C_PRIMARY),
        ('TOPPADDING',     (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 18),
        ('LEFTPADDING',    (0, 0), (-1, -1), 20),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 16))

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────
    story += section_header("Executive Summary")
    bad_pct = round(qualities.get('Bad', 0) / total * 100) if total > 0 else 0
    exc_pct = round(qualities.get('Excellent', 0) / total * 100) if total > 0 else 0
    ang_pct = round(emotions.get('Angry', 0) / total * 100) if total > 0 else 0
    summary_text = (
        f"This report covers <b>{total}</b> passenger feedback records collected through the Metro Bus "
        f"Feedback Analyzer system. Of the total records, <b>{pending}</b> complaints are currently "
        f"pending review, <b>{complete}</b> have been resolved, and <b>{on_hold}</b> are on hold. "
        f"Service quality analysis indicates <b>{bad_pct}%</b> of feedback is rated <b>Bad</b> and "
        f"<b>{exc_pct}%</b> rated <b>Excellent</b>. Passenger emotion analysis shows <b>{ang_pct}%</b> "
        f"of respondents expressed anger or high frustration. "
        f"This report provides route-level analysis, emotion distribution, quality classification, "
        f"and AI-generated improvement recommendations for operational decision-making."
    )
    story.append(Paragraph(summary_text, sBody))
    story.append(Spacer(1, 10))

    # ── KEY METRICS ───────────────────────────────────────────────────
    story += section_header("Key Metrics Overview")
    story.append(stat_table([
        ("Total Complaints", total,    C_PRIMARY),
        ("Pending Review",  pending,   C_WARNING),
        ("Completed",       complete,  C_SUCCESS),
        ("On Hold",         on_hold,   C_ACCENT),
    ]))
    story.append(Spacer(1, 14))

    # ── QUALITY CLASSIFICATION ─────────────────────────────────────────
    story += section_header("Service Quality Classification")
    q_rows = []
    for q, cnt in qualities.items():
        pct = round(cnt / total * 100) if total > 0 else 0
        c   = C_DANGER if q == 'Bad' else (C_SUCCESS if q == 'Excellent' else C_WARNING)
        q_rows.append([
            Paragraph(q, sCellBold),
            Paragraph(str(cnt), sCellCtr),
            Paragraph(f"{pct}%", style('Normal', fontName='Helvetica-Bold', fontSize=9,
                                       textColor=c, alignment=TA_CENTER)),
        ])
    if q_rows:
        q_tbl = Table(
            [[Paragraph(h, sCellBoldW) for h in ["Classification", "Count", "Percentage"]]] + q_rows,
            colWidths=[W * 0.5, W * 0.25, W * 0.25]
        )
        q_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  C_PRIMARY),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, C_BORDER),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('BACKGROUND',    (0, 1), (-1, 1),  C_ALT_ROW),
            ('BACKGROUND',    (0, 3), (-1, 3),  C_ALT_ROW),
        ]))
        story.append(q_tbl)
    story.append(Spacer(1, 14))

    # ── EMOTION DISTRIBUTION ──────────────────────────────────────────
    story += section_header("Passenger Emotion Distribution")
    em_colors = {
        'Angry':     C_DANGER,
        'Frustrated': C_WARNING,
        'Neutral':   C_MUTED,
        'Satisfied': C_ACCENT,
        'Happy':     C_SUCCESS,
    }
    em_rows = []
    for i, (emo, cnt) in enumerate(emotions.items()):
        pct = round(cnt / total * 100) if total > 0 else 0
        c   = em_colors.get(emo, C_TEXT)
        bar_cells = [
            Paragraph(emo, sCellBold),
            Paragraph(str(cnt), sCellCtr),
            Paragraph(f"{pct}%", style('Normal', fontName='Helvetica-Bold', fontSize=9,
                                       textColor=c, alignment=TA_CENTER)),
            Paragraph("|" * int(pct / 4) if pct else "-",
                      style('Normal', fontName='Helvetica', fontSize=8,
                            textColor=c, alignment=TA_LEFT)),
        ]
        em_rows.append(bar_cells)

    if em_rows:
        em_tbl = Table(
            [[Paragraph(h, sCellBoldW) for h in ["Emotion", "Count", "Share", "Visual Distribution"]]] + em_rows,
            colWidths=[W * 0.22, W * 0.13, W * 0.12, W * 0.53]
        )
        em_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  C_PRIMARY),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, C_BORDER),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (0, 1), (0, -1),  'LEFT'),
            ('ALIGN',         (3, 1), (3, -1),  'LEFT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        for i in range(0, len(em_rows), 2):
            em_tbl.setStyle(TableStyle([('BACKGROUND', (0, i+1), (-1, i+1), C_ALT_ROW)]))
        story.append(em_tbl)
    story.append(Spacer(1, 14))

    # ── ROUTE-WISE COMPLAINTS ──────────────────────────────────────────
    story += section_header("Route-wise Complaint Volume")
    if routes:
        max_cnt = max(routes.values()) if routes.values() else 1
        rt_rows = []
        for rt, cnt in sorted(routes.items(), key=lambda x: -x[1]):
            pct = round(cnt / total * 100) if total > 0 else 0
            bar = "|" * int(cnt / max_cnt * 30) if cnt else "-"
            rt_rows.append([
                Paragraph(rt, sCellBold),
                Paragraph(str(cnt), sCellCtr),
                Paragraph(f"{pct}%", sCellCtr),
                Paragraph(bar, style('Normal', fontName='Helvetica', fontSize=8,
                                     textColor=C_SECONDARY, alignment=TA_LEFT)),
            ])
        rt_tbl = Table(
            [[Paragraph(h, sCellBoldW) for h in ["Route", "Complaints", "Share", "Volume Bar"]]] + rt_rows,
            colWidths=[W * 0.18, W * 0.15, W * 0.12, W * 0.55]
        )
        rt_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  C_SECONDARY),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.4, C_BORDER),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (0, 1), (0, -1),  'LEFT'),
            ('ALIGN',         (3, 1), (3, -1),  'LEFT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        for i in range(0, len(rt_rows), 2):
            rt_tbl.setStyle(TableStyle([('BACKGROUND', (0, i+1), (-1, i+1), C_ALT_ROW)]))
        story.append(rt_tbl)
    story.append(Spacer(1, 14))

    # ── AI RECOMMENDATIONS ────────────────────────────────────────────
    story += section_header("AI-Generated Improvement Recommendations")

    rec_header.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#E3EEFF')),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.HexColor('#90CAF9')),
        ('LINERIGHT',     (0, 0), (0, -1),  3,   C_PRIMARY),
    ]))
    story.append(rec_header)
    story.append(Spacer(1, 10))

    for i, sug in enumerate(suggestions, 1):
        clean_sug = sug.lstrip('0123456789.-) ').strip()
        rec_row = Table(
            [[Paragraph(str(i), style('Normal', fontName='Helvetica-Bold', fontSize=11,
                                      textColor=C_WHITE, alignment=TA_CENTER)),
              Paragraph(clean_sug, sSug)]],
            colWidths=[28, W - 28]
        )
        rec_row.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, -1),  C_PRIMARY),
            ('BACKGROUND',    (1, 0), (1, -1),  C_WHITE),
            ('BOX',           (0, 0), (-1, -1), 0.5, C_BORDER),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (1, 0), (1, -1),  10),
            ('RIGHTPADDING',  (1, 0), (1, -1),  10),
        ]))
        story.append(rec_row)
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 14))

    # ── RECENT COMPLAINTS TABLE ───────────────────────────────────────
    story += section_header("Recent Complaints (Latest 15)")
    recent = sorted(records, key=lambda r: r.get('date', ''), reverse=True)[:15]
    if recent:
        rec_rows = []
        for r in recent:
            q   = r.get('quality', '')
            qc  = C_DANGER if q == 'Bad' else (C_SUCCESS if q == 'Excellent' else C_WARNING)
            rec_rows.append([
                Paragraph(r.get('id', ''),     sCell),
                Paragraph(r.get('name', '')[:18], sCell),
                Paragraph(r.get('route', ''),  sCellCtr),
                Paragraph(r.get('emotion', ''), sCellCtr),
                Paragraph(q, style('Normal', fontName='Helvetica-Bold', fontSize=9,
                                   textColor=qc, alignment=TA_CENTER)),
                Paragraph(r.get('status', ''), sCellCtr),
            ])
        rec_tbl = Table(
            [[Paragraph(h, sCellBoldW) for h in ["ID", "Name", "Route", "Emotion", "Quality", "Status"]]] + rec_rows,
            colWidths=[W*0.12, W*0.25, W*0.11, W*0.17, W*0.17, W*0.18]
        )
        rec_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0),  C_TEXT),
            ('TEXTCOLOR',     (0, 0), (-1, 0),  C_WHITE),
            ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('GRID',          (0, 0), (-1, -1), 0.3, C_BORDER),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN',         (0, 1), (1, -1),  'LEFT'),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE',      (0, 1), (-1, -1), 8.5),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        for i in range(0, len(rec_rows), 2):
            rec_tbl.setStyle(TableStyle([('BACKGROUND', (0, i+1), (-1, i+1), C_ALT_ROW)]))
        story.append(rec_tbl)
    story.append(Spacer(1, 16))

    # ── FOOTER ────────────────────────────────────────────────────────
    footer_data = [[
        Paragraph(
            f"Report ID: {report_id}  |  Punjab Mass Transit Authority  |  "
            f"Metro Bus Pakistan  |  Generated: {now.strftime('%d %B %Y, %I:%M %p')}  |  "
            f"This report is system-generated and represents analyzed passenger feedback data.",
            sFooter
        )
    ]]
    footer_tbl = Table(footer_data, colWidths=[W])
    footer_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_LIGHT),
        ('BOX',           (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 14),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
    ]))
    story.append(footer_tbl)

    # ── BUILD PDF ─────────────────────────────────────────────────────
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    filename = f"MetroBus_Report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    response = make_response(pdf_bytes)
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def generate_html_fallback(stats, suggestions, records):
    """Minimal HTML fallback when ReportLab is unavailable."""
    from flask import make_response
    now   = datetime.now().strftime("%d %B %Y, %I:%M %p")
    total = stats.get('total', 0)
    html  = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'>
    <title>Metro Bus Report</title>
    <style>body{{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;padding:20px;color:#1A2634}}
    h1{{color:#0D47A1}}h2{{color:#0D47A1;border-bottom:2px solid #0D47A1;padding-bottom:6px}}
    table{{width:100%;border-collapse:collapse;margin:10px 0}}
    th{{background:#0D47A1;color:white;padding:8px}}td{{padding:8px;border:1px solid #DDE3EA}}
    tr:nth-child(even){{background:#F5F7FA}}ul{{line-height:2}}</style></head><body>
    <h1>Metro Bus Feedback Report</h1>
    <p>Generated: {now} | Total Records: {total}</p>
    <h2>Suggestions</h2><ul>{''.join(f'<li>{s}</li>' for s in suggestions)}</ul>
    </body></html>"""
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html'
    return resp


# ── Keep backward-compat alias ────────────────────────────────────────
def generate_html_report(stats, suggestions, records):
    return generate_pdf_report(stats, suggestions, records)

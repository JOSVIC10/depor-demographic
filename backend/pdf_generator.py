import os
from typing import List, Dict, Optional, Tuple
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.models import Player, Team, Match
from backend.layout_engine import LayoutEngine, PitchSpec, calculate_box_width_and_font

# Widescreen 16:9 slide dimensions in points (13.333 in x 7.5 in = 960 pt x 540 pt)
SLIDE_W = 13.3333 * 72.0 # 960 pt
SLIDE_H = 7.5 * 72.0     # 540 pt

# Exact Color Palette matching reference PDF
C_NAVY = colors.HexColor("#002060")
C_PALE_GREEN = colors.HexColor("#D9EAD3")
C_DARK_GREEN = colors.HexColor("#38761D")
C_PITCH_BG = colors.HexColor("#EBF5EB")
C_PITCH_LINE = colors.HexColor("#2D6A1E")
C_PEACH = colors.HexColor("#FCE5CD")
C_PEACH_BORDER = colors.HexColor("#E2AA6E")
C_GOLD = colors.HexColor("#D4AF37")
C_LIGHT_GRAY = colors.HexColor("#F0F0F0")
C_BORDER_GRAY = colors.HexColor("#CCCCCC")
C_WHITE = colors.white
C_DARK_GRAY = colors.HexColor("#555555")
C_RED_ARROW = colors.HexColor("#CC0000")
C_GREEN_ARROW = colors.HexColor("#00994C")
C_YELLOW_CARD = colors.HexColor("#FFCC00")

def draw_header_footer(c: canvas.Canvas, title_lines: List[str], kpi_text: Optional[str], team: Team):
    """Draws standardized Navy header, dotted KPI box, golden divider, and footer."""
    # 1. Header Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(C_NAVY)
    y_start = SLIDE_H - 32
    for line in title_lines:
        c.drawString(36, y_start, line)
        y_start -= 18

    # 2. Header KPI Box (top right)
    if kpi_text:
        kpi_lines = kpi_text.split("\n")
        box_w = 260
        box_h = 42
        box_x = SLIDE_W - 36 - box_w
        box_y = SLIDE_H - 52
        
        c.saveState()
        c.setStrokeColor(C_NAVY)
        c.setLineWidth(1.5)
        c.setDash(4, 3)
        c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)
        c.restoreState()

        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(C_NAVY)
        line_y = box_y + box_h - 16
        for line in kpi_lines:
            c.drawCentredString(box_x + box_w / 2.0, line_y, line)
            line_y -= 14

    # 3. Footer Divider Line
    c.setStrokeColor(C_GOLD)
    c.setLineWidth(1.5)
    c.line(36, 42, SLIDE_W - 36, 42)

    # 4. Footer Text
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(C_GOLD)
    footer_str = f"{team.club_name}  |  {team.season}  |  MEDICAL & SPORTS SCIENCE DEPARTMENT"
    c.drawCentredString(SLIDE_W / 2.0, 26, footer_str)

def draw_pitch(c: canvas.Canvas, pitch_spec: PitchSpec):
    """Draws perspective trapezoid soccer pitch with lines, boxes, and center circle."""
    # Convert inches to points (origin bottom-left for ReportLab canvas)
    x_c = pitch_spec.x_center * 72.0
    y_t = SLIDE_H - (pitch_spec.y_top * 72.0)
    h = pitch_spec.height * 72.0
    y_b = y_t - h
    wt = pitch_spec.w_top * 72.0
    wb = pitch_spec.w_bottom * 72.0

    # Trapezoid coordinates
    p_tl = (x_c - wt / 2.0, y_t)
    p_tr = (x_c + wt / 2.0, y_t)
    p_br = (x_c + wb / 2.0, y_b)
    p_bl = (x_c - wb / 2.0, y_b)

    # Fill field background
    path = c.beginPath()
    path.moveTo(*p_tl)
    path.lineTo(*p_tr)
    path.lineTo(*p_br)
    path.lineTo(*p_bl)
    path.close()
    
    c.setFillColor(C_PITCH_BG)
    c.setStrokeColor(C_DARK_GREEN)
    c.setLineWidth(2.0)
    c.drawPath(path, fill=1, stroke=1)

    # Pitch markings
    c.setStrokeColor(C_PITCH_LINE)
    c.setLineWidth(1.2)

    # Halfway line
    y_mid = (y_t + y_b) / 2.0
    w_mid = (wt + wb) / 2.0
    c.line(x_c - w_mid / 2.0, y_mid, x_c + w_mid / 2.0, y_mid)

    # Center circle
    c.ellipse(x_c - 45, y_mid - 25, x_c + 45, y_mid + 25)

    # Top goal box / penalty area (attacking)
    c.rect(x_c - (wt * 0.35) / 2.0, y_t - 55, wt * 0.35, 55, fill=0, stroke=1)
    c.rect(x_c - (wt * 0.18) / 2.0, y_t - 22, wt * 0.18, 22, fill=0, stroke=1)

    # Bottom goal box / penalty area (defending)
    c.rect(x_c - (wb * 0.38) / 2.0, y_b, wb * 0.38, 70, fill=0, stroke=1)
    c.rect(x_c - (wb * 0.20) / 2.0, y_b, wb * 0.20, 28, fill=0, stroke=1)

class PDFReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.c = canvas.Canvas(output_path, pagesize=(SLIDE_W, SLIDE_H))
        self.layout_engine = LayoutEngine()
        self.styles = getSampleStyleSheet()

    def generate_cover_slide(self, team: Team, subtitle: str = "DEMOGRAPHIC & MATCH REPORT CADENCE"):
        """Generates premium club cover slide."""
        c = self.c
        
        # Deep Navy Background
        c.setFillColor(C_NAVY)
        c.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)

        # Golden Accent Lines
        c.setStrokeColor(C_GOLD)
        c.setLineWidth(2.5)
        c.line(72, SLIDE_H - 72, SLIDE_W - 72, SLIDE_H - 72)
        c.line(72, 72, SLIDE_W - 72, 72)

        # Title
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(SLIDE_W / 2.0, SLIDE_H / 2.0 + 40, team.club_name.upper())

        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(SLIDE_W / 2.0, SLIDE_H / 2.0 - 5, f"{team.name.upper()} - {team.season}")

        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 14)
        c.drawCentredString(SLIDE_W / 2.0, SLIDE_H / 2.0 - 45, subtitle)

        # Footer
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(SLIDE_W / 2.0, 48, "MEDICAL & SPORTS SCIENCE DEPARTMENT")

        c.showPage()

    def generate_demographic_slide(self, team: Team, players: List[Player]):
        """Generates Slide A: High-fidelity demographic table matching PDF."""
        c = self.c

        # Header and Footer
        title = [f"Analysis | Player", f"{team.name} SQUAD DEMOGRAPHIC"]
        avg_age = round(sum(p.age for p in players) / len(players), 1) if players else 0.0
        kpi = f"TOTAL PLAYERS: {len(players)}\nAVG AGE: {str(avg_age).replace('.', ',')}"
        draw_header_footer(c, title, kpi, team)

        # Age bands & Position categories
        age_bands = [
            ("30+", lambda a: a >= 30),
            ("26-29", lambda a: 26 <= a <= 29),
            ("22-25", lambda a: 22 <= a <= 25),
            ("18-21", lambda a: 18 <= a <= 21),
        ]
        categories = ["Porteros", "Centrales", "Laterales", "Mediocentros", "Int/Extremos", "Delanteros"]

        grid = {b_label: {cat: [] for cat in categories} for b_label, _ in age_bands}
        for p in players:
            cat = p.derived_category if p.derived_category in categories else "Mediocentros"
            for b_label, condition in age_bands:
                if condition(p.age):
                    grid[b_label][cat].append(p)
                    break

        col_widths_in = self.layout_engine.calculate_demographic_column_widths([p.model_dump() for p in players], total_table_width=12.2)
        col_widths_pt = [w * 72.0 for w in col_widths_in]

        # Build table data
        table_data = []
        
        # Header Row
        h_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WHITE, alignment=TA_CENTER))
                 for h in ["BANDA DE EDAD"] + [c_name.upper() for c_name in categories] + ["TOTAL"]]
        table_data.append(h_row)

        col_totals = [0] * len(categories)
        col_ages_sum = [0.0] * len(categories)

        # Band Rows
        for b_label, _ in age_bands:
            row = [Paragraph(f"<b>{b_label}</b>", ParagraphStyle('Band', fontName='Helvetica-Bold', fontSize=10, textColor=C_NAVY, alignment=TA_CENTER))]
            row_total = 0
            for idx, cat in enumerate(categories):
                p_list = grid[b_label][cat]
                row_total += len(p_list)
                col_totals[idx] += len(p_list)
                for p in p_list:
                    col_ages_sum[idx] += p.age

                if p_list:
                    p_txt = "<br/>".join([f"• {p.name} - {p.age}" for p in p_list])
                    cell_p = Paragraph(p_txt, ParagraphStyle('P', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=C_NAVY))
                else:
                    cell_p = Paragraph("-", ParagraphStyle('Dash', fontName='Helvetica', fontSize=8.5, textColor=C_DARK_GRAY, alignment=TA_CENTER))
                row.append(cell_p)

            row.append(Paragraph(f"<b>{row_total}</b>", ParagraphStyle('Tot', fontName='Helvetica-Bold', fontSize=10, textColor=C_NAVY, alignment=TA_CENTER)))
            table_data.append(row)

        # TOTALS Row
        t_row = [Paragraph("<b>TOTALS</b>", ParagraphStyle('TotH', fontName='Helvetica-Bold', fontSize=9, textColor=C_WHITE, alignment=TA_CENTER))]
        grand_total = sum(col_totals)
        for count in col_totals:
            t_row.append(Paragraph(f"<b>{count}</b>", ParagraphStyle('TotV', fontName='Helvetica-Bold', fontSize=10, textColor=C_NAVY, alignment=TA_CENTER)))
        t_row.append(Paragraph(f"<b>{grand_total}</b>", ParagraphStyle('GTot', fontName='Helvetica-Bold', fontSize=10.5, textColor=C_WHITE, alignment=TA_CENTER)))
        table_data.append(t_row)

        # MEDIA EDAD Row
        m_row = [Paragraph("<b>MEDIA EDAD</b>", ParagraphStyle('MedH', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WHITE, alignment=TA_CENTER))]
        for idx in range(len(categories)):
            count = col_totals[idx]
            avg = (col_ages_sum[idx] / count) if count > 0 else 0.0
            avg_str = f"{avg:.1f}".replace('.', ',') if count > 0 else "-"
            m_row.append(Paragraph(f"<b>{avg_str}</b>", ParagraphStyle('MedV', fontName='Helvetica-Bold', fontSize=9, textColor=C_NAVY, alignment=TA_CENTER)))
        all_avg = (sum(col_ages_sum) / grand_total) if grand_total > 0 else 0.0
        all_avg_str = f"{all_avg:.1f}".replace('.', ',') if grand_total > 0 else "-"
        m_row.append(Paragraph(f"<b>{all_avg_str}</b>", ParagraphStyle('GMed', fontName='Helvetica-Bold', fontSize=9.5, textColor=C_WHITE, alignment=TA_CENTER)))
        table_data.append(m_row)

        # Table Styling
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C_NAVY),
            ('BACKGROUND', (0, 1), (0, 4), C_LIGHT_GRAY),
            ('BACKGROUND', (7, 1), (7, 4), C_LIGHT_GRAY),
            ('BACKGROUND', (0, 5), (0, 5), C_NAVY),
            ('BACKGROUND', (1, 5), (6, 5), C_PALE_GREEN),
            ('BACKGROUND', (7, 5), (7, 5), C_NAVY),
            ('BACKGROUND', (0, 6), (0, 6), C_NAVY),
            ('BACKGROUND', (1, 6), (6, 6), C_LIGHT_GRAY),
            ('BACKGROUND', (7, 6), (7, 6), C_NAVY),
            ('GRID', (0, 0), (-1, -1), 0.75, C_BORDER_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ])

        table = Table(table_data, colWidths=col_widths_pt, repeatRows=1)
        table.setStyle(t_style)
        
        # Draw table
        w, h = table.wrap(SLIDE_W - 72, SLIDE_H - 120)
        table.drawOn(c, 36, 55)

        c.showPage()

    def generate_squad_pitch_slide(self, team: Team, players: List[Player]):
        """Generates Slide B: Full squad positioned on tactical pitch in 6 columns."""
        c = self.c

        title = [f"Analysis | Player", f"{team.name}"]
        kpi = f"NUMERO DE JUGADORES: {len(players)} JUGADORES"
        draw_header_footer(c, title, kpi, team)

        pitch_spec = PitchSpec()
        draw_pitch(c, pitch_spec)

        boxes = self.layout_engine.layout_full_squad([p.model_dump() for p in players])

        for box in boxes:
            # Convert box inches to points (origin bottom-left)
            bx = box.x * 72.0
            by = SLIDE_H - ((box.y + box.height) * 72.0)
            bw = box.width * 72.0
            bh = box.height * 72.0

            # Draw rounded player badge
            c.saveState()
            c.setFillColor(C_PALE_GREEN)
            c.setStrokeColor(C_DARK_GREEN)
            c.setLineWidth(1.2)
            c.roundRect(bx, by, bw, bh, 4, fill=1, stroke=1)
            
            c.setFillColor(C_NAVY)
            c.setFont("Helvetica-Bold", box.font_size * 0.85)
            c.drawCentredString(bx + bw / 2.0, by + (bh / 2.0) - 3.0, box.label)
            c.restoreState()

        c.showPage()

    def generate_match_report_slide(self, full_match: Dict):
        """Generates Slide C: Match report with starters, bench, and subs cadence."""
        c = self.c

        match: Match = full_match['match']
        team: Team = full_match['team']
        starters = full_match['starters']
        substitutes = full_match['substitutes']
        subs_events = full_match['substitutions']
        players_map = full_match['players_map']

        title = [f"Analysis | Player", f"{match.title_display}"]
        kpi = f"TOTAL NUMBER OF SUBSTITUTIONS: {len(subs_events)}"
        draw_header_footer(c, title, kpi, team)

        # Center Pitch
        pitch_spec = PitchSpec(x_center=6.4, y_top=1.35, height=5.25, w_top=5.5, w_bottom=7.8)
        draw_pitch(c, pitch_spec)

        # Left Panel: Substitutes (Peach box)
        p_left_x = 36
        p_left_y = 52
        p_left_w = 160
        p_left_h = SLIDE_H - 120

        c.saveState()
        c.setFillColor(C_PEACH)
        c.setStrokeColor(C_PEACH_BORDER)
        c.setLineWidth(1.5)
        c.roundRect(p_left_x, p_left_y, p_left_w, p_left_h, 6, fill=1, stroke=1)

        # Substitutes Header
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(p_left_x + p_left_w / 2.0, p_left_y + p_left_h - 22, "Substitutes")

        subbed_in_map = {se.player_in_id: se for se in subs_events}
        subbed_out_map = {se.player_out_id: se for se in subs_events}

        cur_y = p_left_y + p_left_h - 44
        for sub_entry in substitutes:
            p_obj = players_map.get(sub_entry.player_id)
            p_name = p_obj.name if p_obj else "Suplente"
            has_yellow = getattr(sub_entry, 'has_yellow_card', False)
            has_red = getattr(sub_entry, 'has_red_card', False)
            c_min = getattr(sub_entry, 'card_minute', None)
            card_badge = f" ({c_min}’ 🟥)" if (has_red and c_min) else (" 🟥" if has_red else (f" ({c_min}’ 🟨)" if (has_yellow and c_min) else (" 🟨" if has_yellow else "")))

            if sub_entry.player_id in subbed_in_map:
                ev = subbed_in_map[sub_entry.player_id]
                c.setFillColor(C_GREEN_ARROW)
                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(p_left_x + 10, cur_y, f"▲ {p_name} ({ev.minute}’){card_badge}")
            else:
                c.setFillColor(C_NAVY)
                c.setFont("Helvetica", 8.0)
                c.drawString(p_left_x + 16, cur_y, f"• {p_name}{card_badge}")
            cur_y -= 16
            if cur_y < p_left_y + 15:
                break
        c.restoreState()

        # Starters on Pitch
        starters_dicts = []
        for s in starters:
            sd = s.model_dump()
            if s.player_id in subbed_out_map:
                sd['sub_out_minute'] = subbed_out_map[s.player_id].minute
            starters_dicts.append(sd)

        layout_eng = LayoutEngine(pitch_spec)
        starter_boxes = layout_eng.layout_match_starters(starters_dicts, {k: v.model_dump() for k, v in players_map.items()})

        for box in starter_boxes:
            bx = box.x * 72.0
            by = SLIDE_H - ((box.y + box.height) * 72.0)
            bw = box.width * 72.0
            bh = box.height * 72.0

            c.saveState()
            c.setFillColor(C_PALE_GREEN)
            c.setStrokeColor(C_DARK_GREEN)
            c.setLineWidth(1.3)
            c.roundRect(bx, by, bw, bh, 4, fill=1, stroke=1)

            c.setFillColor(C_NAVY)
            c.setFont("Helvetica-Bold", box.font_size * 0.82)
            c.drawCentredString(bx + bw / 2.0, by + (bh / 2.0) - 3.0, box.label)

            # Red Down Arrow for substituted off starter
            if box.id in subbed_out_map:
                c.setFillColor(C_RED_ARROW)
                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(bx + bw - 11, by + (bh / 2.0) - 3.0, "▼")

            c.restoreState()

        # Right Panel: Match Times & Chronological Substitutions
        r_x = SLIDE_W - 36 - 195
        r_y = SLIDE_H - 100

        c.saveState()
        # Match Time
        c.setFillColor(C_NAVY)
        c.setFont("Helvetica-Bold", 9.0)
        m_time_str = match.match_time or "Match Time: 90:00"
        c.drawString(r_x, r_y, m_time_str)
        r_y -= 14

        # Cadence
        cadence_str = match.substitution_cadence or (f"Substitution Cadence ({subs_events[0].minute}' to {subs_events[-1].minute}')" if subs_events else "Substitution Cadence (-)")
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(r_x, r_y, cadence_str)
        r_y -= 14

        # Total Substitutions header
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(r_x, r_y, f"Total Number of Substitutions: {len(subs_events)}")
        r_y -= 20

        # Substitutions Log
        c.setFont("Helvetica-Bold", 11)
        c.drawString(r_x, r_y, "Substitutions")
        r_y -= 16

        # Group substitutions by minute / event index
        grouped_subs = {}
        for ev in subs_events:
            grouped_subs.setdefault(ev.minute, []).append(ev)

        sub_idx = 1
        for min_val, ev_list in grouped_subs.items():
            c.setFont("Helvetica-Bold", 8.5)
            c.setFillColor(C_NAVY)
            c.drawString(r_x, r_y, f"Substitutions ({sub_idx}): Min {min_val}’")
            r_y -= 13

            for ev in ev_list:
                p_out = players_map.get(ev.player_out_id)
                p_in = players_map.get(ev.player_in_id)
                out_name = p_out.name if p_out else "Out"
                in_name = p_in.name if p_in else "In"

                c.setFont("Helvetica", 8.0)
                c.drawString(r_x + 8, r_y, f"{in_name} (In) /")
                r_y -= 10
                c.drawString(r_x + 8, r_y, f"{out_name} (Out)")
                r_y -= 13
            sub_idx += 1
            r_y -= 4

        # Footnote if present
        if match.notes:
            c.setFont("Helvetica-Oblique", 7.5)
            c.setFillColor(C_DARK_GRAY)
            c.drawString(r_x, 55, f"*{match.notes}")

        c.restoreState()

        c.showPage()

    def save(self):
        self.c.save()

"""
Export engine: generates CSV, XLSX, PDF, DOCX, PNG from tabular data.
All functions accept (headers, rows, title) and return HttpResponse.
"""
import csv
import io
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone


HOSPITAL_NAME = 'JACKSON F. DOE MEMORIAL REGIONAL REFERRAL HOSPITAL'
HOSPITAL_SUBTITLE = 'Hospital Management Information System'


def _safe_str(val):
    if val is None:
        return ''
    if isinstance(val, bool):
        return 'Yes' if val else 'No'
    if isinstance(val, datetime):
        return val.strftime('%d %b %Y %H:%M')
    return str(val)


def _timestamp():
    return timezone.now().strftime('%d %b %Y %H:%M')


def generate_csv(headers, rows, title):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    safe_title = title.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe_str(cell) for cell in row])
    return response


def generate_xlsx(headers, rows, title):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31] if title else 'Export'

    blue_fill = PatternFill(start_color='1E40AF', end_color='1E40AF', fill_type='solid')
    white_font = Font(color='FFFFFF', bold=True, size=11)
    title_font = Font(bold=True, size=16, color='1E3A8A')
    subtitle_font = Font(bold=True, size=11, color='6B7280')
    header_font = Font(bold=True, size=10, color='1E3A8A')
    light_gray = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
    border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=min(len(headers), 8))
    cell = ws.cell(row=1, column=1, value=HOSPITAL_NAME)
    cell.font = title_font
    cell.alignment = Alignment(horizontal='center')

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=min(len(headers), 8))
    cell = ws.cell(row=2, column=1, value=f'{title} — {_timestamp()}')
    cell.font = subtitle_font
    cell.alignment = Alignment(horizontal='center')

    header_row = 4
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header)
        cell.font = white_font
        cell.fill = blue_fill
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = border

    for row_idx, row in enumerate(rows, header_row + 1):
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=_safe_str(val))
            cell.border = border
            cell.alignment = Alignment(wrap_text=True)
            if row_idx % 2 == 0:
                cell.fill = light_gray

    for col_idx in range(1, len(headers) + 1):
        max_len = max(len(str(headers[col_idx - 1])), 12)
        for row_idx in range(header_row + 1, header_row + len(rows) + 2):
            val = ws.cell(row=row_idx, column=col_idx).value
            if val:
                max_len = max(max_len, min(len(str(val)), 50))
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max_len + 2

    ws.print_area = f'A1:{ws.cell(row=1, column=len(headers)).column_letter}{header_row + len(rows) + 1}'
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    safe_title = title.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.xlsx"'
    wb.save(response)
    return response


def generate_pdf(headers, rows, title):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)

    styles = getSampleStyleSheet()
    hospital_style = ParagraphStyle('Hospital', parent=styles['Title'], fontSize=14,
                                     textColor=colors.HexColor('#1E3A8A'), spaceAfter=2)
    title_style = ParagraphStyle('ExportTitle', parent=styles['Heading2'], fontSize=11,
                                  textColor=colors.HexColor('#4B5563'), spaceAfter=2)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7,
                                   textColor=colors.HexColor('#9CA3AF'), spaceBefore=10)

    elements = []
    elements.append(Paragraph(HOSPITAL_NAME, hospital_style))
    elements.append(Paragraph(f'{title} — Generated: {_timestamp()}', title_style))
    elements.append(Spacer(1, 8))

    table_data = [headers]
    for row in rows:
        table_data.append([_safe_str(cell) for cell in row])

    available_width = landscape(A4)[0] - 30*mm
    col_width = available_width / max(len(headers), 1)

    tbl = Table(table_data, colWidths=[col_width]*len(headers), repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(tbl)
    elements.append(Paragraph(f'{HOSPITAL_SUBTITLE} | Data export', footer_style))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    safe_title = title.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.pdf"'
    return response


def generate_docx(headers, rows, title):
    from docx import Document
    from docx.shared import Inches, Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(9)

    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run(HOSPITAL_NAME)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(f'{title} — Generated: {_timestamp()}')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    doc.add_paragraph()

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = str(header)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(8)

    for row_idx, row in enumerate(rows):
        for col_idx, val in enumerate(row):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = _safe_str(val)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8)

    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(f'{HOSPITAL_SUBTITLE} | Data export')
    run.font.size = Pt(7)
    run.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    safe_title = title.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.docx"'
    return response


def generate_png(headers, rows, title):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from PIL import Image

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=15*mm, bottomMargin=10*mm,
                            leftMargin=10*mm, rightMargin=10*mm)

    styles = getSampleStyleSheet()
    hospital_style = ParagraphStyle('Hospital', parent=styles['Title'], fontSize=14,
                                     textColor=colors.HexColor('#1E3A8A'), spaceAfter=2)
    title_style = ParagraphStyle('ExportTitle', parent=styles['Heading2'], fontSize=10,
                                  textColor=colors.HexColor('#4B5563'), spaceAfter=6)

    elements = []
    elements.append(Paragraph(HOSPITAL_NAME, hospital_style))
    elements.append(Paragraph(f'{title} — {_timestamp()}', title_style))

    table_data = [headers]
    for row in rows:
        table_data.append([_safe_str(cell) for cell in row])

    available_width = landscape(A4)[0] - 20*mm
    col_width = available_width / max(len(headers), 1)

    tbl = Table(table_data, colWidths=[col_width]*len(headers), repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(tbl)

    doc.build(elements)
    buffer.seek(0)

    pdf_img = Image.open(buffer)
    pdf_img = pdf_img.convert('RGB')

    png_buffer = io.BytesIO()
    pdf_img.save(png_buffer, format='PNG', quality=95)
    png_buffer.seek(0)

    response = HttpResponse(png_buffer, content_type='image/png')
    safe_title = title.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.png"'
    return response


FORMAT_HANDLERS = {
    'csv': generate_csv,
    'xlsx': generate_xlsx,
    'pdf': generate_pdf,
    'docx': generate_docx,
    'png': generate_png,
}

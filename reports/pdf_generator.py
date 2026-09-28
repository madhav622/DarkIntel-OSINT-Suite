import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(metrics, logs, filename="reports/DarkIntel_Threat_Report.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#00e676'), spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1e222d'), spaceAfter=8)

    story.append(Paragraph("🕵️‍♂️ DarkIntel OSINT Suite - Threat Intelligence Report", title_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Executive Summary Metrics", heading_style))
    summary_data = [
        ["Target Vendors", "PGP Keys", "Crypto Wallets", "GEO Dead-Drops"],
        [str(metrics[0]), str(metrics[1]), str(metrics[2]), str(metrics[3])]
    ]
    t = Table(summary_data, colWidths=[120, 120, 120, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e222d')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#2d313e')),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Recent Scraped Target Logs", heading_style))
    log_data = [["Log ID", "Vendor ID", "Source / Onion URL", "Scraped At"]]
    for log in logs:
        log_data.append([str(log[0]), str(log[1]), str(log[2])[:30], str(log[3])])

    if len(log_data) == 1:
        log_data.append(["N/A", "N/A", "No ingestion logs recorded yet.", "N/A"])

    log_table = Table(log_data, colWidths=[60, 80, 200, 140])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d313e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(log_table)

    doc.build(story)
    return filename

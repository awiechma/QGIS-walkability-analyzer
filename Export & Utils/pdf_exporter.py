# pdf_exporter.py - PDF-Export-Funktionalität

import os
from datetime import datetime
from qgis.core import QgsMessageLog, Qgis

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    QgsMessageLog.logMessage("ReportLab not available - PDF export disabled", level=Qgis.Warning)
    REPORTLAB_AVAILABLE = False

def export_walkability_pdf(analysis_data, output_path):
    """
    Exportiere Walkability-Analyse als PDF
    
    :param analysis_data: Analyse-Ergebnisse
    :param output_path: Pfad für die PDF-Datei
    """
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab ist nicht installiert. Bitte installieren Sie es mit: pip install reportlab")
    
    try:
        # PDF-Dokument erstellen
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles definieren
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Story (Inhalt) zusammenstellen
        story = []
        
        # Header
        story.extend(create_header(analysis_data, title_style, styles))
        
        # Zusammenfassung
        story.extend(create_summary(analysis_data, heading_style, styles))
        
        # Detaillierte Ergebnisse
        story.extend(create_detailed_results(analysis_data, heading_style, styles))
        
        # Service-Details
        story.extend(create_service_details(analysis_data, heading_style, styles))
        
        # Empfehlungen
        story.extend(create_recommendations(analysis_data, heading_style, styles))
        
        # Footer
        story.extend(create_footer(analysis_data, styles))
        
        # PDF generieren
        doc.build(story)
        
        QgsMessageLog.logMessage(f"PDF successfully created: {output_path}", level=Qgis.Info)
        
    except Exception as e:
        QgsMessageLog.logMessage(f"PDF export error: {str(e)}", level=Qgis.Critical)
        raise

def create_header(analysis_data, title_style, styles):
    """Erstelle PDF-Header"""
    
    story = []
    
    # Titel
    story.append(Paragraph("Walkability-Analyse Münster", title_style))
    story.append(Spacer(1, 20))
    
    # Grundinformationen
    location_name = analysis_data.get('location_name', analysis_data.get('district', 'Unbekannt'))
    time_limit = analysis_data['time_limit']
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    info_data = [
        ["Standort:", location_name],
        ["Maximale Gehzeit:", f"{time_limit} Minuten"],
        ["Analyse-Zeitpunkt:", timestamp],
        ["Koordinaten:", f"{analysis_data['coordinates'][1]:.4f}, {analysis_data['coordinates'][0]:.4f}"]
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 20))
    
    return story

def create_summary(analysis_data, heading_style, styles):
    """Erstelle Zusammenfassungsbereich"""
    
    story = []
    score_data = analysis_data['score']
    total_score = score_data['total_score']
    
    # Überschrift
    story.append(Paragraph("🏆 Zusammenfassung", heading_style))
    
    # Score-Box
    if total_score >= 80:
        rating = "Excellent - Sehr gute Walkability"
        color = colors.green
    elif total_score >= 60:
        rating = "Good - Gute Walkability"
        color = colors.orange
    elif total_score >= 40:
        rating = "Fair - Durchschnittliche Walkability"
        color = colors.yellow
    else:
        rating = "Poor - Schlechte Walkability"
        color = colors.red
    
    summary_data = [
        ["Walkability-Score", f"{total_score:.1f}/100"],
        ["Bewertung", rating],
        ["Gefundene Services", str(score_data['total_services'])],
        ["Analysierte Service-Typen", str(len(analysis_data['service_types']))]
    ]
    
    summary_table = Table(summary_data, colWidths=[6*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('BACKGROUND', (0, 1), (-1, 1), color),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    return story

def create_detailed_results(analysis_data, heading_style, styles):
    """Erstelle detaillierte Ergebnisse"""
    
    story = []
    score_data = analysis_data['score']
    
    # Überschrift
    story.append(Paragraph("📊 Detaillierte Ergebnisse", heading_style))
    
    # Service-Scores Tabelle
    service_headers = ["Service-Typ", "Gefunden", "Minimum", "Score", "Gewichtung"]
    service_data = [service_headers]
    
    for service_type, service_score in score_data['service_scores'].items():
        count = service_score['count']
        min_count = service_score['min_count']
        raw_score = service_score['raw_score']
        weight = service_score['weight']
        
        # Status-Symbol
        status = "✅" if count >= min_count else "❌"
        
        row = [
            f"{status} {service_type}",
            str(count),
            str(min_count),
            f"{raw_score:.1f}",
            f"{weight:.2f}"
        ]
        service_data.append(row)
    
    service_table = Table(service_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm, 2*cm])
    service_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    
    story.append(service_table)
    story.append(Spacer(1, 20))
    
    return story

def create_service_details(analysis_data, heading_style, styles):
    """Erstelle Service-Details"""
    
    story = []
    services_data = analysis_data['services']
    
    # Überschrift
    story.append(Paragraph("🏪 Service-Details", heading_style))
    
    for service_type, pois in services_data.items():
        if not pois:
            continue
            
        # Service-Typ Überschrift
        story.append(Paragraph(f"{service_type} ({len(pois)} gefunden):", styles['Heading3']))
        
        # POI-Liste (nur erste 10 zeigen)
        poi_list = []
        for i, poi in enumerate(pois[:10]):
            name = poi.get('name', 'Unbenannt')
            osm_type = poi.get('osm_type', '')
            poi_list.append(f"• {name} ({osm_type})")
        
        if len(pois) > 10:
            poi_list.append(f"... und {len(pois) - 10} weitere")
        
        for poi_text in poi_list:
            story.append(Paragraph(poi_text, styles['Normal']))
        
        story.append(Spacer(1, 12))
    
    return story

def create_recommendations(analysis_data, heading_style, styles):
    """Erstelle Empfehlungen"""
    
    story = []
    score_data = analysis_data['score']
    total_score = score_data['total_score']
    
    # Überschrift
    story.append(Paragraph("💡 Empfehlungen", heading_style))
    
    # Allgemeine Empfehlung
    if total_score >= 80:
        general_rec = "Excellent! Dieser Standort hat eine sehr gute Walkability mit ausgezeichneter Service-Abdeckung."
    elif total_score >= 60:
        general_rec = "Gute Walkability. Der Standort bietet eine solide Service-Abdeckung mit Potential für kleinere Verbesserungen."
    elif total_score >= 40:
        general_rec = "Durchschnittliche Walkability. Zusätzliche Services würden die Fußgängerfreundlichkeit deutlich verbessern."
    else:
        general_rec = "Schlechte Walkability. Eine deutliche Verbesserung der Service-Infrastruktur ist erforderlich."
    
    story.append(Paragraph(general_rec, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Spezifische Empfehlungen
    story.append(Paragraph("Spezifische Verbesserungsvorschläge:", styles['Heading4']))
    
    recommendations = []
    for service_type, service_score in score_data['service_scores'].items():
        count = service_score['count']
        min_count = service_score['min_count']
        
        if count < min_count:
            missing = min_count - count
            recommendations.append(f"• {service_type}: {missing} zusätzliche Einrichtung(en) empfohlen")
        elif count == min_count:
            recommendations.append(f"• {service_type}: Grundversorgung erfüllt, weitere Einrichtungen würden Score verbessern")
    
    if not recommendations:
        recommendations.append("• Alle Service-Mindestanforderungen sind erfüllt")
        recommendations.append("• Zusätzliche Services würden den Score weiter verbessern")
    
    for rec in recommendations:
        story.append(Paragraph(rec, styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    return story

def create_footer(analysis_data, styles):
    """Erstelle PDF-Footer"""
    
    story = []
    
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 12))
    
    footer_text = f"""
    <b>Walkability Analyzer für Münster</b><br/>
    Erstellt mit QGIS Plugin - OpenRouteService & OpenStreetMap<br/>
    Analyse basiert auf Fußgänger-Isochronen und OpenStreetMap POI-Daten<br/>
    <i>Generiert am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}</i>
    """
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story.append(Paragraph(footer_text, footer_style))
    
    return story
import os
import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.units import inch

def generar_pdf_estado_cuenta(cliente_data, cartera_df):
    """
    Genera el estado de cuenta profesional de ALPAPEL SAS directamente en PDF.
    Compatible con Linux/Streamlit Cloud.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- 1. ENCABEZADO (Logo y Título) ---
    logo_path = os.path.join(base_dir, "assets", "logo_formato.jpg")
    
    # Estilo para el título
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor("#00B3B0"), # Turquesa ALPAPEL
        alignment=1, # Centro
        spaceAfter=10
    )

    header_data = []
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.8*inch, height=0.6*inch)
        header_data = [[img, Paragraph("ESTADO DE CUENTA<br/>ALPAPEL SAS", title_style)]]
    else:
        header_data = [["", Paragraph("ESTADO DE CUENTA<br/>ALPAPEL SAS", title_style)]]

    header_table = Table(header_data, colWidths=[2.5*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # --- 2. DATOS DEL CLIENTE ---
    nombre = (cliente_data.get('nombre_cliente') or cliente_data.get('razon_social') or 'CLIENTE').upper()
    nit = str(cliente_data.get('nit_cliente') or 'N/A')
    fecha_emision = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    data_info = [
        [Paragraph(f"<b>CLIENTE:</b> {nombre}", styles['Normal'])],
        [Paragraph(f"<b>NIT/C.C:</b> {nit}", styles['Normal'])],
        [Paragraph(f"<b>FECHA EMISIÓN:</b> {fecha_emision}", styles['Normal'])]
    ]
    info_table = Table(data_info, colWidths=[6.5*inch])
    story.append(info_table)
    story.append(Spacer(1, 20))

    # --- 3. PROCESAR TABLA DE CARTERA ---
    story.append(Paragraph("<b>DETALLE DE DOCUMENTOS</b>", styles['Normal']))
    story.append(Spacer(1, 10))

    # Cabecera de la tabla
    table_data = [['DOCUMENTO', 'EMISIÓN', 'VENCIMIENTO', 'DÍAS MORA', 'SALDO']]
    
    total_mora = 0
    total_cartera = 0

    for _, row in cartera_df.iterrows():
        monto = 0
        for col in ['saldo', 'total_cop']:
            if col in row and pd.notna(row[col]):
                monto = float(row[col])
                break
        
        total_cartera += monto
        dias_mora = int(row.get('dias_vencidos', 0))
        
        # Estilo para días de mora (Rojo si es > 0)
        mora_val = str(dias_mora) if dias_mora > 0 else "0"
        if dias_mora > 0:
            total_mora += monto
            mora_p = Paragraph(f'<font color="red">{mora_val}</font>', styles['Normal'])
        else:
            mora_p = mora_val

        table_data.append([
            str(row.get('documento') or row.get('nro_factura') or 'N/A'),
            str(row.get('fecha_emision', 'N/A')).split(' ')[0],
            str(row.get('fecha_vencimiento', 'N/A')).split(' ')[0],
            mora_p,
            f"${monto:,.0f}"
        ])

    # Crear tabla con ReportLab
    table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 1.3*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#00B3B0")), # Fondo Turquesa
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (3,1), (3,-1), 'CENTER'), # Días mora centro
        ('ALIGN', (4,1), (4,-1), 'RIGHT'),  # Saldo derecha
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(table)

    # --- 4. TOTALES ---
    story.append(Spacer(1, 15))
    totales_style = ParagraphStyle('Total', parent=styles['Normal'], alignment=2, fontSize=11)
    
    story.append(Paragraph(f'<font color="red"><b>TOTAL EN MORA: ${total_mora:,.0f}</b></font>', totales_style))
    story.append(Paragraph(f'<b>TOTAL SALDO CARTERA: ${total_cartera:,.0f}</b>', totales_style))

    # --- 5. NOTA FINAL Y PIE ---
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    
    nota_style = ParagraphStyle('Nota', fontSize=8, textColor=colors.grey, leading=10, alignment=4) # Justify
    nota_texto = (
        "<i>Nota: Este extracto refleja la totalidad de facturas pendientes en nuestro sistema (al día y vencidas). "
        "Si usted ya realizó el pago, por favor envíe su soporte a quien le ha hecho llegar este documento o a los correos: "
        "tesoreria@alpapel.com / coordinador.cartera@alpapel.com / cartera@alpapel.com para su debida legalización.</i>"
    )
    story.append(Paragraph(nota_texto, nota_style))

    # Logo inferior
    logo_inf_path = os.path.join(base_dir, "assets", "logo_inferior.jpg")
    if os.path.exists(logo_inf_path):
        story.append(Spacer(1, 20))
        img_inf = Image(logo_inf_path, width=6*inch, height=0.8*inch)
        story.append(img_inf)

    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
import pandas as pd
from datetime import datetime
import os
import io
import base64
import tempfile
import plotly.io as pio
import plotly.graph_objects as go

# Configuración del motor de imágenes (requiere kaleido instalado: pip install kaleido)
pio.kaleido.scope.default_format = "png"

def generar_reporte_html(df_filtrado, graficas_activas, filtros_aplicados=None):
    """
    Genera un reporte HTML premium con rutas dinámicas, métricas exactas
    y títulos que se ajustan a los filtros aplicados.
    """
    if df_filtrado.empty:
        return None

    # --- 1. LÓGICA DE TÍTULO DINÁMICO ---
    tipo_reporte = "REPORTE GENERAL DE CARTERA"
    detalles_contexto = []

    if filtros_aplicados:
        if filtros_aplicados.get('vendedor') and filtros_aplicados['vendedor'] != "Todos los vendedores":
            detalles_contexto.append(f"Vendedor: {filtros_aplicados['vendedor']}")
        if filtros_aplicados.get('ciudad') and filtros_aplicados['ciudad'] != "Todas las ciudades":
            detalles_contexto.append(f"Ciudad: {filtros_aplicados['ciudad']}")
        if filtros_aplicados.get('dias_min') or filtros_aplicados.get('dias_max'):
            d_min = filtros_aplicados.get('dias_min', 0)
            d_max = filtros_aplicados.get('dias_max', '+')
            detalles_contexto.append(f"Rango Mora: {d_min} a {d_max} días")
        
        if detalles_contexto:
            tipo_reporte = "REPORTE DE CARTERA PARTICULAR"

    texto_filtros = " / ".join(detalles_contexto) if detalles_contexto else "Consolidado Completo de la Compañía"

    # --- 2. RUTA DINÁMICA DEL LOGO (logo_login.png) ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo_login.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    # --- 3. CÁLCULO DE MÉTRICAS (Tal como las pediste) ---
    total_cartera = df_filtrado['total_cop'].sum()
    mora_cartera = df_filtrado[df_filtrado['dias_vencidos'] > 0]['total_cop'].sum()
    porc_mora = (mora_cartera / total_cartera * 100) if total_cartera > 0 else 0
    
    total_clientes = df_filtrado['nit_cliente'].nunique()
    clientes_mora = df_filtrado[df_filtrado['dias_vencidos'] > 0]['nit_cliente'].nunique()
    porc_clientes_mora = (clientes_mora / total_clientes * 100) if total_clientes > 0 else 0

    # --- 4. ESTRUCTURA HTML Y DISEÑO CORPORATIVO ---
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px; background-color: #f1f5f9; color: #1e293b; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 45px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 5px solid #00B3B0; padding-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            
            .context-box {{ margin-top: 20px; margin-bottom: 35px; border-left: 6px solid #cbd5e1; padding-left: 20px; }}
            .main-title {{ font-size: 26px; font-weight: 800; color: #00B3B0; text-transform: uppercase; margin: 0; }}
            .sub-title {{ font-size: 16px; color: #64748b; margin: 5px 0 0 0; font-weight: 600; }}

            .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; border-top: 5px solid #00B3B0; }}
            .metric-title {{ font-size: 13px; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 10px; }}
            .metric-value {{ font-size: 32px; font-weight: 800; color: #0f172a; margin: 0; }}
            .metric-sub {{ font-size: 18px; color: #ef4444; font-weight: 700; margin-top: 5px; }}
            
            .chart-card {{ margin-top: 50px; text-align: center; page-break-inside: avoid; }}
            .chart-card h3 {{ color: #334155; border-left: 6px solid #00B3B0; padding-left: 15px; text-align: left; margin-bottom: 25px; font-size: 20px; }}
            .chart-card img {{ width: 100%; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            
            .footer {{ text-align: center; margin-top: 60px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="data:image/png;base64,{logo_b64}" class="logo">
                <div style="text-align: right;">
                    <p style="margin:0; font-weight: bold; color: #475569;">ALPAPEL S.A.S.</p>
                    <p style="margin:0; font-size: 12px; color: #94a3b8;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>

            <div class="context-box">
                <p class="main-title">{tipo_reporte}</p>
                <p class="sub-title">Filtros aplicados: {texto_filtros}</p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">CARTERA TOTAL ANALIZADA</div>
                    <div class="metric-value">${total_cartera:,.0f}</div>
                    <div class="metric-title" style="margin-top:10px; color: #00B3B0;">TOTAL CLIENTES: {total_clientes}</div>
                </div>
                <div class="metric-card" style="border-top-color: #ef4444;">
                    <div class="metric-title">CARTERA EN MORA</div>
                    <div class="metric-value">${mora_cartera:,.0f}</div>
                    <div class="metric-sub">{porc_mora:.1f}% de la Cartera</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">CLIENTES EN MORA</div>
                    <div class="metric-value">{clientes_mora} Clientes</div>
                    <div class="metric-sub" style="color: #f59e0b;">{porc_clientes_mora:.1f}% del total de clientes</div>
                </div>
            </div>

            <div class="chart-section">
    """

    # --- 5. GENERACIÓN DE GRÁFICAS ---
    archivos_temporales = []
    try:
        for chart_id in graficas_activas:
            fig = obtener_figura_real(chart_id, df_filtrado)
            if fig:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    t_path = tmp.name
                
                fig.update_layout(width=1100, height=550, template="plotly_white")
                pio.write_image(fig, t_path, engine="kaleido")
                archivos_temporales.append(t_path)

                with open(t_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()

                titulo_grafica = GRAFICAS_MAP[chart_id]['titulo']
                html += f"""
                <div class="chart-card">
                    <h3>{titulo_grafica}</h3>
                    <img src="data:image/png;base64,{img_data}">
                </div>
                """
    finally:
        for p in archivos_temporales:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

    html += """
            </div>
            <div class="footer">
                ALPAPEL S.A.S. - Confidencial - Reporte generado automáticamente por CRM Cartera
            </div>
        </div>
    </body>
    </html>
    """
    return html

# --- MAPEO DE FUNCIONES DE GRÁFICAS ---

def obtener_figura_real(chart_id, d):
    if chart_id in GRAFICAS_MAP:
        return GRAFICAS_MAP[chart_id]['func'](d)
    return None

def fig_distribucion_real(d):
    cat = ['Corriente', '1-30', '31-60', '61-90', '+90']
    val = [
        d[d['dias_vencidos'] == 0]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 1) & (d['dias_vencidos'] <= 30)]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 31) & (d['dias_vencidos'] <= 60)]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 61) & (d['dias_vencidos'] <= 90)]['total_cop'].sum(),
        d[d['dias_vencidos'] > 90]['total_cop'].sum()
    ]
    return go.Figure(go.Bar(x=cat, y=val, marker_color='#00B3B0'))

def fig_top_mora_real(d):
    top = d[d['dias_vencidos'] > 0].groupby('razon_social_cliente')['total_cop'].sum().nlargest(10).sort_values(ascending=True)
    return go.Figure(go.Bar(x=top.values, y=top.index, orientation='h', marker_color='#ef4444'))

def fig_vendedores_real(d):
    vend = d.groupby('nombre_vendedor')['total_cop'].sum().nlargest(10)
    return go.Figure(go.Bar(x=vend.index, y=vend.values, marker_color='#64748b'))

def fig_condiciones_real(d):
    cond = d.groupby('condicion_pago')['total_cop'].sum()
    return go.Figure(go.Pie(labels=cond.index, values=cond.values, hole=0.3, marker=dict(colors=['#00B3B0', '#334155', '#94a3b8'])))

# Diccionario Maestro de Gráficas
GRAFICAS_MAP = {
    'chart1': {'titulo': 'Distribución por Estado de Vencimiento', 'func': fig_distribucion_real},
    'chart2': {'titulo': 'Top 10 Clientes con Mayor Deuda en Mora', 'func': fig_top_mora_real},
    'chart3': {'titulo': 'Análisis de Cartera por Vendedor', 'func': fig_vendedores_real},
    'chart4': {'titulo': 'Distribución por Condición de Pago', 'func': fig_condiciones_real},
    'chart5': {'titulo': 'Proyección de Vencimientos', 'func': fig_distribucion_real},
    'chart6': {'titulo': 'Análisis de Concentración 80/20', 'func': fig_top_mora_real},
    'chart7': {'titulo': 'Resumen de Envejecimiento', 'func': fig_condiciones_real},
    'chart8': {'titulo': 'Análisis Geográfico de Cartera', 'func': fig_vendedores_real},
    'chart9': {'titulo': 'Evaluación de Límites de Crédito', 'func': fig_distribucion_real}
}
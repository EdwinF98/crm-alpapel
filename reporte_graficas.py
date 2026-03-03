import pandas as pd
from datetime import datetime
import os
import base64
import plotly.graph_objects as go

def generar_reporte_html(df_filtrado, graficas_activas, filtros_aplicados=None):
    """
    Genera un reporte HTML Interactivo. 
    NO requiere Kaleido ni Google Chrome.
    """
    if df_filtrado.empty:
        return None

    # --- 1. TÍTULO DINÁMICO ---
    tipo_reporte = "REPORTE GENERAL DE CARTERA"
    detalles = []
    if filtros_aplicados:
        v = filtros_aplicados.get('vendedor')
        if v and v not in ["Todos los vendedores", "Todos", "Seleccionar..."]:
            detalles.append(f"Vendedor: {v}")
        c = filtros_aplicados.get('ciudad')
        if c and c not in ["Todas las ciudades", "Todas", "Seleccionar..."]:
            detalles.append(f"Ciudad: {c}")
        if detalles: tipo_reporte = "REPORTE DE CARTERA PARTICULAR"
    
    texto_filtros = " / ".join(detalles) if detalles else "Consolidado Completo de la Compañía"

    # --- 2. LOGO DINÁMICO ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo_login.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    # --- 3. MÉTRICAS ---
    total_cartera = df_filtrado['total_cop'].sum()
    mora_cartera = df_filtrado[df_filtrado['dias_vencidos'] > 0]['total_cop'].sum()
    porc_mora = (mora_cartera / total_cartera * 100) if total_cartera > 0 else 0
    total_clientes = df_filtrado['nit_cliente'].nunique()
    clientes_mora = df_filtrado[df_filtrado['dias_vencidos'] > 0]['nit_cliente'].nunique()
    porc_cl_mora = (clientes_mora / total_clientes * 100) if total_clientes > 0 else 0

    # --- 4. ESTRUCTURA HTML (Incluye el motor de Plotly) ---
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 40px; background-color: #f1f5f9; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 5px solid #00B3B0; padding-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            .context-box {{ margin-top: 20px; margin-bottom: 35px; border-left: 6px solid #cbd5e1; padding-left: 20px; }}
            .main-title {{ font-size: 26px; font-weight: 800; color: #00B3B0; text-transform: uppercase; margin: 0; }}
            .sub-title {{ font-size: 16px; color: #64748b; margin: 5px 0 0 0; font-weight: 600; }}
            .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; border-top: 5px solid #00B3B0; }}
            .metric-title {{ font-size: 13px; text-transform: uppercase; color: #64748b; font-weight: 700; }}
            .metric-value {{ font-size: 32px; font-weight: 800; color: #0f172a; margin: 5px 0; }}
            .metric-sub {{ font-size: 18px; color: #ef4444; font-weight: 700; }}
            .chart-card {{ margin-top: 50px; background: #fff; padding: 20px; border: 1px solid #f1f5f9; border-radius: 10px; }}
            .chart-card h3 {{ color: #334155; border-left: 6px solid #00B3B0; padding-left: 15px; text-align: left; margin-bottom: 25px; }}
            .footer {{ text-align: center; margin-top: 60px; font-size: 11px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="data:image/png;base64,{logo_b64}" class="logo">
                <div style="text-align: right;">
                    <p style="margin:0; font-weight: bold; color: #475569;">ALPAPEL S.A.S.</p>
                    <p style="margin:0; font-size: 12px;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>

            <div class="context-box">
                <p class="main-title">{tipo_reporte}</p>
                <p class="sub-title">Filtros: {texto_filtros}</p>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">CARTERA TOTAL</div>
                    <div class="metric-value">${total_cartera:,.0f}</div>
                    <div class="metric-title" style="color: #00B3B0;">TOTAL CLIENTES: {total_clientes}</div>
                </div>
                <div class="metric-card" style="border-top-color: #ef4444;">
                    <div class="metric-title">CARTERA EN MORA</div>
                    <div class="metric-value">${mora_cartera:,.0f}</div>
                    <div class="metric-sub">{porc_mora:.1f}% del Total</div>
                </div>
            </div>

            <div class="chart-section">
    """

    # --- 5. INSERTAR GRÁFICAS INTERACTIVAS ---
    for chart_id in graficas_activas:
        fig = obtener_figura_real(chart_id, df_filtrado)
        if fig:
            fig.update_layout(template="plotly_white", autosize=True)
            # Convertimos la gráfica directamente a un bloque HTML (DIV)
            chart_html = fig.to_html(full_html=False, include_plotlyjs=False)
            
            titulo = GRAFICAS_MAP.get(chart_id, {}).get('titulo', 'Gráfica de Análisis')
            html += f"""
            <div class="chart-card">
                <h3>{titulo}</h3>
                {chart_html}
            </div>
            """

    html += """
            </div>
            <div class="footer">ALPAPEL S.A.S. - Confidencial</div>
        </div>
    </body>
    </html>
    """
    return html

# --- FUNCIONES DE GRÁFICAS (Iguales, pero sin necesidad de kaleido) ---

def fig_dist(d):
    cat = ['Corriente', '1-30', '31-60', '61-90', '+90']
    val = [d[d['dias_vencidos'] == 0]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 1) & (d['dias_vencidos'] <= 30)]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 31) & (d['dias_vencidos'] <= 60)]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 61) & (d['dias_vencidos'] <= 90)]['total_cop'].sum(),
           d[d['dias_vencidos'] > 90]['total_cop'].sum()]
    return go.Figure(go.Bar(x=cat, y=val, marker_color='#00B3B0'))

def fig_top(d):
    top = d[d['dias_vencidos'] > 0].groupby('razon_social_cliente')['total_cop'].sum().nlargest(10).sort_values(ascending=True)
    return go.Figure(go.Bar(x=top.values, y=top.index, orientation='h', marker_color='#ef4444'))

def fig_vend(d):
    vend = d.groupby('nombre_vendedor')['total_cop'].sum().nlargest(10)
    return go.Figure(go.Bar(x=vend.index, y=vend.values, marker_color='#64748b'))

def fig_cond(d):
    cond = d.groupby('condicion_pago')['total_cop'].sum()
    return go.Figure(go.Pie(labels=cond.index, values=cond.values, hole=0.3, marker=dict(colors=['#00B3B0', '#334155', '#94a3b8'])))

GRAFICAS_MAP = {
    'chart1': {'titulo': 'Distribución por Vencimiento', 'func': fig_dist},
    'chart2': {'titulo': 'Top 10 Clientes Mayor Mora', 'func': fig_top},
    'chart3': {'titulo': 'Cartera por Vendedor', 'func': fig_vend},
    'chart4': {'titulo': 'Condiciones de Pago', 'func': fig_cond},
    'chart5': {'titulo': 'Proyección de Vencimientos', 'func': fig_dist},
    'chart6': {'titulo': 'Análisis 80/20', 'func': fig_top},
    'chart7': {'titulo': 'Envejecimiento', 'func': fig_cond},
    'chart8': {'titulo': 'Distribución Geográfica', 'func': fig_vend},
    'chart9': {'titulo': 'Límites de Crédito', 'func': fig_dist}
}

def obtener_figura_real(chart_id, d):
    if chart_id in GRAFICAS_MAP: return GRAFICAS_MAP[chart_id]['func'](d)
    return None
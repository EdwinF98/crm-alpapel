import pandas as pd
from datetime import datetime
import os
import base64
import plotly.graph_objects as go
import plotly.express as px

def generar_reporte_html(df_filtrado, graficas_activas, filtros_aplicados=None):
    """
    Genera el reporte ejecutivo definitivo para ALPAPEL S.A.S.
    Combina interactividad HTML con lógica financiera profunda.
    """
    if df_filtrado.empty:
        return None

    # --- 1. LÓGICA DE TÍTULO DINÁMICO ---
    tipo_reporte = "REPORTE GENERAL DE CARTERA"
    detalles = []
    if filtros_aplicados:
        v = filtros_aplicados.get('vendedor')
        if v and v not in ["Todos los vendedores", "Todos"]: detalles.append(f"Vendedor: {v}")
        c = filtros_aplicados.get('ciudad')
        if c and c not in ["Todas las ciudades", "Todas"]: detalles.append(f"Ciudad: {c}")
        if detalles: tipo_reporte = "REPORTE DE CARTERA PARTICULAR"
    
    texto_filtros = " / ".join(detalles) if detalles else "Consolidado Completo de la Compañía"

    # --- 2. LOGO DINÁMICO ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo_login.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    # --- 3. CÁLCULO DE MÉTRICAS EJECUTIVAS ---
    total_cartera = df_filtrado['total_cop'].sum()
    mora_cartera = df_filtrado[df_filtrado['dias_vencidos'] > 0]['total_cop'].sum()
    porc_mora = (mora_cartera / total_cartera * 100) if total_cartera > 0 else 0
    total_clientes = df_filtrado['nit_cliente'].nunique()
    clientes_mora = df_filtrado[df_filtrado['dias_vencidos'] > 0]['nit_cliente'].nunique()
    porc_cl_mora = (clientes_mora / total_clientes * 100) if total_clientes > 0 else 0

    # --- 4. ESTRUCTURA HTML ---
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 40px; background-color: #f1f5f9; color: #1e293b; }}
            .container {{ max-width: 1100px; margin: auto; background: white; padding: 45px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 5px solid #00B3B0; padding-bottom: 20px; }}
            .logo {{ max-height: 80px; }}
            .context-box {{ margin-top: 25px; margin-bottom: 35px; border-left: 6px solid #cbd5e1; padding-left: 20px; }}
            .main-title {{ font-size: 26px; font-weight: 800; color: #00B3B0; text-transform: uppercase; margin: 0; }}
            .sub-title {{ font-size: 16px; color: #64748b; margin: 5px 0 0 0; font-weight: 600; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: #ffffff; border: 1px solid #e2e8f0; padding: 25px; border-radius: 12px; border-top: 5px solid #00B3B0; }}
            .metric-title {{ font-size: 13px; text-transform: uppercase; color: #64748b; font-weight: 700; }}
            .metric-value {{ font-size: 32px; font-weight: 800; color: #0f172a; margin: 5px 0; }}
            .metric-sub {{ font-size: 18px; color: #ef4444; font-weight: 700; }}
            .chart-card {{ margin-top: 50px; page-break-inside: avoid; background: #fff; padding: 20px; border: 1px solid #f1f5f9; border-radius: 10px; }}
            .chart-card h3 {{ color: #334155; border-left: 6px solid #00B3B0; padding-left: 15px; text-align: left; margin-bottom: 25px; font-size: 20px; }}
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
                <p class="sub-title">Contexto de filtros: {texto_filtros}</p>
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
                    <div class="metric-sub">{porc_mora:.1f}% de la Cartera Actual</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">CLIENTES EN MORA</div>
                    <div class="metric-value">{clientes_mora} Clientes</div>
                    <div class="metric-sub" style="color: #f59e0b;">{porc_cl_mora:.1f}% del total filtrado</div>
                </div>
            </div>

            <div class="chart-section">
    """

    # --- 5. GENERACIÓN DE GRÁFICAS CON LÓGICA PROFUNDA ---
    for chart_id in graficas_activas:
        fig = obtener_figura_inteligente(chart_id, df_filtrado)
        if fig:
            fig.update_layout(template="plotly_white", autosize=True, font=dict(family="Segoe UI"))
            chart_html = fig.to_html(full_html=False, include_plotlyjs=False)
            titulo = GRAFICAS_MAP[chart_id]['titulo']
            html += f"""<div class="chart-card"><h3>{titulo}</h3>{chart_html}</div>"""

    html += """
            </div>
            <div class="footer">ALPAPEL S.A.S. - Confidencial - Reporte generado automáticamente por CRM Cartera</div>
        </div>
    </body>
    </html>
    """
    return html

# --- 6. LÓGICA MATEMÁTICA DE LAS GRÁFICAS (Espejo del Módulo de Análisis) ---

def fig_distribucion_maestra(d):
    """Calcula los tramos de edad exactos"""
    cat = ['Corriente', '1-30', '31-60', '61-90', '91-120', '+120']
    val = [
        d[d['dias_vencidos'] <= 0]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 1) & (d['dias_vencidos'] <= 30)]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 31) & (d['dias_vencidos'] <= 60)]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 61) & (d['dias_vencidos'] <= 90)]['total_cop'].sum(),
        d[(d['dias_vencidos'] >= 91) & (d['dias_vencidos'] <= 120)]['total_cop'].sum(),
        d[d['dias_vencidos'] > 120]['total_cop'].sum()
    ]
    fig = go.Figure(go.Bar(x=cat, y=val, marker_color='#00B3B0', text=[f"${v:,.0f}" for v in val], textposition='auto'))
    return fig

def fig_top_mora_maestra(d):
    """NIT + Razón Social para claridad gerencial"""
    mora = d[d['dias_vencidos'] > 0].copy()
    mora['cliente_label'] = mora['nit_cliente'] + " - " + mora['razon_social_cliente']
    top = mora.groupby('cliente_label')['total_cop'].sum().nlargest(10).sort_values(ascending=True)
    return go.Figure(go.Bar(x=top.values, y=top.index, orientation='h', marker_color='#ef4444'))

def fig_pareto_maestra(d):
    """Análisis 80/20 real: ¿Qué clientes representan la mayor deuda?"""
    df_p = d.groupby('razon_social_cliente')['total_cop'].sum().sort_values(ascending=False).reset_index()
    df_p['cum_sum'] = df_p['total_cop'].cumsum()
    df_p['cum_perc'] = 100 * df_p['cum_sum'] / df_p['total_cop'].sum()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_p['razon_social_cliente'].head(15), y=df_p['total_cop'].head(15), name="Deuda", marker_color='#00B3B0'))
    fig.add_trace(go.Scatter(x=df_p['razon_social_cliente'].head(15), y=df_p['cum_perc'].head(15), name="% Acumulado", yaxis="y2", line=dict(color="#ef4444")))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right', range=[0, 105]))
    return fig

def fig_vendedores_maestra(d):
    vend = d.groupby('nombre_vendedor')['total_cop'].sum().nlargest(12).sort_values(ascending=True)
    return go.Figure(go.Bar(x=vend.values, y=vend.index, orientation='h', marker_color='#64748b'))

def fig_condiciones_maestra(d):
    cond = d.groupby('condicion_pago')['total_cop'].sum().nlargest(5)
    return go.Figure(go.Pie(labels=cond.index, values=cond.values, hole=0.4, marker=dict(colors=['#00B3B0', '#334155', '#94a3b8', '#cbd5e1'])))

def fig_evolucion_maestra(d):
    """Proyección de recaudos por mes de vencimiento"""
    d['mes_vencimiento'] = pd.to_datetime(d['fecha_vencimiento']).dt.strftime('%Y-%m')
    evol = d.groupby('mes_vencimiento')['total_cop'].sum().sort_index()
    return go.Figure(go.Scatter(x=evol.index, y=evol.values, mode='lines+markers', fill='tozeroy', line=dict(color='#00B3B0')))

# --- DICCIONARIO MAESTRO ---
GRAFICAS_MAP = {
    'chart1': {'titulo': 'Análisis por Tramos de Vencimiento', 'func': fig_distribucion_maestra},
    'chart2': {'titulo': 'Top 10 Clientes Mayor Mora', 'func': fig_top_mora_maestra},
    'chart3': {'titulo': 'Desempeño de Cartera por Vendedor', 'func': fig_vendedores_maestra},
    'chart4': {'titulo': 'Distribución por Condición de Pago', 'func': fig_condiciones_maestra},
    'chart5': {'titulo': 'Proyección de Flujo de Recaudo', 'func': fig_evolucion_maestra},
    'chart6': {'titulo': 'Análisis de Concentración (Pareto)', 'func': fig_pareto_maestra},
    'chart7': {'titulo': 'Envejecimiento Detallado', 'func': fig_distribucion_maestra},
    'chart8': {'titulo': 'Ubicación Geográfica', 'func': fig_vendedores_maestra},
    'chart9': {'titulo': 'Exposición de Riesgo', 'func': fig_condiciones_maestra}
}

def obtener_figura_inteligente(chart_id, d):
    if chart_id in GRAFICAS_MAP: return GRAFICAS_MAP[chart_id]['func'](d)
    return None
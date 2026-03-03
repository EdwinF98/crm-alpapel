import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import base64

def generar_reporte_html(df_filtrado, graficas_activas, filtros_aplicados=None):
    """Genera el reporte ejecutivo con la lógica exacta del dashboard de ALPAPEL"""
    if df_filtrado.empty:
        return None

    # --- 1. TÍTULO DINÁMICO ---
    tipo_reporte = "REPORTE GENERAL DE CARTERA"
    detalles = []
    if filtros_aplicados:
        v = filtros_aplicados.get('vendedor')
        if v and v not in ["Todos los vendedores", "Todos"]: detalles.append(f"Vendedor: {v}")
        c = filtros_aplicados.get('ciudad')
        if c and c not in ["Todas las ciudades", "Todas"]: detalles.append(f"Ciudad: {c}")
        cd = filtros_aplicados.get('condicion')
        if cd and cd not in ["Todas las condiciones"]: detalles.append(f"Condición: {cd}")
        d = filtros_aplicados.get('dias')
        if d and d not in ["Todos los días"]: detalles.append(f"Tramo: {d}")
        
        if detalles: tipo_reporte = "REPORTE DE CARTERA PARTICULAR"
    
    texto_filtros = " / ".join(detalles) if detalles else "Consolidado Completo de la Compañía"

    # --- 2. LOGO ---
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

    # --- 4. HTML HEADER ---
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; background-color: #f1f5f9; color: #1e293b; }}
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
            .chart-card {{ margin-top: 50px; background: #fff; padding: 20px; border: 1px solid #f1f5f9; border-radius: 10px; page-break-inside: avoid; }}
            .chart-card h3 {{ color: #334155; border-left: 6px solid #00B3B0; padding-left: 15px; text-align: left; margin-bottom: 25px; font-size: 20px; }}
            .footer {{ text-align: center; margin-top: 60px; font-size: 11px; color: #94a3b8; border-top: 1px solid #eee; padding-top: 20px; }}
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
                    <div class="metric-title">CARTERA TOTAL ANALIZADA</div>
                    <div class="metric-value">${total_cartera:,.0f}</div>
                    <div class="metric-title" style="color: #00B3B0; margin-top:10px;">CLIENTES: {total_clientes}</div>
                </div>
                <div class="metric-card" style="border-top-color: #ef4444;">
                    <div class="metric-title">CARTERA EN MORA</div>
                    <div class="metric-value">${mora_cartera:,.0f}</div>
                    <div class="metric-sub">{porc_mora:.1f}% de la Cartera</div>
                </div>
            </div>
    """

    # --- 5. GENERACIÓN DE GRÁFICAS (CON TU LÓGICA EXACTA) ---
    mapeo_nombres = {
        'chart1': 'Distribución por Estado', 'chart2': 'Top 10 Clientes Mora',
        'chart3': 'Cartera por Vendedor', 'chart4': 'Condiciones de Pago',
        'chart5': 'Evolución + Proyección', 'chart6': 'Concentración 20/80',
        'chart7': 'Envejecimiento Detallado', 'chart8': 'Análisis Geográfico',
        'chart9': 'Proyección por Crédito'
    }

    for chart_id in graficas_activas:
        fig = None
        if chart_id == 'chart1': fig = fig_chart1(df_filtrado)
        elif chart_id == 'chart2': fig = fig_chart2(df_filtrado)
        elif chart_id == 'chart3': fig = fig_chart3(df_filtrado)
        elif chart_id == 'chart4': fig = fig_chart4(df_filtrado)
        elif chart_id == 'chart5': fig = fig_chart5(df_filtrado)
        elif chart_id == 'chart6': fig = fig_chart6(df_filtrado)
        elif chart_id == 'chart7': fig = fig_chart7(df_filtrado)
        elif chart_id == 'chart8': fig = fig_chart8(df_filtrado)
        elif chart_id == 'chart9': fig = fig_chart9(df_filtrado)

        if fig:
            fig.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            chart_html = fig.to_html(full_html=False, include_plotlyjs=False)
            html += f"""<div class="chart-card"><h3>{mapeo_nombres[chart_id]}</h3>{chart_html}</div>"""

    html += """<div class="footer">ALPAPEL S.A.S. - Confidencial</div></div></body></html>"""
    return html

# --- BLOQUE DE FUNCIONES MATEMÁTICAS (Sincronizadas con tu módulo) ---

def fig_chart1(d):
    cat = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
    val = [d[d['dias_vencidos'] == 0]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 1) & (d['dias_vencidos'] <= 30)]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 31) & (d['dias_vencidos'] <= 60)]['total_cop'].sum(),
           d[(d['dias_vencidos'] >= 61) & (d['dias_vencidos'] <= 90)]['total_cop'].sum(),
           d[d['dias_vencidos'] > 90]['total_cop'].sum()]
    fig = go.Figure(go.Bar(x=cat, y=val, marker_color='#00B3B0'))
    fig.update_yaxes(tickprefix="$", tickformat=".0s")
    return fig

def fig_chart2(d):
    top = d[d['dias_vencidos'] > 0].groupby('razon_social_cliente')['total_cop'].sum().nlargest(10).iloc[::-1]
    return go.Figure(go.Bar(y=top.index, x=top.values, orientation='h', marker_color='#ef4444'))

def fig_chart3(d):
    d2 = d.copy()
    d2['cond_display'] = d2['condicion_pago'].apply(lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x))
    piv = d2.groupby(['nombre_vendedor', 'cond_display'])['total_cop'].sum().unstack().fillna(0)
    piv = piv.loc[piv.sum(axis=1).sort_values(ascending=False).index].head(10)
    fig = go.Figure()
    for col in piv.columns:
        fig.add_trace(go.Bar(name=col, x=piv.index, y=piv[col]))
    fig.update_layout(barmode='stack')
    return fig

def fig_chart4(d):
    d2 = d.copy()
    d2['cond_display'] = d2['condicion_pago'].apply(lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x))
    dist = d2.groupby('cond_display')['total_cop'].sum().sort_values(ascending=True)
    return go.Figure(go.Bar(y=dist.index, x=dist.values, orientation='h', marker_color='#00B3B0'))

def fig_chart5(d):
    # Simplificado para reporte pero basado en fechas reales
    d['mes'] = pd.to_datetime(d['fecha_vencimiento']).dt.strftime('%Y-%m')
    evol = d.groupby('mes')['total_cop'].sum().sort_index()
    return go.Figure(go.Scatter(x=evol.index, y=evol.values, mode='lines+markers', fill='tozeroy', line=dict(color='#00B3B0')))

def fig_chart6(d):
    c_pc = d.groupby('razon_social_cliente')['total_cop'].sum().sort_values(ascending=False)
    total = c_pc.sum()
    acum = c_pc.cumsum()
    c20 = len(acum[acum <= total * 0.2])
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "bar"}]])
    fig.add_trace(go.Bar(y=c_pc.head(10).index, x=c_pc.head(10).values, orientation='h'), row=1, col=1)
    fig.add_trace(go.Bar(x=['Top Clientes', 'Resto'], y=[acum.iloc[c20] if c20 < len(acum) else total, total - (acum.iloc[c20] if c20 < len(acum) else total)]), row=1, col=2)
    return fig

def fig_chart7(d):
    rangos = {'Corriente': (0, 0), '1-30': (1, 30), '31-60': (31, 60), '+60': (61, 9999)}
    res = {k: d[(d['dias_vencidos'] >= v[0]) & (d['dias_vencidos'] <= v[1])]['total_cop'].sum() for k, v in rangos.items()}
    return go.Figure(go.Pie(labels=list(res.keys()), values=list(res.values()), hole=0.3))

def fig_chart8(d):
    # Asume que ya viene con ciudad si se filtró, sino usa genérico
    if 'ciudad' in d.columns:
        geo = d.groupby('ciudad')['total_cop'].sum().nlargest(10).sort_values()
        return go.Figure(go.Bar(y=geo.index, x=geo.values, orientation='h', marker_color='#3b82f6'))
    return fig_chart1(d)

def fig_chart9(d):
    # Lógica de 4 rangos de vencimiento futuro
    hoy = datetime.now().date()
    d['fv'] = pd.to_datetime(d['fecha_vencimiento']).dt.date
    vencido = d[d['fv'] < hoy]['total_cop'].sum()
    m1 = d[(d['fv'] >= hoy) & (d['fv'] <= hoy + timedelta(30))]['total_cop'].sum()
    m2 = d[(d['fv'] > hoy + timedelta(30)) & (d['fv'] <= hoy + timedelta(60))]['total_cop'].sum()
    m3 = d[d['fv'] > hoy + timedelta(60)]['total_cop'].sum()
    return go.Figure(go.Bar(x=['Vencido', '0-30 días', '31-60 días', '+60 días'], y=[vencido, m1, m2, m3], marker_color='#f59e0b'))
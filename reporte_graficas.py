# reporte_graficas.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import base64

# ------------------------------------------------------------
# FUNCIONES DE CREACIÓN DE GRÁFICAS (IDÉNTICAS AL DASHBOARD)
# ------------------------------------------------------------

def _grafica_distribucion_estado(df):
    """Gráfica 1: Distribución por Estado de Cartera"""
    if df.empty:
        return None

    categorias_estado = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
    valores_estado = [
        df[df['dias_vencidos'] == 0]['total_cop'].sum(),
        df[(df['dias_vencidos'] >= 1) & (df['dias_vencidos'] <= 30)]['total_cop'].sum(),
        df[(df['dias_vencidos'] >= 31) & (df['dias_vencidos'] <= 60)]['total_cop'].sum(),
        df[(df['dias_vencidos'] >= 61) & (df['dias_vencidos'] <= 90)]['total_cop'].sum(),
        df[df['dias_vencidos'] > 90]['total_cop'].sum()
    ]

    if not any(v > 0 for v in valores_estado):
        return None

    colors = ['#10b981', '#f59e0b', '#f97316', '#dc2626', '#991b1b']
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categorias_estado,
        y=valores_estado,
        marker_color=colors,
        text=[f'${v/1e6:.1f}M' if v >= 1e6 else f'${v/1e3:.0f}K' for v in valores_estado],
        textposition='auto',
    ))
    fig.update_layout(
        title="Distribución por Estado de Cartera",
        xaxis_title="Estado de Cartera",
        yaxis_title="Valor COP",
        template="plotly_dark",
        height=500,
        showlegend=False
    )
    fig.update_yaxes(tickprefix='$', tickformat='.0s')
    return fig


def _grafica_top_clientes_mora(df):
    """Gráfica 2: Top 10 Clientes con Mayor Mora"""
    df_mora = df[df['dias_vencidos'] > 0]
    if df_mora.empty:
        return None

    top_clientes = df_mora.groupby('razon_social_cliente').agg({
        'total_cop': 'sum',
        'dias_vencidos': 'max'
    }).nlargest(10, 'total_cop').iloc[::-1]  # invertir para gráfica horizontal

    if top_clientes.empty:
        return None

    clientes_nombres = [nombre[:20] + '...' if len(nombre) > 20 else nombre 
                        for nombre in top_clientes.index]
    valores = top_clientes['total_cop'].values

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=clientes_nombres,
        x=valores,
        orientation='h',
        marker_color='#ef4444',
        text=[f'${v/1e6:.1f}M' for v in valores],
        textposition='auto',
    ))
    fig.update_layout(
        title="Top 10 Clientes con Mayor Mora",
        xaxis_title="Valor en Mora (COP)",
        yaxis_title="Cliente",
        template="plotly_dark",
        height=500
    )
    fig.update_xaxes(tickprefix='$', tickformat='.0s')
    return fig

def _grafica_condiciones_pago(df):
    """Gráfica 4: Distribución por Condición de Pago"""
    if df.empty:
        return None

    df_mod = df.copy()
    df_mod['condicion_display'] = df_mod['condicion_pago'].apply(
        lambda x: 'CONTADO' if str(x).upper() in ['CO1', 'CON'] else str(x)
    )

    distribucion = df_mod.groupby('condicion_display')['total_cop'].sum().sort_values(ascending=False)

    if distribucion.empty:
        return None

    distribucion = distribucion.iloc[::-1]  # invertir para gráfica horizontal

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=distribucion.index,
        x=distribucion.values,
        orientation='h',
        marker_color='#00B3B0',
        text=[f'${v/1e6:.1f}M' for v in distribucion.values],
        textposition='auto',
    ))
    fig.update_layout(
        title="Distribución por Condición de Pago",
        xaxis_title="Valor COP",
        yaxis_title="Condición de Pago",
        template="plotly_dark",
        height=500
    )
    fig.update_xaxes(tickprefix='$', tickformat='.0s')
    return fig


def _grafica_evolucion_proyeccion(df):
    """Gráfica 5: Evolución Histórica + Proyección (12M + 4M)"""
    if df.empty:
        return None

    # Datos históricos (últimos 12 meses)
    df_hist = df.copy()
    df_hist['fecha_vencimiento'] = pd.to_datetime(df_hist['fecha_vencimiento'], errors='coerce')
    if df_hist.empty:
        return None

    fecha_max = df_hist['fecha_vencimiento'].max()
    fecha_limite = fecha_max - timedelta(days=365)
    df_hist = df_hist[df_hist['fecha_vencimiento'] >= fecha_limite]

    # Agrupar por mes para histórico
    historico = []
    if not df_hist.empty:
        df_hist['mes'] = df_hist['fecha_vencimiento'].dt.strftime('%Y-%m')
        agrupado = df_hist.groupby('mes')['total_cop'].sum().reset_index()
        agrupado = agrupado.sort_values('mes')
        for _, row in agrupado.iterrows():
            historico.append({'mes': row['mes'], 'cartera': row['total_cop']})

    # Proyección futura (próximos 4 meses)
    hoy = datetime.now().date()
    df_fut = df.copy()
    df_fut['fecha_vencimiento'] = pd.to_datetime(df_fut['fecha_vencimiento'], errors='coerce')
    df_fut = df_fut[df_fut['fecha_vencimiento'] >= pd.to_datetime(hoy)]

    proyeccion = []
    for i in range(4):
        mes_futuro = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        mes_nombre = mes_futuro.strftime('%Y-%m')
        mes_display = mes_futuro.strftime('%b %Y')
        inicio_mes = mes_futuro
        fin_mes = (mes_futuro + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        df_mes = df_fut[
            (df_fut['fecha_vencimiento'] >= pd.to_datetime(inicio_mes)) &
            (df_fut['fecha_vencimiento'] <= pd.to_datetime(fin_mes))
        ]
        total_mes = df_mes['total_cop'].sum()
        if total_mes > 0:
            proyeccion.append({'mes': mes_nombre, 'display': mes_display, 'cartera': total_mes})

    # Combinar datos
    meses = []
    valores = []
    es_proy = []
    display_meses = []

    for item in historico:
        meses.append(item['mes'])
        display_meses.append(datetime.strptime(item['mes'], '%Y-%m').strftime('%b %Y'))
        valores.append(item['cartera'])
        es_proy.append(False)

    for item in proyeccion:
        meses.append(item['mes'])
        display_meses.append(item['display'])
        valores.append(item['cartera'])
        es_proy.append(True)

    if not meses:
        return None

    # Separar histórico y proyección
    meses_hist = [display_meses[i] for i in range(len(display_meses)) if not es_proy[i]]
    valores_hist = [valores[i] for i in range(len(valores)) if not es_proy[i]]
    meses_proy = [display_meses[i] for i in range(len(display_meses)) if es_proy[i]]
    valores_proy = [valores[i] for i in range(len(valores)) if es_proy[i]]

    fig = make_subplots(rows=2, cols=1, subplot_titles=('Cartera (Millones COP)', 'Clientes (no disponible)'),
                        vertical_spacing=0.1)

    # Gráfica de cartera
    if meses_hist:
        fig.add_trace(go.Scatter(
            x=meses_hist,
            y=[v/1e6 for v in valores_hist],
            mode='lines+markers+text',
            name='Cartera Histórica',
            line=dict(color='#00B3B0', width=4),
            marker=dict(size=8, color='#00B3B0'),
            text=[f'${v/1e6:.1f}M' for v in valores_hist],
            textposition='top center',
            textfont=dict(color='#00B3B0', size=10)
        ), row=1, col=1)

    if meses_proy:
        fig.add_trace(go.Scatter(
            x=meses_proy,
            y=[v/1e6 for v in valores_proy],
            mode='lines+markers+text',
            name='Proyección',
            line=dict(color='#F57C00', width=4, dash='dash'),
            marker=dict(size=8, color='#F57C00'),
            text=[f'${v/1e6:.1f}M' for v in valores_proy],
            textposition='top center',
            textfont=dict(color='#F57C00', size=10)
        ), row=1, col=1)

    fig.update_layout(
        height=600,
        showlegend=True,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    fig.update_xaxes(title_text="Mes", row=1, col=1, tickangle=-45)
    fig.update_yaxes(title_text="Millones COP", tickprefix="$", row=1, col=1)

    # Segunda gráfica (clientes) - no implementada en el dashboard, se deja vacía
    fig.update_xaxes(title_text="Mes", row=2, col=1, tickangle=-45)
    fig.update_yaxes(title_text="Clientes", row=2, col=1)

    return fig


def _grafica_concentracion_cartera(df):
    """Gráfica 6: Concentración 20/80"""
    if df.empty:
        return None

    cartera_cliente = df.groupby(['nit_cliente', 'razon_social_cliente'])['total_cop'].sum().sort_values(ascending=False)
    total = cartera_cliente.sum()
    if total == 0:
        return None

    acum = cartera_cliente.cumsum()
    clientes_20 = len(acum[acum <= total * 0.2])
    cartera_80 = acum.iloc[clientes_20] if clientes_20 < len(acum) else acum.iloc[-1]

    # Top 15 clientes
    top_clientes = cartera_cliente.head(15).iloc[::-1]
    clientes_nombres = [nombre[:15] + '...' if len(nombre) > 15 else nombre 
                        for nombre in top_clientes.index.get_level_values(1)]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('Top 15 Clientes', 'Distribución 20/80'),
                        specs=[[{"type": "bar"}, {"type": "bar"}]])

    fig.add_trace(go.Bar(
        y=clientes_nombres,
        x=top_clientes.values,
        orientation='h',
        marker_color='#3b82f6'
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=[f'Top {clientes_20} Clientes', f'Resto {len(cartera_cliente)-clientes_20} Clientes'],
        y=[cartera_80, total - cartera_80],
        marker_color=['#00B3B0', '#475569']
    ), row=1, col=2)

    fig.update_layout(
        title="Concentración de Cartera - Análisis 20/80",
        template="plotly_dark",
        height=500,
        showlegend=False
    )
    fig.update_xaxes(tickprefix='$', tickformat='.0s', row=1, col=1)
    fig.update_xaxes(tickprefix='$', tickformat='.0s', row=1, col=2)
    return fig


def _grafica_envejecimiento_detallado(df):
    """Gráfica 7: Envejecimiento Detallado"""
    if df.empty:
        return None

    rangos = {
        'Corriente (0 días)': (0, 0),
        '1-15 días': (1, 15),
        '16-30 días': (16, 30),
        '31-60 días': (31, 60),
        '61-90 días': (61, 90),
        '91-180 días': (91, 180),
        '181-365 días': (181, 365),
        '+365 días': (366, 9999)
    }

    valores_rangos = {}
    clientes_rangos = {}
    for nombre, (min_dias, max_dias) in rangos.items():
        if max_dias == 9999:
            datos_rango = df[df['dias_vencidos'] >= min_dias]
        else:
            datos_rango = df[(df['dias_vencidos'] >= min_dias) & (df['dias_vencidos'] <= max_dias)]
        valores_rangos[nombre] = datos_rango['total_cop'].sum()
        clientes_rangos[nombre] = datos_rango['nit_cliente'].nunique()

    # Filtrar rangos con valor
    valores_rangos = {k: v for k, v in valores_rangos.items() if v > 0}
    if not valores_rangos:
        return None

    rangos_nombres = list(valores_rangos.keys())
    rangos_valores = [v / 1e6 for v in valores_rangos.values()]
    rangos_clientes = [clientes_rangos[k] for k in rangos_nombres]

    colores = ['#10b981', '#84cc16', '#f59e0b', '#f97316', '#ef4444', '#dc2626', '#991b1b', '#7f1d1d']
    colores = colores[:len(rangos_nombres)]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('Cartera por Rango', 'Distribución Porcentual'),
                        specs=[[{"type": "bar"}, {"type": "pie"}]])

    fig.add_trace(go.Bar(
        x=rangos_nombres,
        y=rangos_valores,
        marker_color=colores,
        text=[f'${v:.1f}M<br>{c} clientes' for v, c in zip(rangos_valores, rangos_clientes)],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Cartera: $%{y:.1f}M<br>Clientes: %{customdata}<extra></extra>',
        customdata=rangos_clientes
    ), row=1, col=1)

    total_cartera = sum(valores_rangos.values())
    porcentajes = [v / total_cartera * 100 for v in valores_rangos.values()]

    fig.add_trace(go.Pie(
        labels=rangos_nombres,
        values=porcentajes,
        marker_colors=colores,
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Porcentaje: %{percent}<br>Valor: $%{value:.1f}M<extra></extra>'
    ), row=1, col=2)

    fig.update_layout(
        height=500,
        showlegend=False,
        template="plotly_dark",
        title="Análisis Detallado de Envejecimiento - Cartera Actual"
    )
    fig.update_xaxes(tickangle=45, row=1, col=1)
    fig.update_yaxes(title_text="Millones COP", tickprefix="$", row=1, col=1)
    return fig


def _grafica_analisis_geografico(df):
    """Gráfica 8: Análisis Geográfico"""
    if df.empty or 'ciudad' not in df.columns:
        return None

    # Agrupar por ciudad (la columna ya debe venir del merge en el dashboard)
    cartera_ciudad = df.groupby('ciudad').agg({
        'total_cop': 'sum',
        'nit_cliente': 'nunique',
        'dias_vencidos': 'mean'
    }).round(2)

    cartera_ciudad = cartera_ciudad[cartera_ciudad['total_cop'] > 0]
    cartera_ciudad = cartera_ciudad.sort_values('total_cop', ascending=False).head(15)

    if cartera_ciudad.empty:
        return None

    ciudades = [c[:20] + '...' if len(c) > 20 else c for c in cartera_ciudad.index]
    valores = cartera_ciudad['total_cop'].values / 1e6
    n_clientes = cartera_ciudad['nit_cliente'].values

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=('Top 15 Ciudades - Cartera', 'Promedio de Morosidad'),
                        specs=[[{"type": "bar"}, {"type": "bar"}]])

    fig.add_trace(go.Bar(
        y=ciudades,
        x=valores,
        orientation='h',
        marker_color='#3b82f6',
        text=[f'${v:.1f}M<br>{c} clientes' for v, c in zip(valores, n_clientes)],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Cartera: $%{x:.1f}M<br>Clientes: %{customdata}<extra></extra>',
        customdata=n_clientes
    ), row=1, col=1)

    # Ciudades con mora (promedio de días vencidos)
    ciudades_mora = cartera_ciudad[cartera_ciudad['dias_vencidos'] > 0]
    if not ciudades_mora.empty:
        ciudades_mora = ciudades_mora.sort_values('dias_vencidos', ascending=False)
        ciudades_mora_nombres = [c[:15] + '...' if len(c) > 15 else c for c in ciudades_mora.index]
        promedios_mora = ciudades_mora['dias_vencidos'].values

        colors_mora = [f'rgb({int(239 + (220-239)*i/len(promedios_mora))}, {int(68 + (38-68)*i/len(promedios_mora))}, {int(68 + (38-68)*i/len(promedios_mora))})'
                       for i in range(len(promedios_mora))]

        fig.add_trace(go.Bar(
            x=ciudades_mora_nombres,
            y=promedios_mora,
            marker_color=colors_mora,
            text=[f'{v:.0f} días' for v in promedios_mora],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Días vencidos promedio: %{y:.0f} días<extra></extra>'
        ), row=1, col=2)

        fig.update_xaxes(tickangle=45, row=1, col=2)
    else:
        fig.add_annotation(
            text="No hay morosidad en las ciudades analizadas",
            xref="x2", yref="y2",
            x=0.5, y=0.5,
            xanchor="center", yanchor="middle",
            showarrow=False,
            font=dict(size=14, color="#94a3b8"),
            row=1, col=2
        )

    fig.update_layout(
        height=500,
        showlegend=False,
        template="plotly_dark",
        title="Análisis Geográfico de Cartera"
    )
    fig.update_xaxes(title_text="Millones COP", tickprefix="$", row=1, col=1)
    fig.update_yaxes(title_text="Ciudad", row=1, col=1)
    if not ciudades_mora.empty:
        fig.update_yaxes(title_text="Días Vencidos Promedio", row=1, col=2)
    return fig


# ------------------------------------------------------------
# GENERADOR DE REPORTE HTML
# ------------------------------------------------------------

def generar_reporte_html(df_filtrado, graficas_activas, filtros_aplicados=None):
    """Genera reporte ejecutivo con las gráficas idénticas al dashboard"""
    if df_filtrado.empty:
        return None

    # Título dinámico
    tipo_reporte = "REPORTE GENERAL DE CARTERA"
    detalles = []
    if filtros_aplicados:
        v = filtros_aplicados.get('vendedor')
        if v and v not in ["Todos los vendedores", "Todos"]:
            detalles.append(f"Vendedor: {v}")
        c = filtros_aplicados.get('ciudad')
        if c and c not in ["Todas las ciudades", "Todas"]:
            detalles.append(f"Ciudad: {c}")
        cd = filtros_aplicados.get('condicion')
        if cd and cd not in ["Todas las condiciones"]:
            detalles.append(f"Condición: {cd}")
        d = filtros_aplicados.get('dias')
        if d and d not in ["Todos los días"]:
            detalles.append(f"Tramo: {d}")

        if detalles:
            tipo_reporte = "REPORTE DE CARTERA PARTICULAR"

    texto_filtros = " / ".join(detalles) if detalles else "Consolidado Completo de la Compañía"

    # Logo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo_login.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    # Métricas
    total_cartera = df_filtrado['total_cop'].sum()
    mora_cartera = df_filtrado[df_filtrado['dias_vencidos'] > 0]['total_cop'].sum()
    porc_mora = (mora_cartera / total_cartera * 100) if total_cartera > 0 else 0
    total_clientes = df_filtrado['nit_cliente'].nunique()
    clientes_mora = df_filtrado[df_filtrado['dias_vencidos'] > 0]['nit_cliente'].nunique()
    porc_cl_mora = (clientes_mora / total_clientes * 100) if total_clientes > 0 else 0

    # HTML base
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
            @media print {{
                body {{ background: white; padding: 20px; }}
                .container {{ box-shadow: none; padding: 20px; }}
                .chart-card {{ break-inside: avoid; }}
                .metric-card {{ break-inside: avoid; }}
            }}
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
                    <div class="metric-title" style="margin-top:5px;">Clientes en mora: {clientes_mora} ({porc_cl_mora:.1f}%)</div>
                </div>
            </div>
    """

    # Mapeo de nombres para títulos
    nombres_graficas = {
        'chart1': '📊 Distribución por Estado',
        'chart2': '⚠️ Top 10 Clientes Mora',
        'chart3': '👥 Cartera por Vendedor',
        'chart4': '💰 Condiciones de Pago',
        'chart5': '📅 Evolución + Proyección',
        'chart6': '📊 Concentración 20/80',
        'chart7': '📈 Envejecimiento Detallado',
        'chart8': '🏙️ Análisis Geográfico',
        'chart9': '💰 Proyección por Crédito'
    }

    # Mapeo de funciones
    funciones = {
        'chart1': _grafica_distribucion_estado,
        'chart2': _grafica_top_clientes_mora,
        'chart4': _grafica_condiciones_pago,
        'chart5': _grafica_evolucion_proyeccion,
        'chart6': _grafica_concentracion_cartera,
        'chart7': _grafica_envejecimiento_detallado,
        'chart8': _grafica_analisis_geografico,       
    }

    for chart_id in graficas_activas:
        if chart_id in funciones:
            fig = funciones[chart_id](df_filtrado)
            if fig:
                # Convertir la figura a HTML (sin incluir plotly.js de nuevo)
                chart_html = fig.to_html(full_html=False, include_plotlyjs=False)
                html += f"""
                <div class="chart-card">
                    <h3>{nombres_graficas[chart_id]}</h3>
                    {chart_html}
                </div>
                """

    html += """
            <div class="footer">
                ALPAPEL S.A.S. - Confidencial<br>
                Reporte generado automáticamente.
            </div>
        </div>
    </body>
    </html>
    """
    return html
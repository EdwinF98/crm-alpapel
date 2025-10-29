# graficas.py
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def crear_grafica_distribucion_estado(datos_graficas):
    """Crea gráfica de distribución por estado de cartera"""
    try:
        distribucion_estado = datos_graficas['distribucion_estado']
        
        if not any(distribucion_estado):
            return None
        
        categorias = ['Corriente', '1-30 días', '31-60 días', '61-90 días', '+90 días']
        valores = [distribucion_estado[i] or 0 for i in range(5)]
        valores_millones = [valor / 1000000 for valor in valores]
        
        colores_mora = ['#10b981', '#f59e0b', '#f97316', '#dc2626', '#991b1b']
        
        # Crear DataFrame para Plotly
        df = pd.DataFrame({
            'Estado': categorias,
            'Valor_Millones': valores_millones,
            'Color': colores_mora
        })
        
        fig = px.bar(
            df,
            x='Estado',
            y='Valor_Millones',
            title="Distribución de Cartera por Estado (Valores en Millones)",
            labels={'Valor_Millones': 'Valor (Millones COP)', 'Estado': 'Estado de Cartera'},
            color='Estado',
            color_discrete_sequence=colores_mora
        )
        
        # Layout sin parámetros obsoletos
        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            showlegend=False,
            height=400
        )
        
        fig.update_yaxes(tickprefix='$', tickformat='.1f')
        fig.update_traces(texttemplate='$%{y:.1f}M', textposition='outside')
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de distribución: {e}")
        return None

def crear_grafica_top_clientes(datos_graficas):
    """Crea gráfica de top clientes con mora"""
    try:
        top_clientes_mora = datos_graficas['top_clientes_mora']
        
        if not top_clientes_mora:
            return None
        
        clientes = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] for item in top_clientes_mora[:10]]
        valores = [item[1] for item in top_clientes_mora[:10]]
        valores_millones = [valor / 1000000 for valor in valores]
        
        color_corporativo = '#00B3B0'
        
        # Crear DataFrame para Plotly
        df = pd.DataFrame({
            'Cliente': clientes,
            'Mora_Millones': valores_millones
        })
        
        fig = px.bar(
            df,
            y='Cliente',
            x='Mora_Millones',
            title="Top 10 Clientes con Mayor Mora",
            labels={'Mora_Millones': 'Valor en Mora (Millones COP)', 'Cliente': 'Cliente'},
            orientation='h',
            color_discrete_sequence=[color_corporativo]
        )
        
        # Layout sin parámetros obsoletos
        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            showlegend=False,
            height=400
        )
        
        fig.update_xaxes(tickprefix='$', tickformat='.1f')
        
        return fig
        
    except Exception as e:
        print(f"Error creando gráfica de top clientes: {e}")
        return None

def crear_grafica_evolucion_mensual(datos_graficas):
    """Crea gráfica de evolución mensual - VERSIÓN LIMPIA"""
    try:
        import streamlit as st
        from datetime import datetime, timedelta
        import plotly.express as px
        import pandas as pd
        
        # Usar la misma instancia de DatabaseManager
        db = st.session_state.db
        
        cartera_actual = db.obtener_cartera_actual()
        
        if cartera_actual.empty:
            return None
        
        # Crear copia y procesar fechas
        cartera_actual = cartera_actual.copy()
        cartera_actual['fecha_vencimiento'] = pd.to_datetime(cartera_actual['fecha_vencimiento'], errors='coerce')
        
        # Filtrar fechas válidas
        cartera_actual = cartera_actual.dropna(subset=['fecha_vencimiento'])
        
        if cartera_actual.empty:
            return None
        
        # Filtrar últimos 12 meses
        fecha_limite = datetime.now() - timedelta(days=365)
        cartera_filtrada = cartera_actual[cartera_actual['fecha_vencimiento'] >= fecha_limite]
        
        if cartera_filtrada.empty:
            return None
        
        # Procesar datos por mes
        cartera_filtrada['mes'] = cartera_filtrada['fecha_vencimiento'].dt.strftime('%m/%y')
        
        cartera_por_mes = cartera_filtrada.groupby('mes').agg({
            'total_cop': 'sum',
            'nro_factura': 'count'
        }).reset_index()
        
        if cartera_por_mes.empty:
            return None
        
        # Ordenar por mes
        try:
            cartera_por_mes['mes_orden'] = pd.to_datetime(cartera_por_mes['mes'], format='%m/%y')
            cartera_por_mes = cartera_por_mes.sort_values('mes_orden')
            cartera_por_mes = cartera_por_mes.drop('mes_orden', axis=1)
        except:
            cartera_por_mes = cartera_por_mes.sort_values('mes')
        
        # Convertir a millones
        cartera_por_mes['total_millones'] = cartera_por_mes['total_cop'] / 1000000
        
        # Crear gráfica
        fig = px.bar(
            cartera_por_mes,
            x='mes',
            y='total_millones',
            title="Cartera por Mes de Vencimiento (Último Año)",
            labels={
                'total_millones': 'Valor (Millones COP)', 
                'mes': 'Mes de Vencimiento'
            },
            text='total_millones'
        )
        
        # Actualizar diseño
        fig.update_traces(
            texttemplate='$%{y:.1f}M<br>%{customdata[0]} facturas',
            textposition='outside',
            customdata=cartera_por_mes[['nro_factura']].values,
            marker_color='#00B3B0',
            hovertemplate='<b>Mes: %{x}</b><br>Valor: $%{y:.1f}M<br>Facturas: %{customdata[0]}<extra></extra>'
        )
        
        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font_color='#e2e8f0',
            height=500,
            showlegend=False,
            xaxis=dict(tickangle=-45),
            yaxis=dict(tickprefix='$', tickformat='.1f')
        )
        
        fig.update_yaxes(title='Millones de COP', tickprefix='$', tickformat='.1f')
        fig.update_xaxes(title='Mes de Vencimiento')
        
        return fig
        
    except Exception:
        return None
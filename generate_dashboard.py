#!/usr/bin/env python3
"""
Genera un dashboard HTML interactivo con datos del BCRA.
Consulta la API, guarda CSVs y produce index.html con gráficos Plotly.js.
"""

import json
import os
from datetime import datetime
from bcra_api_client import BCRAClient

# Variables principales del BCRA
VARIABLES = {
    1: {"nombre": "Reservas Internacionales", "unidad": "USD millones", "archivo": "reservas"},
    4: {"nombre": "Tipo de Cambio (B 9791)", "unidad": "ARS/USD", "archivo": "tipo_cambio_oficial"},
    5: {"nombre": "TC Referencia (A 3500)", "unidad": "ARS/USD", "archivo": "tipo_cambio_referencia"},
    12: {"nombre": "Tasa Plazo Fijo", "unidad": "% TNA", "archivo": "tasa_plazo_fijo"},
    15: {"nombre": "Base Monetaria", "unidad": "millones ARS", "archivo": "base_monetaria"},
}

DIAS_ATRAS = 90


def fetch_datos():
    """Consulta la API y devuelve un dict {id: {nombre, unidad, fechas, valores, ultimo}}"""
    bcra = BCRAClient()
    datos = {}

    for id_var, info in VARIABLES.items():
        print(f"Consultando {info['nombre']} (ID {id_var})...")
        try:
            df = bcra.get_datos_variable(id_var, dias_atras=DIAS_ATRAS)
            if not df.empty:
                # Guardar CSV
                os.makedirs("data", exist_ok=True)
                df.to_csv(f"data/{info['archivo']}.csv", index=False)

                fechas = df["fecha"].dt.strftime("%Y-%m-%d").tolist()
                valores = df["valor"].tolist()
                ultimo = valores[-1] if valores else None
                datos[id_var] = {
                    "nombre": info["nombre"],
                    "unidad": info["unidad"],
                    "fechas": fechas,
                    "valores": valores,
                    "ultimo": ultimo,
                }
            else:
                print(f"  Sin datos para {info['nombre']}")
        except Exception as e:
            print(f"  Error: {e}")

    return datos


def format_valor(valor, unidad):
    """Formatea un valor numérico para mostrar en tarjeta."""
    if valor is None:
        return "N/D"
    if "USD" in unidad or "ARS" in unidad:
        return f"{valor:,.0f}"
    if "%" in unidad:
        return f"{valor:.1f}%"
    return f"{valor:,.2f}"


def generar_html(datos):
    """Genera index.html con dashboard Plotly.js."""
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Colores para cada gráfico
    colores = ["#00d4aa", "#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff"]

    # Generar tarjetas HTML
    cards_html = ""
    for i, (id_var, d) in enumerate(datos.items()):
        color = colores[i % len(colores)]
        valor_fmt = format_valor(d["ultimo"], d["unidad"])
        cards_html += f"""
        <div class="card" style="border-top: 3px solid {color}">
            <div class="card-title">{d['nombre']}</div>
            <div class="card-value" style="color: {color}">{valor_fmt}</div>
            <div class="card-unit">{d['unidad']}</div>
        </div>"""

    # Generar gráficos Plotly
    plots_js = ""
    plots_html = ""
    for i, (id_var, d) in enumerate(datos.items()):
        color = colores[i % len(colores)]
        div_id = f"chart_{id_var}"
        plots_html += f'<div class="chart-container"><div id="{div_id}"></div></div>\n'
        plots_js += f"""
    Plotly.newPlot('{div_id}', [{{
        x: {json.dumps(d['fechas'])},
        y: {json.dumps(d['valores'])},
        type: 'scatter',
        mode: 'lines',
        line: {{color: '{color}', width: 2}},
        fill: 'tozeroy',
        fillcolor: '{color}22',
        hovertemplate: '%{{x}}<br><b>%{{y:,.2f}}</b> {d["unidad"]}<extra></extra>'
    }}], {{
        title: {{text: '{d["nombre"]}', font: {{color: '#e0e0e0', size: 16}}}},
        paper_bgcolor: '#1e1e2e',
        plot_bgcolor: '#1e1e2e',
        font: {{color: '#a0a0a0'}},
        xaxis: {{gridcolor: '#333', linecolor: '#444'}},
        yaxis: {{gridcolor: '#333', linecolor: '#444', title: '{d["unidad"]}'}},
        margin: {{l: 60, r: 20, t: 50, b: 40}},
        hovermode: 'x unified'
    }}, {{responsive: true}});
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard BCRA</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #13131f;
            color: #e0e0e0;
            min-height: 100vh;
        }}
        header {{
            background: #1e1e2e;
            padding: 1.5rem 2rem;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        header h1 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        header h1 span {{ color: #00d4aa; }}
        .updated {{
            color: #888;
            font-size: 0.85rem;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            padding: 1.5rem 2rem;
        }}
        .card {{
            background: #1e1e2e;
            border-radius: 8px;
            padding: 1.2rem;
        }}
        .card-title {{
            font-size: 0.8rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}
        .card-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        .card-unit {{
            font-size: 0.75rem;
            color: #666;
            margin-top: 0.3rem;
        }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 1rem;
            padding: 0 2rem 2rem;
        }}
        .chart-container {{
            background: #1e1e2e;
            border-radius: 8px;
            padding: 0.5rem;
            overflow: hidden;
        }}
        footer {{
            text-align: center;
            padding: 1.5rem;
            color: #555;
            font-size: 0.8rem;
        }}
        footer a {{ color: #00d4aa; text-decoration: none; }}
        @media (max-width: 600px) {{
            .charts {{ grid-template-columns: 1fr; }}
            header {{ padding: 1rem; }}
            .cards {{ padding: 1rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1><span>BCRA</span> Dashboard</h1>
        <div class="updated">Actualizado: {ahora} (UTC-3)</div>
    </header>

    <div class="cards">
        {cards_html}
    </div>

    <div class="charts">
        {plots_html}
    </div>

    <footer>
        Datos de la <a href="https://www.bcra.gob.ar/BCRAyVos/Catalogo_de_APIs_702.asp">API del BCRA</a>.
        Actualizado cada 6 horas via GitHub Actions.
    </footer>

    <script>
    {plots_js}
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nDashboard generado: index.html ({len(html):,} bytes)")


def main():
    datos = fetch_datos()
    if datos:
        generar_html(datos)
    else:
        print("No se obtuvieron datos. No se genera dashboard.")


if __name__ == "__main__":
    main()

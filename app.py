import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Poopydiscoop Wrapped", page_icon="💩", layout="wide")

@st.cache_data
def load_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)
    header = df.iloc[0].tolist()
    df = df.iloc[1:].copy()
    df.columns = header
    df = df.dropna(axis=1, how="all")
    df["Miembro"] = df["Miembro"].astype(str).str.strip()

    # Identify day columns (datetime) and totals
    day_cols = [c for c in df.columns if isinstance(c, pd.Timestamp)]
    tot_col = "Total de Cagadas"
    kpd_col = "Cagadas diarias"

    # Cast numerics
    for c in day_cols + [tot_col, kpd_col]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Separate members vs total row
    total_row = df[df["Miembro"].str.lower() == "total"]
    members = df[df["Miembro"].str.lower() != "total"].copy()

    return members, total_row, day_cols, tot_col, kpd_col

st.title("💩 Poopydiscoop Wrapped")
st.caption("Dashboard interactivo para explorar 2024 vs 2025 (datos diarios + rankings + heatmap)")

xlsx_path = "Poopydiscoop.xlsx"
sheets = pd.ExcelFile(xlsx_path).sheet_names

colA, colB = st.columns([1, 2])
with colA:
    year_sheet = st.selectbox("Selecciona el año", sheets, index=len(sheets)-1)
with colB:
    mode = st.radio("Modo", ["Resumen", "Explorar por persona", "Comparar 2 personas"], horizontal=True)

members, total_row, day_cols, tot_col, kpd_col = load_sheet(xlsx_path, year_sheet)

# Sidebar filters
with st.sidebar:
    st.header("Filtros")
    selected = st.multiselect("Participantes", members["Miembro"].tolist(), default=members["Miembro"].tolist())
    show_total_line = st.checkbox("Mostrar línea del total del grupo", value=True)

df = members[members["Miembro"].isin(selected)].copy()
daily_total = df[day_cols].sum()
daily_total.index = [d.day for d in daily_total.index]

# Top KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("KGDs totales (grupo)", int(total_row[tot_col].iloc[0]) if not total_row.empty else int(df[tot_col].sum()))
k2.metric("Promedio diario (grupo)", f"{float(total_row[kpd_col].iloc[0]):.1f}" if not total_row.empty else f"{df[tot_col].sum()/31:.1f}")
k3.metric("Día pico", f"{int(daily_total.idxmax())} dic · {int(daily_total.max())} KGDs")
k4.metric("Día mínimo", f"{int(daily_total.idxmin())} dic · {int(daily_total.min())} KGDs")

st.divider()

# Line chart
st.subheader("Actividad diaria del grupo")
fig = px.line(x=daily_total.index, y=daily_total.values, labels={"x": "Día de diciembre", "y": "KGDs"})
st.plotly_chart(fig, use_container_width=True)

# Ranking
st.subheader("Ranking anual")
rank = df[["Miembro", tot_col, kpd_col]].sort_values(tot_col, ascending=False).reset_index(drop=True)
rank.columns = ["Miembro", "Total KGDs", "KPD"]
st.dataframe(rank, use_container_width=True, hide_index=True)

# Rivalry compare 2
if mode == "Comparar 2 personas":
    st.subheader("Comparación 1 a 1")
    c1, c2 = st.columns(2)
    with c1:
        p1 = st.selectbox("Persona A", members["Miembro"].tolist(), index=0)
    with c2:
        p2 = st.selectbox("Persona B", members["Miembro"].tolist(), index=1 if len(members)>1 else 0)

    s1 = members.loc[members["Miembro"] == p1, day_cols].iloc[0]
    s2 = members.loc[members["Miembro"] == p2, day_cols].iloc[0]
    comp = pd.DataFrame({"día": [d.day for d in day_cols], p1: s1.values, p2: s2.values})

    fig2 = px.line(comp, x="día", y=[p1, p2], labels={"value": "KGDs", "variable": "Persona"})
    st.plotly_chart(fig2, use_container_width=True)

# Heatmap
st.subheader("Mapa de calor (participantes vs días)")
heat = df.set_index("Miembro")[day_cols]
fig3 = px.imshow(
    heat,
    labels=dict(x="Día de diciembre", y="Miembro", color="KGDs"),
    aspect="auto",
)
st.plotly_chart(fig3, use_container_width=True)

st.caption("Tip: pasa el mouse sobre cualquier punto/celda para ver el valor exacto.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard zapisów", layout="wide")
st.title("📊 Dashboard zapisów")

# --- Wczytaj dane ---
uploaded_file = st.file_uploader("Wgraj plik Excel (.xlsx)", type=["xlsx", "csv"])

if uploaded_file:
    import io
    raw = uploaded_file.read()
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python")
    else:
        df = pd.read_excel(io.BytesIO(raw), sheet_name="dane")

    df.columns = [str(c).strip() for c in df.columns]
    df["dzien_zapisu"] = pd.to_datetime(df["dzien_zapisu"])
    df = df.sort_values("dzien_zapisu")

    # Kolumny z danymi (wszystko poza datą)
    all_cols = [c for c in df.columns if c != "dzien_zapisu"]

    # Podziel kolumny na grupy
    def get_group(col):
        if col.startswith("online_platni"):
            return "online_platni"
        elif col.startswith("sala_platni"):
            return "sala_platni"
        elif col.startswith("platni"):
            return "platni"
        elif col.startswith("suma_zapisow"):
            return "suma_zapisow"
        return "inne"

    groups = sorted(set(get_group(c) for c in all_cols))
    years = sorted(set(c.split("_")[-1] for c in all_cols if c.split("_")[-1].isdigit()))

    # --- Filtry w sidebarze ---
    st.sidebar.header("🔧 Filtry")

    selected_groups = st.sidebar.multiselect(
        "Typ serii", groups, default=groups
    )
    selected_years = st.sidebar.multiselect(
        "Rok", years, default=years
    )

    date_range = st.sidebar.date_input(
        "Zakres dat",
        value=[df["dzien_zapisu"].min(), df["dzien_zapisu"].max()],
        min_value=df["dzien_zapisu"].min().date(),
        max_value=df["dzien_zapisu"].max().date(),
    )

    # Filtruj dane po dacie
    if len(date_range) == 2:
        df = df[(df["dzien_zapisu"] >= pd.Timestamp(date_range[0])) &
                (df["dzien_zapisu"] <= pd.Timestamp(date_range[1]))]

    # Wybierz kolumny do wyświetlenia
    selected_cols = [
        c for c in all_cols
        if get_group(c) in selected_groups
        and c.split("_")[-1] in selected_years
    ]

    # --- Wykres ---
    fig = go.Figure()

    # Kolory per rok
    year_colors = {"2023": "#1f77b4", "2024": "#ff7f0e", "2025": "#2ca02c", "2026": "#d62728"}
    # Styl linii per grupa
    group_dash = {
        "online_platni": "solid",
        "platni": "dash",
        "sala_platni": "dot",
        "suma_zapisow": "dashdot",
    }

    for col in selected_cols:
        year = col.split("_")[-1]
        group = get_group(col)
        fig.add_trace(go.Scatter(
            x=df["dzien_zapisu"],
            y=df[col],
            name=col,
            mode="lines",
            line=dict(
                color=year_colors.get(year, "#888"),
                dash=group_dash.get(group, "solid"),
                width=2,
            ),
        ))

    fig.update_layout(
        height=600,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_title="Data",
        yaxis_title="Liczba",
        margin=dict(t=80),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela z ostatnimi wartościami
    with st.expander("📋 Ostatnie wartości"):
        last = df[["dzien_zapisu"] + selected_cols].tail(10)
        st.dataframe(last, use_container_width=True)

else:
    st.info("👆 Wgraj plik Excel żeby zacząć")
    st.markdown("""
    **Oczekiwany format:**
    - Kolumna `dzien_zapisu` z datami
    - Kolumny w formacie: `online_platni_2023`, `platni_2024`, `sala_platni_2025`, `suma_zapisow_2026` itp.
    """)
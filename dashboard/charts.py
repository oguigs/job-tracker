import json
import pandas as pd
import plotly.express as px


def extrair_stacks_flat(df, categoria: str) -> pd.DataFrame:
    todas = []
    for stacks_json in df["stacks"].dropna():
        try:
            stacks = json.loads(stacks_json) if isinstance(stacks_json, str) else stacks_json
            todas.extend(stacks.get(categoria, []))
        except Exception:
            pass
    return pd.Series(todas).value_counts().reset_index().rename(
        columns={"index": "stack", 0: "count", "count": "count"}
    )


def grafico_stacks(df_counts: pd.DataFrame, titulo: str, cor: str):
    if df_counts.empty:
        return None
    df_counts.columns = ["stack", "count"]
    fig = px.bar(df_counts, x="count", y="stack", orientation="h",
        title=titulo, color_discrete_sequence=[cor], template="plotly_white")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0),
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="Vagas"), showlegend=False, title_font_size=14)
    fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x} vagas<extra></extra>")
    return fig
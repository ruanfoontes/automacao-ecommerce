import argparse
from typing import Optional

import pandas as pd

from etl import buscar_dados_meli


def _calcular_metricas(df: pd.DataFrame) -> tuple[pd.DataFrame, float, int, float]:
    df = df.copy()
    df["Total_Venda"] = df["Preco_Unitario"] * df["Quantidade"]
    total_faturado = float(df["Total_Venda"].sum())
    total_itens = int(df["Quantidade"].sum())
    ticket_medio = (total_faturado / len(df)) if len(df) > 0 else 0.0
    return df, total_faturado, total_itens, ticket_medio


def run_cli(*, export_csv: Optional[str] = None, limit: int = 20) -> int:
    df, mensagem = buscar_dados_meli()
    if df is None or df.empty:
        print(f"Não foi possível carregar os dados: {mensagem}")
        return 1

    df, total_faturado, total_itens, ticket_medio = _calcular_metricas(df)

    print("Dashboard de Vendas - Mercado Livre")
    print(f"Faturamento Total: R$ {total_faturado:,.2f}")
    print(f"Itens Vendidos: {total_itens}")
    print(f"Ticket Médio: R$ {ticket_medio:,.2f}")
    print("")
    print("Lista de Produtos Vendidos")
    cols = [c for c in ["Data", "Produto", "Preco_Unitario", "Quantidade", "Total_Venda", "ID_Ordem"] if c in df.columns]
    to_show = df[cols].head(max(0, limit))
    print(to_show.to_string(index=False))

    if export_csv:
        df.to_csv(export_csv, index=False, encoding="utf-8-sig")
        print("")
        print(f"CSV exportado em: {export_csv}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dashboard Meli (modo terminal, sem Streamlit).")
    parser.add_argument("--export-csv", default=None, help="Caminho para exportar o CSV (opcional).")
    parser.add_argument("--limit", type=int, default=20, help="Quantidade de linhas para exibir no terminal.")
    args = parser.parse_args()
    return run_cli(export_csv=args.export_csv, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
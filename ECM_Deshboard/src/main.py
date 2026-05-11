import argparse
import os
from typing import Optional

import pandas as pd
import requests

from etl import buscar_dados_meli
from testes_vendas import testar_conexao
from ultima_venda_profissional import buscar_ultima_venda


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise SystemExit(
            f"Variável de ambiente ausente: {var_name}\n"
            f"- Dica: crie/ajuste o arquivo .env em `ECM_Deshboard/.env` e execute novamente."
        )
    return value


def _calcular_metricas(df: pd.DataFrame) -> tuple[pd.DataFrame, float, int, float]:
    df = df.copy()
    df["Total_Venda"] = df["Preco_Unitario"] * df["Quantidade"]
    total_faturado = float(df["Total_Venda"].sum())
    total_itens = int(df["Quantidade"].sum())
    ticket_medio_item = (total_faturado / len(df)) if len(df) > 0 else 0.0
    return df, total_faturado, total_itens, ticket_medio_item


def cmd_validate_env() -> int:
    _require_env("ACCESS_TOKEN")
    _require_env("USER_ID")
    print("OK: ACCESS_TOKEN e USER_ID encontrados no ambiente.")
    return 0


def cmd_whoami() -> int:
    token = _require_env("ACCESS_TOKEN")
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Erro ao consultar /users/me: {resp.status_code}")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
        return 1

    data = resp.json()
    print(f"Seu ID real é: {data.get('id')}")
    print(f"Nome da conta: {data.get('nickname')}")
    return 0


def cmd_smoke() -> int:
    cmd_validate_env()
    testar_conexao()
    return 0


def cmd_last_sale() -> int:
    cmd_validate_env()
    buscar_ultima_venda()
    return 0


def cmd_fetch(*, limit: int = 50, show: int = 20, export_csv: Optional[str] = None) -> int:
    cmd_validate_env()

    df, mensagem = buscar_dados_meli()
    if df is None or df.empty:
        print(f"Não foi possível carregar os dados: {mensagem}")
        return 1

    df, total_faturado, total_itens, ticket_medio_item = _calcular_metricas(df)

    print("RELATÓRIO (Terminal)")
    print(f"Faturamento (por item): R$ {total_faturado:,.2f}")
    print(f"Itens vendidos: {total_itens}")
    print(f"Ticket médio (por item): R$ {ticket_medio_item:,.2f}")
    print("")

    cols = [c for c in ["Data", "Produto", "Preco_Unitario", "Quantidade", "Total_Venda", "ID_Ordem"] if c in df.columns]
    print(df[cols].head(max(0, show)).to_string(index=False))

    if export_csv:
        df.to_csv(export_csv, index=False, encoding="utf-8-sig")
        print("")
        print(f"CSV exportado em: {export_csv}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Cabeça (main) para testar o projeto via terminal.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate-env", help="Verifica se ACCESS_TOKEN e USER_ID existem.")
    sub.add_parser("whoami", help="Mostra id/nickname usando ACCESS_TOKEN (/users/me).")
    sub.add_parser("smoke", help="Teste rápido: valida env + consulta orders.")
    sub.add_parser("last-sale", help="Mostra a última venda.")

    p_fetch = sub.add_parser("fetch", help="Baixa dados, calcula métricas e imprime/exporta.")
    p_fetch.add_argument("--limit", type=int, default=50, help="Limite de pedidos (atualmente fixo no etl.py).")
    p_fetch.add_argument("--show", type=int, default=20, help="Linhas para mostrar no terminal.")
    p_fetch.add_argument("--export-csv", default=None, help="Caminho para exportar CSV (opcional).")

    args = parser.parse_args()

    if args.cmd == "validate-env":
        return cmd_validate_env()
    if args.cmd == "whoami":
        return cmd_whoami()
    if args.cmd == "smoke":
        return cmd_smoke()
    if args.cmd == "last-sale":
        return cmd_last_sale()
    if args.cmd == "fetch":
        return cmd_fetch(limit=args.limit, show=args.show, export_csv=args.export_csv)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


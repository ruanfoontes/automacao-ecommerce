"""
Extrato e resumos de vendas Mercado Livre (API orders/search).

Colunas pensadas para planilha operacional + metricas por plataforma (hoje so 'meli').
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from meli_auth import ensure_dotenv_loaded, meli_get

PLATFORM = "meli"


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _date_only(iso: Optional[str]) -> str:
    if not iso or not isinstance(iso, str):
        return ""
    return iso[:10]


def orders_results_to_rows(results: list[dict]) -> list[dict]:
    """Uma linha por item do pedido; campos do pedido repetem por item."""
    rows: list[dict] = []
    for order in results:
        oid = order.get("id")
        created = order.get("date_created") or ""
        status = order.get("status") or ""
        total_pedido = _safe_float(order.get("total_amount"))
        shipping = order.get("shipping") or {}
        if isinstance(shipping, dict):
            envio_status = shipping.get("status") or ""
            envio_id = shipping.get("id")
        else:
            envio_status = ""
            envio_id = None

        for line in order.get("order_items") or []:
            item = line.get("item") or {}
            item_id = item.get("id")
            titulo = item.get("title") or ""
            qtd = _safe_int(line.get("quantity"), 0)
            preco = _safe_float(line.get("unit_price"))
            subtotal = qtd * preco

            rows.append(
                {
                    "plataforma": PLATFORM,
                    "data_pedido": _date_only(created),
                    "data_hora_pedido": created,
                    "id_pedido": oid,
                    "status_pedido": status,
                    "total_pedido": total_pedido,
                    "moeda": order.get("currency_id") or "BRL",
                    "envio_status": envio_status,
                    "envio_id": envio_id,
                    "item_id": item_id,
                    "produto": titulo,
                    "quantidade": qtd,
                    "preco_unitario": preco,
                    "subtotal_linha_itens": subtotal,
                }
            )
    return rows


def fetch_orders_search(*, limit: int = 50, offset: int = 0) -> tuple[list[dict], str]:
    ensure_dotenv_loaded()
    user_id = os.getenv("USER_ID")
    if not user_id:
        return [], "USER_ID ausente no .env"

    url = (
        f"https://api.mercadolibre.com/orders/search"
        f"?seller={user_id}&sort=date_desc&limit={limit}&offset={offset}"
    )
    resp = meli_get(url)
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        return [], f"Erro API: {resp.status_code} {detail}"

    data = resp.json()
    return list(data.get("results") or []), "Sucesso"


def buscar_extrato_meli(*, limit: int = 50, max_pages: int = 1) -> tuple[pd.DataFrame, str]:
    """
    Varias paginas: offset += limit ate max_pages ou acabar resultados.
    """
    all_results: list[dict] = []
    for page in range(max(1, max_pages)):
        offset = page * limit
        chunk, msg = fetch_orders_search(limit=limit, offset=offset)
        if msg != "Sucesso":
            if not all_results:
                return pd.DataFrame(), msg
            break
        if not chunk:
            break
        all_results.extend(chunk)
        if len(chunk) < limit:
            break

    rows = orders_results_to_rows(all_results)
    if not rows:
        return pd.DataFrame(), "Nenhum pedido retornado (lista vazia)."
    return pd.DataFrame(rows), "Sucesso"


def resumo_por_plataforma(df: pd.DataFrame) -> pd.DataFrame:
    """Metricas do backlog: vendas (pedidos), faturamento (total por pedido, sem duplicar)."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "plataforma",
                "pedidos_distintos",
                "faturamento_total_pedidos",
                "itens_vendidos_unidades",
                "receita_soma_linhas_itens",
                "ticket_medio_pedido",
            ]
        )

    rows: list[dict[str, Any]] = []
    for plat, g in df.groupby("plataforma", dropna=False):
        pedidos = int(g["id_pedido"].nunique())
        fat = float(g.drop_duplicates(subset=["id_pedido"])["total_pedido"].sum())
        itens = int(g["quantidade"].sum())
        receita_linhas = float(g["subtotal_linha_itens"].sum())
        ticket = float(fat / pedidos) if pedidos else 0.0
        rows.append(
            {
                "plataforma": plat,
                "pedidos_distintos": pedidos,
                "faturamento_total_pedidos": fat,
                "itens_vendidos_unidades": itens,
                "receita_soma_linhas_itens": receita_linhas,
                "ticket_medio_pedido": ticket,
            }
        )
    return pd.DataFrame(rows)


def top_itens(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    keys = ["plataforma", "item_id", "produto"]
    use = [c for c in keys if c in df.columns]
    g = (
        df.groupby(use, dropna=False)
        .agg(
            quantidade_total=("quantidade", "sum"),
            receita_total=("subtotal_linha_itens", "sum"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
        .head(n)
    )
    return g


def exportar_pasta(
    pasta: Path,
    *,
    limit: int = 50,
    max_pages: int = 1,
) -> tuple[Path, Path, Path, pd.DataFrame, str]:
    """
    Grava 3 CSVs UTF-8 com BOM para Excel:
    - meli_extrato_itens.csv
    - meli_resumo_plataforma.csv
    - meli_top_itens.csv
    Retorna tambem o DataFrame do extrato (evita nova chamada a API).
    """
    pasta.mkdir(parents=True, exist_ok=True)
    df, msg = buscar_extrato_meli(limit=limit, max_pages=max_pages)
    if df.empty:
        raise RuntimeError(msg)

    extrato_path = pasta / "meli_extrato_itens.csv"
    resumo_path = pasta / "meli_resumo_plataforma.csv"
    top_path = pasta / "meli_top_itens.csv"

    df.to_csv(extrato_path, index=False, encoding="utf-8-sig")
    resumo_por_plataforma(df).to_csv(resumo_path, index=False, encoding="utf-8-sig")
    top_itens(df, n=30).to_csv(top_path, index=False, encoding="utf-8-sig")

    meta_path = pasta / "meli_export_meta.txt"
    meta_path.write_text(
        "Gerado em: "
        + datetime.now().isoformat(timespec="seconds")
        + f"\nLinhas extrato: {len(df)}\nLimite por pagina: {limit}\nPaginas: {max_pages}\n",
        encoding="utf-8",
    )

    return extrato_path, resumo_path, top_path, df, msg


def pasta_export_padraio() -> Path:
    """ECM_Deshboard/exports/meli_YYYYMMDD_HHMMSS"""
    base = Path(__file__).resolve().parent.parent / "exports"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base / f"meli_{stamp}"

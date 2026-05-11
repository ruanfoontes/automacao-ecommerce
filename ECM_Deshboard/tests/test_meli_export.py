"""Testes do pipeline de extrato e agregações (sem rede)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from meli_export import (
    buscar_extrato_meli,
    exportar_pasta,
    orders_results_to_rows,
    resumo_por_plataforma,
    top_itens,
)


class TestOrdersResultsToRows:
    def test_vazio(self) -> None:
        assert orders_results_to_rows([]) == []

    def test_um_pedido_um_item(self, order_um_item: list[dict]) -> None:
        rows = orders_results_to_rows(order_um_item)
        assert len(rows) == 1
        r = rows[0]
        assert r["plataforma"] == "meli"
        assert r["id_pedido"] == 1001
        assert r["data_pedido"] == "2026-05-01"
        assert r["quantidade"] == 2
        assert r["preco_unitario"] == 75.0
        assert r["subtotal_linha_itens"] == 150.0
        assert r["total_pedido"] == 150.0
        assert r["envio_status"] == "ready_to_ship"
        assert r["envio_id"] == 555
        assert r["produto"] == "Produto A"
        assert r["item_id"] == "MLB1"

    def test_um_pedido_dois_itens(self, order_dois_itens_mesmo_pedido: list[dict]) -> None:
        rows = orders_results_to_rows(order_dois_itens_mesmo_pedido)
        assert len(rows) == 2
        assert all(x["id_pedido"] == 2002 for x in rows)
        assert rows[0]["subtotal_linha_itens"] == 100.0
        assert rows[1]["subtotal_linha_itens"] == 200.0
        assert rows[0]["total_pedido"] == 300.0
        assert rows[1]["total_pedido"] == 300.0

    def test_sem_order_items(self) -> None:
        rows = orders_results_to_rows([{"id": 1, "date_created": "2026-01-01T00:00:00Z", "order_items": []}])
        assert rows == []

    def test_shipping_nao_dict(self) -> None:
        rows = orders_results_to_rows(
            [
                {
                    "id": 3,
                    "date_created": "2026-01-02T00:00:00Z",
                    "total_amount": 10,
                    "shipping": "x",
                    "order_items": [{"quantity": 1, "unit_price": 10, "item": {"title": "T"}}],
                }
            ]
        )
        assert rows[0]["envio_status"] == ""
        assert rows[0]["envio_id"] is None


class TestResumoPorPlataforma:
    def test_dataframe_vazio(self) -> None:
        out = resumo_por_plataforma(pd.DataFrame())
        assert list(out.columns) == [
            "plataforma",
            "pedidos_distintos",
            "faturamento_total_pedidos",
            "itens_vendidos_unidades",
            "receita_soma_linhas_itens",
            "ticket_medio_pedido",
        ]
        assert len(out) == 0

    def test_um_pedido_duas_linhas_nao_duplica_faturamento(
        self, order_dois_itens_mesmo_pedido: list[dict]
    ) -> None:
        df = pd.DataFrame(orders_results_to_rows(order_dois_itens_mesmo_pedido))
        out = resumo_por_plataforma(df)
        assert len(out) == 1
        row = out.iloc[0]
        assert row["pedidos_distintos"] == 1
        assert row["faturamento_total_pedidos"] == 300.0
        assert row["itens_vendidos_unidades"] == 3
        assert row["receita_soma_linhas_itens"] == 300.0
        assert row["ticket_medio_pedido"] == 300.0

    def test_duas_plataformas(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "plataforma": "meli",
                    "id_pedido": 1,
                    "total_pedido": 100.0,
                    "quantidade": 1,
                    "subtotal_linha_itens": 100.0,
                },
                {
                    "plataforma": "outra",
                    "id_pedido": 2,
                    "total_pedido": 50.0,
                    "quantidade": 2,
                    "subtotal_linha_itens": 50.0,
                },
            ]
        )
        out = resumo_por_plataforma(df)
        assert len(out) == 2
        by = out.set_index("plataforma")
        assert by.loc["meli", "faturamento_total_pedidos"] == 100.0
        assert by.loc["outra", "pedidos_distintos"] == 1


class TestTopItens:
    def test_vazio(self) -> None:
        assert top_itens(pd.DataFrame()).empty

    def test_ordena_por_receita(self, order_dois_itens_mesmo_pedido: list[dict]) -> None:
        df = pd.DataFrame(orders_results_to_rows(order_dois_itens_mesmo_pedido))
        out = top_itens(df, n=10)
        assert len(out) == 2
        assert out.iloc[0]["receita_total"] >= out.iloc[1]["receita_total"]
        assert out.iloc[0]["produto"] == "C"


class TestBuscarExtratoMeli:
    def test_erro_api_sem_resultados_acumulados(self) -> None:
        with patch("meli_export.fetch_orders_search", return_value=([], "USER_ID ausente no .env")):
            df, msg = buscar_extrato_meli(limit=10, max_pages=1)
            assert df.empty
            assert "USER_ID" in msg

    def test_sucesso_uma_pagina(self, order_um_item: list[dict]) -> None:
        with patch("meli_export.fetch_orders_search", return_value=(order_um_item, "Sucesso")):
            df, msg = buscar_extrato_meli(limit=50, max_pages=1)
            assert msg == "Sucesso"
            assert len(df) == 1
            assert df.iloc[0]["plataforma"] == "meli"


class TestExportarPasta:
    def test_grava_csvs_e_meta(self, order_um_item: list[dict], tmp_path: Path) -> None:
        with patch("meli_export.fetch_orders_search", return_value=(order_um_item, "Sucesso")):
            extrato, resumo, top, df, msg = exportar_pasta(tmp_path, limit=50, max_pages=1)
        assert msg == "Sucesso"
        assert len(df) == 1
        assert extrato.name == "meli_extrato_itens.csv"
        assert resumo.name == "meli_resumo_plataforma.csv"
        assert top.name == "meli_top_itens.csv"
        assert (tmp_path / "meli_export_meta.txt").is_file()
        assert extrato.read_text(encoding="utf-8-sig").splitlines()[0].startswith("plataforma")

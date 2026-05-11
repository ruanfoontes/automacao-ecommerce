"""Adaptador legado etl -> colunas do dashboard."""

from __future__ import annotations

from unittest.mock import patch

import etl
import pandas as pd


class TestBuscarDadosMeli:
    def test_renomeia_colunas_esperadas(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "data_pedido": "2026-05-01",
                    "produto": "X",
                    "preco_unitario": 10.0,
                    "quantidade": 2,
                    "id_pedido": 99,
                }
            ]
        )
        with patch.object(etl, "buscar_extrato_meli", return_value=(raw, "Sucesso")):
            df, msg = etl.buscar_dados_meli(limit=5, max_pages=1)

        assert msg == "Sucesso"
        assert list(df.columns) == ["Data", "Produto", "Preco_Unitario", "Quantidade", "ID_Ordem"]
        assert df.iloc[0]["Produto"] == "X"
        assert df.iloc[0]["ID_Ordem"] == 99
        assert df.iloc[0]["Quantidade"] == 2

import pandas as pd

from meli_export import buscar_extrato_meli

from meli_auth import ensure_dotenv_loaded

ensure_dotenv_loaded()


def buscar_dados_meli(*, limit: int = 50, max_pages: int = 1):
    """
    Compativel com dashboard antigo: colunas Data, Produto, Preco_Unitario, Quantidade, ID_Ordem.
    Dados vêm do mesmo extrato ML (orders/search) que meli_export.
    """
    try:
        df, msg = buscar_extrato_meli(limit=limit, max_pages=max_pages)
        if df.empty:
            return df, msg
        legado = df.rename(
            columns={
                "data_pedido": "Data",
                "produto": "Produto",
                "preco_unitario": "Preco_Unitario",
                "quantidade": "Quantidade",
                "id_pedido": "ID_Ordem",
            }
        )
        cols = ["Data", "Produto", "Preco_Unitario", "Quantidade", "ID_Ordem"]
        return legado[cols], msg
    except Exception as e:
        return pd.DataFrame(), str(e)
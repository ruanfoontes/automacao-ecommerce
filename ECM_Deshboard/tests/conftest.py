"""Fixtures compartilhadas (JSON no formato orders/search)."""


import pytest


@pytest.fixture
def order_um_item() -> list[dict]:
    return [
        {
            "id": 1001,
            "date_created": "2026-05-01T14:00:00.000-04:00",
            "status": "paid",
            "total_amount": 150.0,
            "currency_id": "BRL",
            "shipping": {"status": "ready_to_ship", "id": 555},
            "order_items": [
                {
                    "quantity": 2,
                    "unit_price": 75.0,
                    "item": {"id": "MLB1", "title": "Produto A"},
                }
            ],
        }
    ]


@pytest.fixture
def order_dois_itens_mesmo_pedido() -> list[dict]:
    return [
        {
            "id": 2002,
            "date_created": "2026-05-02T10:00:00.000-04:00",
            "status": "paid",
            "total_amount": 300.0,
            "currency_id": "BRL",
            "shipping": {},
            "order_items": [
                {
                    "quantity": 1,
                    "unit_price": 100.0,
                    "item": {"id": "MLB2", "title": "B"},
                },
                {
                    "quantity": 2,
                    "unit_price": 100.0,
                    "item": {"id": "MLB3", "title": "C"},
                },
            ],
        }
    ]

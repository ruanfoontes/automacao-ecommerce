import argparse
import os
from pathlib import Path
from typing import Optional

import pandas as pd

from etl import buscar_dados_meli
from meli_export import exportar_pasta, pasta_export_padraio, resumo_por_plataforma
from meli_auth import (
    build_authorize_url,
    ensure_dotenv_loaded,
    get_redirect_uri,
    login_with_authorization_code,
    meli_get,
    oauth_client_configured,
    refresh_and_persist,
    refresh_credentials_configured,
)
from testes_vendas import testar_conexao


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
    if refresh_credentials_configured():
        print("OK: credenciais de refresh OAuth (MELI_*) configuradas.")
    else:
        print(
            "Aviso: sem MELI_CLIENT_ID / MELI_CLIENT_SECRET / MELI_REFRESH_TOKEN "
            "nao ha renovacao automatica do ACCESS_TOKEN quando expira."
        )
        if oauth_client_configured():
            print("Dica: rode  oauth-url  e depois  exchange-code --code ...  para obter tokens novos.")
    return 0


def cmd_refresh_tokens() -> int:
    try:
        tokens = refresh_and_persist()
        exp = tokens.get("expires_in")
        if exp is not None:
            print(f"ACCESS_TOKEN atualizado com sucesso. expires_in≈{exp}s.")
        else:
            print("ACCESS_TOKEN atualizado com sucesso.")
        print("Valores também foram gravados no arquivo .env (ACCESS_TOKEN e MELI_REFRESH_TOKEN).")
        return 0
    except RuntimeError as exc:
        msg = str(exc)
        print(msg)
        if "401" in msg or "400" in msg or "invalid" in msg.lower():
            print("Se o refresh expirou, use: oauth-url  e  exchange-code --code SEU_CODE")
        return 1


def cmd_oauth_url() -> int:
    if not oauth_client_configured():
        print("[ERRO] Defina MELI_CLIENT_ID e MELI_CLIENT_SECRET no ECM_Deshboard/.env")
        print("  (painel: https://developers.mercadolivre.com.br/  -> sua aplicacao)")
        return 1
    rid = get_redirect_uri()
    try:
        url = build_authorize_url(rid)
    except RuntimeError as exc:
        print(f"[ERRO] {exc}")
        return 1
    print("1) No painel da aplicacao ML, cadastre esta Redirect URI (exatamente igual):")
    print(f"    {rid}")
    print("")
    print("2) Abra no navegador:")
    print(f"    {url}")
    print("")
    print("3) Apos logar e autorizar, o navegador redireciona para a Redirect URI.")
    print("    Copie o parametro  code=...  da URL (ou da barra de endereco).")
    print("")
    print("4) Rode:")
    print('    python ECM_Deshboard\\src\\main.py exchange-code --code "COLAR_CODE_AQUI"')
    return 0


def cmd_exchange_code(code: str, redirect_uri: Optional[str]) -> int:
    if not oauth_client_configured():
        print("[ERRO] Defina MELI_CLIENT_ID e MELI_CLIENT_SECRET no .env")
        return 1
    try:
        tokens = login_with_authorization_code(code, redirect_uri)
        uid = tokens.get("user_id") or "?"
        print(f"[OK] Tokens gravados no .env (ACCESS_TOKEN, MELI_REFRESH_TOKEN, USER_ID={uid}).")
        exp = tokens.get("expires_in")
        if exp is not None:
            print(f"expires_in aproximado: {exp}s")
        print("Teste: python ECM_Deshboard\\src\\main.py smoke")
        return 0
    except RuntimeError as exc:
        print(f"[ERRO] {exc}")
        return 1


def cmd_whoami() -> int:
    _require_env("ACCESS_TOKEN")
    url = "https://api.mercadolibre.com/users/me"

    resp = meli_get(url)
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
    return testar_conexao()


def cmd_fetch(*, limit: int = 50, max_pages: int = 1, show: int = 20, export_csv: Optional[str] = None) -> int:
    cmd_validate_env()

    df, mensagem = buscar_dados_meli(limit=limit, max_pages=max_pages)
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


def cmd_export_backlog(*, limit: int = 50, max_pages: int = 1, out_dir: Optional[str] = None) -> int:
    cmd_validate_env()
    try:
        dest = Path(out_dir) if out_dir else pasta_export_padraio()
        p1, p2, p3, df, _msg = exportar_pasta(dest, limit=limit, max_pages=max_pages)
        print("[OK] Export Mercado Livre (backlog) concluido.")
        print(f"  Extrato itens:     {p1}")
        print(f"  Resumo plataforma: {p2}")
        print(f"  Top itens:         {p3}")
        if not df.empty:
            print("")
            print(resumo_por_plataforma(df).to_string(index=False))
        return 0
    except RuntimeError as exc:
        print(f"[ERRO] {exc}")
        return 1


def main() -> int:
    ensure_dotenv_loaded()
    parser = argparse.ArgumentParser(description="Cabeça (main) para testar o projeto via terminal.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate-env", help="Verifica se ACCESS_TOKEN e USER_ID existem.")
    sub.add_parser(
        "refresh-tokens",
        help="Renova ACCESS_TOKEN com MELI_REFRESH_TOKEN e atualiza o .env.",
    )
    sub.add_parser(
        "oauth-url",
        help="Mostra URL de login ML (precisa MELI_CLIENT_ID/SECRET e Redirect URI cadastrada).",
    )
    p_ex = sub.add_parser(
        "exchange-code",
        help="Troca o authorization code por tokens e grava no .env.",
    )
    p_ex.add_argument("--code", required=True, help="Code retornado na Redirect URI apos autorizar.")
    p_ex.add_argument(
        "--redirect-uri",
        default=None,
        help="Mesma URI cadastrada na app (default: MELI_REDIRECT_URI ou http://127.0.0.1:8765/callback).",
    )
    sub.add_parser("whoami", help="Mostra id/nickname usando ACCESS_TOKEN (/users/me).")
    sub.add_parser("smoke", help="Teste rápido: valida env + consulta orders.")

    p_fetch = sub.add_parser("fetch", help="Baixa dados, calcula métricas e imprime/exporta.")
    p_fetch.add_argument("--limit", type=int, default=50, help="Pedidos por pagina na API (max tipico 50).")
    p_fetch.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Quantas paginas de pedidos buscar (offset = page * limit).",
    )
    p_fetch.add_argument("--show", type=int, default=20, help="Linhas para mostrar no terminal.")
    p_fetch.add_argument("--export-csv", default=None, help="Caminho para exportar CSV (opcional).")

    p_exp = sub.add_parser(
        "export-backlog",
        help="Gera CSVs ML: extrato por item, resumo por plataforma, top itens (pasta exports/).",
    )
    p_exp.add_argument("--limit", type=int, default=50, help="Pedidos por pagina (API).")
    p_exp.add_argument("--pages", type=int, default=1, help="Numero de paginas.")
    p_exp.add_argument(
        "--out-dir",
        default=None,
        help="Pasta de saida (default: ECM_Deshboard/exports/meli_DATA_HORA).",
    )

    args = parser.parse_args()

    if args.cmd == "validate-env":
        return cmd_validate_env()
    if args.cmd == "refresh-tokens":
        return cmd_refresh_tokens()
    if args.cmd == "oauth-url":
        return cmd_oauth_url()
    if args.cmd == "exchange-code":
        return cmd_exchange_code(args.code, args.redirect_uri)
    if args.cmd == "whoami":
        return cmd_whoami()
    if args.cmd == "smoke":
        return cmd_smoke()
    if args.cmd == "fetch":
        return cmd_fetch(
            limit=args.limit,
            max_pages=getattr(args, "pages", 1),
            show=args.show,
            export_csv=args.export_csv,
        )
    if args.cmd == "export-backlog":
        return cmd_export_backlog(
            limit=args.limit,
            max_pages=args.pages,
            out_dir=args.out_dir,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


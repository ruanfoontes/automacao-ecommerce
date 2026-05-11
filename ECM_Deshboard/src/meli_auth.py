"""
Mercado Libre: renovação de ACCESS_TOKEN via refresh_token (OAuth2).

Variáveis no .env (ECM_Deshboard/.env):
- ACCESS_TOKEN, USER_ID — já usados pelo projeto
- MELI_CLIENT_ID, MELI_CLIENT_SECRET, MELI_REFRESH_TOKEN — necessários para o refresh automático

Após cada refresh bem-sucedido, ACCESS_TOKEN e MELI_REFRESH_TOKEN são atualizados no mesmo .env.
"""
from __future__ import annotations

import os
import re
import urllib.parse
from pathlib import Path
from typing import Any, Mapping, Optional

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
# Brasil; sobrescreva com MELI_AUTH_BASE se sua app usar outro host regional.
AUTH_BASE_DEFAULT = "https://auth.mercadolivre.com.br"
REDIRECT_URI_DEFAULT = "http://127.0.0.1:8765/callback"


def _dotenv_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def ensure_dotenv_loaded() -> None:
    load_dotenv(_dotenv_path())


def refresh_credentials_configured() -> bool:
    ensure_dotenv_loaded()
    return all(
        os.getenv(k)
        for k in ("MELI_CLIENT_ID", "MELI_CLIENT_SECRET", "MELI_REFRESH_TOKEN")
    )


def oauth_client_configured() -> bool:
    """Só Client ID + Secret (para primeiro login / exchange-code)."""
    ensure_dotenv_loaded()
    return bool(os.getenv("MELI_CLIENT_ID") and os.getenv("MELI_CLIENT_SECRET"))


def get_redirect_uri() -> str:
    ensure_dotenv_loaded()
    return (os.getenv("MELI_REDIRECT_URI") or REDIRECT_URI_DEFAULT).strip()


def get_auth_base() -> str:
    ensure_dotenv_loaded()
    return (os.getenv("MELI_AUTH_BASE") or AUTH_BASE_DEFAULT).rstrip("/")


def build_authorize_url(redirect_uri: str, *, state: str = "") -> str:
    ensure_dotenv_loaded()
    client_id = os.getenv("MELI_CLIENT_ID")
    if not client_id:
        raise RuntimeError("Defina MELI_CLIENT_ID no .env (ID da aplicacao no painel de desenvolvedores).")
    # Escopos: offline_access costuma ser necessario para receber refresh_token.
    scope_default = "offline_access read write"
    scope = (os.getenv("MELI_OAUTH_SCOPE") or scope_default).strip()

    params: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    if scope:
        params["scope"] = scope
    if state:
        params["state"] = state
    q = urllib.parse.urlencode(params)
    return f"{get_auth_base()}/authorization?{q}"


def fetch_user_id(access_token: str) -> Optional[str]:
    url = "https://api.mercadolibre.com/users/me"
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if r.status_code != 200:
        return None
    uid = r.json().get("id")
    return str(uid) if uid is not None else None


def exchange_authorization_code(code: str, redirect_uri: str) -> dict[str, Any]:
    ensure_dotenv_loaded()
    client_id = os.getenv("MELI_CLIENT_ID")
    client_secret = os.getenv("MELI_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Defina MELI_CLIENT_ID e MELI_CLIENT_SECRET no .env para trocar o code por tokens."
        )
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code.strip(),
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Falha ao trocar code por token ({resp.status_code}): {detail}")

    payload = resp.json()
    access = payload.get("access_token")
    if not access:
        raise RuntimeError(f"Resposta sem access_token: {payload}")
    refresh = payload.get("refresh_token")
    if not refresh:
        raise RuntimeError(
            "Resposta sem refresh_token. No painel da app, autorize com escopo que permita "
            "token de longa duracao (ex.: offline_access, conforme documentacao ML) e tente de novo."
        )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": payload.get("expires_in"),
        "user_id": payload.get("user_id"),
    }


def persist_oauth_tokens(
    access_token: str,
    refresh_token: str,
    *,
    user_id: Optional[str] = None,
) -> None:
    """Grava ACCESS_TOKEN, MELI_REFRESH_TOKEN e opcionalmente USER_ID no .env."""
    path = _dotenv_path()
    if not path.is_file():
        raise FileNotFoundError(f".env nao encontrado em: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    text = _rewrite_dotenv_key(text, "ACCESS_TOKEN", access_token)
    text = _rewrite_dotenv_key(text, "MELI_REFRESH_TOKEN", refresh_token)
    if user_id:
        text = _rewrite_dotenv_key(text, "USER_ID", user_id)
    path.write_text(text, encoding="utf-8")

    os.environ["ACCESS_TOKEN"] = access_token
    os.environ["MELI_REFRESH_TOKEN"] = refresh_token
    if user_id:
        os.environ["USER_ID"] = user_id


def login_with_authorization_code(code: str, redirect_uri: Optional[str] = None) -> dict[str, Any]:
    """Troca authorization code por tokens e atualiza o .env."""
    rid = redirect_uri or get_redirect_uri()
    tokens = exchange_authorization_code(code, rid)
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    uid = tokens.get("user_id")
    if uid is not None:
        uid = str(uid)
    else:
        uid = fetch_user_id(access)
    persist_oauth_tokens(access, refresh, user_id=uid)
    tokens["user_id"] = uid
    return tokens


def _rewrite_dotenv_key(content: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    line = f"{key}={value}"
    if pattern.search(content):
        return pattern.sub(line, content, count=1)
    nl = "\n" if content and not content.endswith("\n") else ""
    prefix = nl if content else ""
    return f"{content}{prefix}{line}\n"


def persist_tokens(access_token: str, refresh_token: Optional[str] = None) -> None:
    path = _dotenv_path()
    if not path.is_file():
        raise FileNotFoundError(f".env não encontrado em: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    text = _rewrite_dotenv_key(text, "ACCESS_TOKEN", access_token)
    if refresh_token:
        text = _rewrite_dotenv_key(text, "MELI_REFRESH_TOKEN", refresh_token)
    path.write_text(text, encoding="utf-8")

    os.environ["ACCESS_TOKEN"] = access_token
    if refresh_token:
        os.environ["MELI_REFRESH_TOKEN"] = refresh_token


def exchange_refresh_token() -> dict[str, Any]:
    ensure_dotenv_loaded()
    client_id = os.getenv("MELI_CLIENT_ID")
    client_secret = os.getenv("MELI_CLIENT_SECRET")
    refresh_token = os.getenv("MELI_REFRESH_TOKEN")
    if not client_id or not client_secret or not refresh_token:
        raise RuntimeError(
            "Defina MELI_CLIENT_ID, MELI_CLIENT_SECRET e MELI_REFRESH_TOKEN no .env para renovar o token."
        )

    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Falha ao renovar token ({resp.status_code}): {detail}")

    payload = resp.json()
    access = payload.get("access_token")
    if not access:
        raise RuntimeError(f"Resposta sem access_token: {payload}")
    new_refresh = payload.get("refresh_token") or refresh_token
    return {"access_token": access, "refresh_token": new_refresh, "expires_in": payload.get("expires_in")}


def refresh_and_persist() -> dict[str, Any]:
    tokens = exchange_refresh_token()
    persist_tokens(tokens["access_token"], tokens["refresh_token"])
    return tokens


def meli_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """
    Chamada HTTP com Bearer do .env.
    Em 401, tenta um refresh (se configurado), atualiza ACCESS_TOKEN/MELI_REFRESH_TOKEN no .env e repete 1 vez.
    """
    ensure_dotenv_loaded()
    timeout = kwargs.pop("timeout", 30)
    headers = dict(kwargs.pop("headers", None) or {})

    token = os.getenv("ACCESS_TOKEN")
    if not token:
        raise RuntimeError("ACCESS_TOKEN ausente no ambiente.")
    headers.setdefault("Authorization", f"Bearer {token}")

    def send(h: Mapping[str, str]) -> requests.Response:
        return requests.request(method, url, headers=dict(h), timeout=timeout, **kwargs)

    resp = send(headers)
    if resp.status_code != 401 or not refresh_credentials_configured():
        return resp

    try:
        refresh_and_persist()
    except Exception:
        return resp

    headers["Authorization"] = f"Bearer {os.environ['ACCESS_TOKEN']}"
    return send(headers)


def meli_get(url: str, **kwargs: Any) -> requests.Response:
    return meli_request("GET", url, **kwargs)

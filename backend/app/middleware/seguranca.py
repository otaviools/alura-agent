"""Preocupacoes transversais de seguranca aplicadas a todas as requisicoes.

Cobre os cabecalhos HTTP de seguranca, a verificacao do token de
protecao contra CSRF e a identificacao da sessao e do IP de origem.
"""

import secrets

from flask import request

from app.models.documento import Sessao
from app.services import sessao_service
from app.utils.erros import ErroAutorizacao

CABECALHO_SESSAO = "X-Sessao"
CABECALHO_PROTECAO = "X-Token-Protecao"

# A API so devolve JSON e nunca renderiza HTML: a politica mais restritiva
# possivel e a correta aqui. O front-end tem a propria politica no Nuxt.
CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
    "Cache-Control": "no-store",
}


def aplicar_cabecalhos(resposta):
    """Adiciona os cabecalhos de seguranca a qualquer resposta da API."""
    for nome, valor in CABECALHOS_SEGURANCA.items():
        resposta.headers.setdefault(nome, valor)
    resposta.headers.pop("Server", None)
    return resposta


def ip_do_cliente() -> str:
    """Descobre o IP de origem, respeitando o proxy reverso quando houver."""
    encaminhado = request.headers.get("X-Forwarded-For", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.remote_addr or "desconhecido"


def identificador_da_sessao() -> str:
    """Le o identificador de sessao enviado pelo front-end."""
    return (request.headers.get(CABECALHO_SESSAO) or "").strip()


def sessao_atual() -> Sessao:
    """Recupera a sessao da requisicao; levanta ErroSessao se nao houver."""
    return sessao_service.obter_sessao(identificador_da_sessao())


def exigir_token_protecao(sessao: Sessao) -> None:
    """Confere o token de protecao em operacoes que alteram estado.

    O token e emitido junto com a sessao e viaja em cabecalho proprio, o que
    impede que uma pagina de terceiros dispare a operacao em nome do usuario.
    """
    enviado = (request.headers.get(CABECALHO_PROTECAO) or "").strip()
    if not enviado or not secrets.compare_digest(enviado, sessao.token_protecao):
        raise ErroAutorizacao("Requisicao sem autorizacao valida. Recarregue a pagina.")

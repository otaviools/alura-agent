"""Rotas da conversa com o agente.

A resposta do agente e entregue em streaming (Server-Sent Events) para que o
texto apareca na tela conforme e gerado, em vez de esperar a resposta inteira.
"""

import json

from flask import Blueprint, Response, jsonify, request

from app.config import Config
from app.middleware.limites import limitador
from app.middleware.seguranca import (
    exigir_token_protecao,
    ip_do_cliente,
    sessao_atual,
)
from app.services import agente_service, sessao_service
from app.utils.erros import ErroSessao, ErroValidacao
from app.utils.log import registrar_auditoria

conversas_bp = Blueprint("conversas", __name__)


@conversas_bp.get("/api/mensagens")
def listar_mensagens():
    """Devolve o historico da conversa da sessao atual."""
    sessao = sessao_atual()
    return jsonify({"mensagens": [item.para_json() for item in sessao.mensagens]}), 200


@conversas_bp.post("/api/mensagens")
@limitador.limit(Config.LIMITE_MENSAGENS)
def enviar_mensagem():
    """Recebe a pergunta e devolve a resposta do agente em streaming."""
    sessao = sessao_atual()
    exigir_token_protecao(sessao)

    if sessao.documento is None:
        raise ErroSessao("Envie um PDF antes de fazer perguntas.")

    corpo = request.get_json(silent=True) or {}
    pergunta = _validar_pergunta(corpo.get("pergunta"))

    ip = ip_do_cliente()
    registrar_auditoria(
        "pergunta_recebida",
        sessao.identificador,
        ip,
        caracteres=len(pergunta),
    )

    def transmitir():
        """Gera os eventos SSE consumidos pelo front-end."""
        resposta_final = ""
        houve_erro = False
        for evento in agente_service.responder_em_streaming(sessao, pergunta):
            if evento["tipo"] == "fim":
                resposta_final = evento["resposta"]
            elif evento["tipo"] == "erro":
                houve_erro = True
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"

        if resposta_final:
            # O historico so e gravado quando ha resposta completa, para nao
            # deixar perguntas orfas na conversa.
            sessao_service.registrar_mensagem(sessao, "usuario", pergunta)
            sessao_service.registrar_mensagem(sessao, "agente", resposta_final)
        registrar_auditoria(
            "resposta_concluida",
            sessao.identificador,
            ip,
            caracteres=len(resposta_final),
            erro=houve_erro,
        )

    return Response(
        transmitir(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
            # Impede que proxies segurem o corpo ate o fim da resposta.
            "X-Accel-Buffering": "no",
        },
    )


def _validar_pergunta(valor) -> str:
    """Valida o texto da pergunta no back-end, nunca so no front."""
    if not isinstance(valor, str):
        raise ErroValidacao("A pergunta precisa ser um texto.")
    pergunta = valor.strip()
    if not pergunta:
        raise ErroValidacao("Escreva uma pergunta antes de enviar.")
    if len(pergunta) > Config.PERGUNTA_MAXIMA_CARACTERES:
        raise ErroValidacao(
            f"A pergunta passa do limite de {Config.PERGUNTA_MAXIMA_CARACTERES} caracteres."
        )
    return pergunta

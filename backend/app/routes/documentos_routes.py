"""Rotas de sessao e de documento.

As rotas sao finas de proposito: validam o basico, delegam aos services e
montam a resposta. A regra de negocio fica nos services.
"""

from flask import Blueprint, current_app, jsonify, request

from app.config import Config
from app.middleware.limites import limitador
from app.middleware.seguranca import (
    exigir_token_protecao,
    ip_do_cliente,
    sessao_atual,
)
from app.services import pdf_service, sessao_service
from app.utils.erros import ErroArquivo, ErroValidacao
from app.utils.log import registrar_auditoria

documentos_bp = Blueprint("documentos", __name__)

CAMPO_ARQUIVO = "arquivo"


@documentos_bp.post("/api/sessoes")
@limitador.limit(Config.LIMITE_SESSOES)
def criar_sessao():
    """Abre uma sessao de trabalho e devolve seus tokens."""
    sessao = sessao_service.criar_sessao()
    registrar_auditoria("sessao_criada", sessao.identificador, ip_do_cliente())
    return (
        jsonify(
            {
                "sessaoId": sessao.identificador,
                "tokenProtecao": sessao.token_protecao,
                "expiraEmMinutos": Config.SESSAO_TTL_MINUTOS,
            }
        ),
        201,
    )


@documentos_bp.post("/api/documentos")
@limitador.limit(Config.LIMITE_UPLOAD)
def enviar_documento():
    """Recebe o PDF, valida, extrai o texto e prende o resultado a sessao."""
    sessao = sessao_atual()
    exigir_token_protecao(sessao)

    if CAMPO_ARQUIVO not in request.files:
        raise ErroValidacao("Nenhum arquivo foi enviado.")

    enviado = request.files[CAMPO_ARQUIVO]
    if not enviado.filename:
        raise ErroValidacao("Selecione um arquivo antes de enviar.")

    conteudo = enviado.read()
    documento = pdf_service.processar_upload(enviado.filename, conteudo)

    sessao.limpar_documento()
    sessao.documento = documento
    sessao.tocar()

    registrar_auditoria(
        "documento_carregado",
        sessao.identificador,
        ip_do_cliente(),
        paginas=documento.total_paginas,
        bytes=documento.tamanho_bytes,
        com_texto=documento.paginas_com_texto,
    )

    resposta = documento.para_json()
    if not documento.possui_texto:
        resposta["aviso"] = (
            "Este PDF nao tem texto extraivel. Provavelmente e um documento "
            "escaneado como imagem, e o Docsy nao faz reconhecimento optico."
        )
    return jsonify(resposta), 201


@documentos_bp.get("/api/documentos")
def obter_documento():
    """Devolve os metadados do documento carregado na sessao."""
    sessao = sessao_atual()
    if sessao.documento is None:
        return jsonify({"documento": None}), 200
    return jsonify(sessao.documento.para_json()), 200


@documentos_bp.delete("/api/documentos")
def remover_documento():
    """Descarta documento e historico da memoria do servidor."""
    sessao = sessao_atual()
    exigir_token_protecao(sessao)
    sessao.limpar_documento()
    registrar_auditoria("documento_removido", sessao.identificador, ip_do_cliente())
    return jsonify({"removido": True}), 200


@documentos_bp.errorhandler(413)
def arquivo_grande_demais(_erro):
    """Traduz o corte do Flask por tamanho em mensagem do dominio."""
    current_app.logger.info("upload rejeitado por tamanho")
    erro = ErroArquivo(f"O arquivo passa do limite de {Config.TAMANHO_MAXIMO_MB} MB.")
    return jsonify({"erro": erro.codigo, "mensagem": erro.mensagem}), 413

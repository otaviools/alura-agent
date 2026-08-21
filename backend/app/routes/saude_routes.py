"""Rota de verificacao de saude do servico."""

from flask import Blueprint, jsonify

from app.config import Config
from app.services import sessao_service

saude_bp = Blueprint("saude", __name__)


@saude_bp.get("/api/saude")
def verificar_saude():
    """Informa se a API esta no ar e se o agente esta configurado."""
    return jsonify(
        {
            "status": "ok",
            "agenteConfigurado": Config.chave_configurada(),
            "modelo": Config.MODELO,
            "sessoesAtivas": sessao_service.total_de_sessoes(),
            "limites": {
                "tamanhoMaximoMb": Config.TAMANHO_MAXIMO_MB,
                "paginasMaximas": Config.PAGINAS_MAXIMAS,
                "perguntaMaximaCaracteres": Config.PERGUNTA_MAXIMA_CARACTERES,
                "sessaoTtlMinutos": Config.SESSAO_TTL_MINUTOS,
            },
        }
    )

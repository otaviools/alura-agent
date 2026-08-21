"""Registro de eventos e trilha de auditoria.

Regra central: o log registra QUEM (sessao e IP), O QUE (acao) e o resultado.
Nunca registra o conteudo do documento nem o texto das perguntas do usuario.
"""

import logging
import sys

_FORMATO = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

logger = logging.getLogger("docsy")


def configurar_log(nivel: str = "INFO") -> None:
    """Configura a saida de log da aplicacao uma unica vez."""
    if logger.handlers:
        return
    manipulador = logging.StreamHandler(sys.stdout)
    manipulador.setFormatter(logging.Formatter(_FORMATO))
    logger.addHandler(manipulador)
    logger.setLevel(getattr(logging, nivel.upper(), logging.INFO))
    logger.propagate = False


def registrar_auditoria(acao: str, sessao_id: str, ip: str, **detalhes) -> None:
    """Registra uma acao sensivel com identificacao de sessao e IP.

    Os detalhes aceitos sao apenas metadados (tamanho, paginas, codigo de erro).
    Nao passe conteudo de documento nem texto digitado pelo usuario.
    """
    extras = " ".join(f"{chave}={valor}" for chave, valor in detalhes.items())
    logger.info("acao=%s sessao=%s ip=%s %s", acao, _mascarar(sessao_id), ip, extras)


def _mascarar(sessao_id: str) -> str:
    """Reduz o identificador de sessao no log, o suficiente para correlacionar."""
    if not sessao_id:
        return "-"
    return f"{sessao_id[:8]}..."

"""Guarda as sessoes de trabalho na memoria do processo.

Nao existe banco de dados: este modulo e o unico lugar onde documento e
historico de conversa vivem. Tudo expira por inatividade e some quando o
servidor reinicia, o que e intencional (ver PLANEJAMENTO.md, secao Dados).
"""

import secrets
import threading
from datetime import datetime, timedelta, timezone

from app.config import Config
from app.models.documento import Mensagem, Sessao
from app.utils.erros import ErroSessao

_sessoes: dict[str, Sessao] = {}
_trava = threading.Lock()


def criar_sessao() -> Sessao:
    """Cria uma sessao vazia com identificador e token de protecao proprios."""
    with _trava:
        _remover_expiradas()
        _respeitar_limite()
        sessao = Sessao(
            identificador=secrets.token_urlsafe(24),
            token_protecao=secrets.token_urlsafe(24),
        )
        _sessoes[sessao.identificador] = sessao
        return sessao


def obter_sessao(identificador: str) -> Sessao:
    """Recupera uma sessao valida ou levanta ErroSessao."""
    if not identificador:
        raise ErroSessao("Sessao nao informada. Recarregue a pagina e envie o arquivo novamente.")
    with _trava:
        _remover_expiradas()
        sessao = _sessoes.get(identificador)
        if sessao is None:
            raise ErroSessao("Sua sessao expirou. Recarregue a pagina e envie o arquivo novamente.")
        sessao.tocar()
        return sessao


def encerrar_sessao(identificador: str) -> None:
    """Remove a sessao e tudo que ela guardava."""
    with _trava:
        sessao = _sessoes.pop(identificador, None)
        if sessao is not None:
            sessao.limpar_documento()


def registrar_mensagem(sessao: Sessao, autor: str, texto: str) -> Mensagem:
    """Adiciona uma fala ao historico, respeitando o limite configurado."""
    mensagem = Mensagem(autor=autor, texto=texto)
    with _trava:
        sessao.mensagens.append(mensagem)
        excedente = len(sessao.mensagens) - Config.MENSAGENS_MAXIMAS_HISTORICO
        if excedente > 0:
            del sessao.mensagens[:excedente]
        sessao.tocar()
    return mensagem


def total_de_sessoes() -> int:
    """Quantidade de sessoes ativas — usado pelo endpoint de saude."""
    with _trava:
        _remover_expiradas()
        return len(_sessoes)


def limpar_tudo() -> None:
    """Zera o armazenamento. Usado pelos testes."""
    with _trava:
        _sessoes.clear()


def _remover_expiradas() -> None:
    """Descarta sessoes inativas alem do TTL. Deve ser chamada com a trava."""
    limite = datetime.now(timezone.utc) - timedelta(minutes=Config.SESSAO_TTL_MINUTOS)
    expiradas = [chave for chave, sessao in _sessoes.items() if sessao.ultimo_acesso < limite]
    for chave in expiradas:
        sessao = _sessoes.pop(chave)
        sessao.limpar_documento()


def _respeitar_limite() -> None:
    """Evita crescimento indefinido da memoria descartando a sessao mais antiga."""
    while len(_sessoes) >= Config.SESSOES_MAXIMAS:
        mais_antiga = min(_sessoes.values(), key=lambda item: item.ultimo_acesso)
        _sessoes.pop(mais_antiga.identificador, None)
        mais_antiga.limpar_documento()

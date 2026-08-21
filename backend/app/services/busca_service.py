"""Busca por palavras dentro do documento, usando BM25.

A busca roda inteiramente no servidor, sem servico externo e sem embeddings:
o agente usa esta funcao como ferramenta para achar as paginas relevantes antes
de responder.
"""

import re
import unicodedata

from rank_bm25 import BM25Okapi

from app.models.documento import Documento, Trecho

def _sem_acento(texto: str) -> str:
    """Remove acentos, para comparar palavras de forma estavel."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(letra for letra in decomposto if not unicodedata.combining(letra))


# Palavras muito frequentes em portugues, que so adicionam ruido ao ranking.
# O conjunto e normalizado sem acento porque a tokenizacao tambem remove acentos.
PALAVRAS_IGNORADAS = {
    _sem_acento(palavra)
    for palavra in (
        "a ao aos as com como da das de do dos e em entre essa esse esta este "
        "eu foi há isso já la lhe mais mas me mesmo meu muito na nas não no "
        "nos o os ou para pela pelo por qual quando que quem se sem ser seu "
        "sobre sua tem um uma você à às é"
    ).split()
}


class IndiceDocumento:
    """Indice BM25 construido sobre os trechos de um documento."""

    def __init__(self, documento: Documento):
        self._trechos: list[Trecho] = documento.trechos
        corpus = [_tokenizar(trecho.texto) for trecho in self._trechos]
        # BM25Okapi rejeita corpus vazio; documentos sem texto ficam sem indice.
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def buscar(self, consulta: str, limite: int = 6) -> list[Trecho]:
        """Devolve os trechos mais relevantes para a consulta, do maior ao menor."""
        if self._bm25 is None:
            return []
        termos = _tokenizar(consulta)
        if not termos:
            # Sem termos uteis, devolve o inicio do documento como contexto.
            return self._trechos[:limite]
        pontuacoes = list(self._bm25.get_scores(termos))
        # Em documentos muito curtos o BM25 zera ou inverte as pontuacoes: com
        # poucos trechos, um termo presente em quase todos recebe peso negativo.
        # Nesse caso a contagem de termos distintos e mais confiavel.
        if max(pontuacoes, default=0) <= 0:
            pontuacoes = self._pontuar_por_sobreposicao(termos)

        ordenados = sorted(
            zip(pontuacoes, self._trechos),
            key=lambda par: par[0],
            reverse=True,
        )
        return [trecho for pontuacao, trecho in ordenados[:limite] if pontuacao > 0]

    def _pontuar_por_sobreposicao(self, termos: list[str]) -> list[float]:
        """Conta quantos termos distintos da consulta aparecem em cada trecho."""
        procurados = set(termos)
        return [
            float(len(procurados & set(_tokenizar(trecho.texto))))
            for trecho in self._trechos
        ]


def _tokenizar(texto: str) -> list[str]:
    """Normaliza acentos, caixa e pontuacao, removendo palavras sem peso."""
    palavras = re.findall(r"[a-z0-9]+", _sem_acento(texto))
    return [palavra for palavra in palavras if palavra not in PALAVRAS_IGNORADAS and len(palavra) > 1]

"""Estruturas de dados mantidas em memoria.

O Docsy nao possui banco de dados: estas classes descrevem o estado que vive
apenas no processo do servidor, preso a uma sessao, e e descartado na troca de
documento, na remocao ou por inatividade.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _agora() -> datetime:
    """Horario atual em UTC (convertido para exibicao no front-end)."""
    return datetime.now(timezone.utc)


@dataclass
class Pagina:
    """Texto extraido de uma pagina do PDF."""

    numero: int
    texto: str

    @property
    def possui_texto(self) -> bool:
        return bool(self.texto.strip())


@dataclass
class Trecho:
    """Pedaco indexavel de uma pagina, usado na busca por palavras."""

    pagina: int
    ordem: int
    texto: str


@dataclass
class Documento:
    """PDF carregado em uma sessao."""

    nome_arquivo: str
    tamanho_bytes: int
    total_paginas: int
    paginas: list[Pagina]
    trechos: list[Trecho]
    criado_em: datetime = field(default_factory=_agora)

    @property
    def total_caracteres(self) -> int:
        return sum(len(pagina.texto) for pagina in self.paginas)

    @property
    def paginas_com_texto(self) -> int:
        return sum(1 for pagina in self.paginas if pagina.possui_texto)

    @property
    def possui_texto(self) -> bool:
        return self.paginas_com_texto > 0

    def texto_da_pagina(self, numero: int) -> str | None:
        """Devolve o texto de uma pagina pelo numero, ou None se nao existir."""
        for pagina in self.paginas:
            if pagina.numero == numero:
                return pagina.texto
        return None

    def para_json(self) -> dict:
        """Metadados seguros para envio ao front-end (sem o conteudo)."""
        return {
            "nomeArquivo": self.nome_arquivo,
            "tamanhoBytes": self.tamanho_bytes,
            "totalPaginas": self.total_paginas,
            "paginasComTexto": self.paginas_com_texto,
            "totalCaracteres": self.total_caracteres,
            "possuiTexto": self.possui_texto,
            "criadoEm": self.criado_em.isoformat(),
        }


@dataclass
class Mensagem:
    """Uma fala da conversa: pergunta do usuario ou resposta do agente."""

    autor: str  # "usuario" ou "agente"
    texto: str
    criado_em: datetime = field(default_factory=_agora)

    def para_json(self) -> dict:
        return {
            "autor": self.autor,
            "texto": self.texto,
            "criadoEm": self.criado_em.isoformat(),
        }


@dataclass
class Sessao:
    """Sessao de trabalho: um documento e o historico da conversa."""

    identificador: str
    token_protecao: str
    documento: Documento | None = None
    mensagens: list[Mensagem] = field(default_factory=list)
    criada_em: datetime = field(default_factory=_agora)
    ultimo_acesso: datetime = field(default_factory=_agora)

    def tocar(self) -> None:
        """Marca a sessao como usada agora, adiando a expiracao."""
        self.ultimo_acesso = _agora()

    def limpar_documento(self) -> None:
        """Descarta documento e historico da memoria."""
        self.documento = None
        self.mensagens = []

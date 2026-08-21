"""Erros de dominio do Docsy.

Cada erro carrega uma mensagem ja pronta para o usuario final, sem detalhe
tecnico. Stack trace e detalhe interno ficam so no log do servidor.
"""


class ErroDocsy(Exception):
    """Erro previsto, com mensagem segura para exibicao ao usuario."""

    codigo_http = 400
    codigo = "erro_generico"

    def __init__(self, mensagem: str, codigo: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo


class ErroValidacao(ErroDocsy):
    """Entrada do usuario invalida."""

    codigo_http = 400
    codigo = "validacao"


class ErroArquivo(ErroDocsy):
    """Arquivo enviado nao pode ser processado."""

    codigo_http = 400
    codigo = "arquivo_invalido"


class ErroSessao(ErroDocsy):
    """Sessao inexistente, expirada ou sem documento carregado."""

    codigo_http = 404
    codigo = "sessao_invalida"


class ErroAutorizacao(ErroDocsy):
    """Token de protecao ausente ou incorreto."""

    codigo_http = 403
    codigo = "nao_autorizado"


class ErroAgente(ErroDocsy):
    """Falha ao consultar o servico de IA."""

    codigo_http = 502
    codigo = "agente_indisponivel"

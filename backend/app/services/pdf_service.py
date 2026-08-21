"""Validacao e leitura de arquivos PDF com pdfplumber.

A escolha do pdfplumber esta justificada no PLANEJAMENTO.md: e a melhor
extracao de texto disponivel sob licenca permissiva (MIT), sem a amarra de
copyleft de rede da AGPL. Toda validacao aqui roda no back-end, nunca so no
front — o navegador pode ser contornado.
"""

import io
import re

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from app.config import Config
from app.models.documento import Documento, Pagina, Trecho
from app.utils.erros import ErroArquivo

ASSINATURA_PDF = b"%PDF-"
TAMANHO_TRECHO = 1200
_ESPACOS = re.compile(r"[ \t ]+")
_LINHAS_VAZIAS = re.compile(r"\n{3,}")


def processar_upload(nome_arquivo: str, conteudo: bytes) -> Documento:
    """Valida o arquivo enviado e devolve o documento com o texto extraido."""
    _validar_arquivo(nome_arquivo, conteudo)
    paginas = _extrair_paginas(conteudo)
    trechos = _dividir_em_trechos(paginas)
    return Documento(
        nome_arquivo=_sanear_nome(nome_arquivo),
        tamanho_bytes=len(conteudo),
        total_paginas=len(paginas),
        paginas=paginas,
        trechos=trechos,
    )


def _validar_arquivo(nome_arquivo: str, conteudo: bytes) -> None:
    """Confere extensao, assinatura real do arquivo e tamanho."""
    if not conteudo:
        raise ErroArquivo("O arquivo chegou vazio. Selecione um PDF e tente de novo.")

    if not nome_arquivo.lower().endswith(".pdf"):
        raise ErroArquivo("Envie um arquivo com extensao .pdf.")

    # Nao confiamos na extensao: a assinatura real do arquivo precisa bater.
    if not conteudo.startswith(ASSINATURA_PDF):
        raise ErroArquivo("Este arquivo nao e um PDF valido, mesmo que o nome termine em .pdf.")

    if len(conteudo) > Config.MAX_CONTENT_LENGTH:
        raise ErroArquivo(
            f"O arquivo passa do limite de {Config.TAMANHO_MAXIMO_MB} MB."
        )


def _extrair_paginas(conteudo: bytes) -> list[Pagina]:
    """Le o PDF pagina a pagina, preservando o numero de cada uma."""
    try:
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            if len(pdf.pages) > Config.PAGINAS_MAXIMAS:
                raise ErroArquivo(
                    f"O documento tem {len(pdf.pages)} paginas e o limite e "
                    f"{Config.PAGINAS_MAXIMAS}."
                )
            paginas = []
            for indice, pagina_pdf in enumerate(pdf.pages, start=1):
                texto = pagina_pdf.extract_text(x_tolerance=1.5) or ""
                paginas.append(Pagina(numero=indice, texto=_normalizar(texto)))
            return paginas
    except ErroArquivo:
        raise
    except PDFPasswordIncorrect as erro:
        raise ErroArquivo(
            "Este PDF esta protegido por senha. Remova a protecao e envie de novo."
        ) from erro
    except Exception as erro:  # arquivo corrompido ou estrutura ilegivel
        raise ErroArquivo(
            "Nao foi possivel ler este PDF. Ele pode estar corrompido."
        ) from erro


def _dividir_em_trechos(paginas: list[Pagina]) -> list[Trecho]:
    """Quebra cada pagina em trechos menores para a busca por palavras."""
    trechos: list[Trecho] = []
    for pagina in paginas:
        if not pagina.possui_texto:
            continue
        for ordem, texto in enumerate(_quebrar(pagina.texto), start=1):
            trechos.append(Trecho(pagina=pagina.numero, ordem=ordem, texto=texto))
    return trechos


def _quebrar(texto: str) -> list[str]:
    """Divide um texto longo em blocos, cortando em quebras de paragrafo."""
    if len(texto) <= TAMANHO_TRECHO:
        return [texto]

    blocos: list[str] = []
    atual: list[str] = []
    tamanho = 0
    for paragrafo in texto.split("\n"):
        if tamanho + len(paragrafo) > TAMANHO_TRECHO and atual:
            blocos.append("\n".join(atual))
            atual, tamanho = [], 0
        atual.append(paragrafo)
        tamanho += len(paragrafo) + 1
    if atual:
        blocos.append("\n".join(atual))
    return blocos


def _normalizar(texto: str) -> str:
    """Compacta espacos e linhas em branco sem perder a estrutura do texto."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = _ESPACOS.sub(" ", texto)
    texto = _LINHAS_VAZIAS.sub("\n\n", texto)
    return texto.strip()


def _sanear_nome(nome_arquivo: str) -> str:
    """Remove caminho e caracteres perigosos do nome exibido na interface."""
    nome = nome_arquivo.replace("\\", "/").split("/")[-1]
    nome = re.sub(r"[^\w\s.\-()\[\]]", "", nome, flags=re.UNICODE).strip()
    return nome[:120] or "documento.pdf"

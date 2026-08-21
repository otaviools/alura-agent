"""Configuracao da aplicacao, carregada de variaveis de ambiente."""

import os

from dotenv import load_dotenv

load_dotenv()


def _inteiro(nome: str, padrao: int) -> int:
    """Le uma variavel de ambiente inteira, caindo no padrao quando invalida."""
    try:
        return int(os.getenv(nome, padrao))
    except (TypeError, ValueError):
        return padrao


class Config:
    """Parametros de execucao do Docsy."""

    # --- Servidor ---
    HOST = os.getenv("DOCSY_HOST", "127.0.0.1")
    PORTA = _inteiro("DOCSY_PORTA", 5000)
    # Debug fica desligado por padrao: o modo debug do Flask expoe um console
    # que executa codigo arbitrario no servidor.
    DEBUG = os.getenv("DOCSY_DEBUG", "false").lower() == "true"

    # --- Limites de upload e de entrada ---
    TAMANHO_MAXIMO_MB = _inteiro("DOCSY_TAMANHO_MAXIMO_MB", 20)
    MAX_CONTENT_LENGTH = TAMANHO_MAXIMO_MB * 1024 * 1024
    PAGINAS_MAXIMAS = _inteiro("DOCSY_PAGINAS_MAXIMAS", 300)
    PERGUNTA_MAXIMA_CARACTERES = _inteiro("DOCSY_PERGUNTA_MAXIMA_CARACTERES", 2000)
    MENSAGENS_MAXIMAS_HISTORICO = _inteiro("DOCSY_MENSAGENS_MAXIMAS_HISTORICO", 40)

    # --- Sessao em memoria ---
    SESSAO_TTL_MINUTOS = _inteiro("DOCSY_SESSAO_TTL_MINUTOS", 60)
    SESSOES_MAXIMAS = _inteiro("DOCSY_SESSOES_MAXIMAS", 200)

    # --- Modelo de IA (Google Gemini) ---
    # Aceita GOOGLE_API_KEY ou o nome antigo GEMINI_API_KEY, o que existir.
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    MODELO = os.getenv("DOCSY_MODELO", "gemini-flash-lite-latest")
    MODELO_MAX_TOKENS = _inteiro("DOCSY_MODELO_MAX_TOKENS", 8000)
    TRECHOS_POR_BUSCA = _inteiro("DOCSY_TRECHOS_POR_BUSCA", 6)

    # --- Limites de requisicao por origem ---
    LIMITE_PADRAO = os.getenv("DOCSY_LIMITE_PADRAO", "240 per hour")
    LIMITE_SESSOES = os.getenv("DOCSY_LIMITE_SESSOES", "60 per hour")
    LIMITE_UPLOAD = os.getenv("DOCSY_LIMITE_UPLOAD", "5 per minute;40 per hour")
    LIMITE_MENSAGENS = os.getenv("DOCSY_LIMITE_MENSAGENS", "20 per minute;150 per hour")

    # --- Origem permitida do front-end ---
    ORIGEM_PERMITIDA = os.getenv("DOCSY_ORIGEM_PERMITIDA", "http://localhost:3000")

    @classmethod
    def chave_configurada(cls) -> bool:
        """Indica se ha credencial do Google (Gemini) disponivel para o agente."""
        return bool(cls.GOOGLE_API_KEY.strip())

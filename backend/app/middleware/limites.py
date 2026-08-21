"""Limite de requisicoes por origem.

O armazenamento e em memoria, coerente com uma aplicacao de instancia unica.
Com mais de uma instancia atras de um balanceador, este armazenamento
precisa virar compartilhado (Redis, por exemplo).
"""

from flask_limiter import Limiter

from app.config import Config
from app.middleware.seguranca import ip_do_cliente

limitador = Limiter(
    key_func=ip_do_cliente,
    default_limits=[Config.LIMITE_PADRAO],
    storage_uri="memory://",
    strategy="fixed-window",
)

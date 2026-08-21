"""Fabrica da aplicacao Flask do Docsy."""

from flask import Flask, jsonify

from app.config import Config
from app.middleware.limites import limitador
from app.middleware.seguranca import aplicar_cabecalhos
from app.routes.conversas_routes import conversas_bp
from app.routes.documentos_routes import documentos_bp
from app.routes.saude_routes import saude_bp
from app.utils.erros import ErroDocsy
from app.utils.log import configurar_log, logger


def criar_app(config=Config) -> Flask:
    """Monta a aplicacao com configuracao, middleware, rotas e erros."""
    configurar_log()

    app = Flask(__name__)
    app.config.from_object(config)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["JSON_SORT_KEYS"] = False

    limitador.init_app(app)

    app.register_blueprint(saude_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(conversas_bp)

    app.after_request(aplicar_cabecalhos)
    _registrar_erros(app)

    logger.info(
        "docsy iniciado modelo=%s agente_configurado=%s",
        config.MODELO,
        config.chave_configurada(),
    )
    return app


def _registrar_erros(app: Flask) -> None:
    """Centraliza o tratamento de erros, sem vazar detalhe tecnico ao usuario."""

    @app.errorhandler(ErroDocsy)
    def tratar_erro_dominio(erro: ErroDocsy):
        return jsonify({"erro": erro.codigo, "mensagem": erro.mensagem}), erro.codigo_http

    @app.errorhandler(404)
    def tratar_nao_encontrado(_erro):
        return jsonify({"erro": "nao_encontrado", "mensagem": "Recurso nao encontrado."}), 404

    @app.errorhandler(405)
    def tratar_metodo_invalido(_erro):
        return jsonify({"erro": "metodo_invalido", "mensagem": "Metodo nao permitido."}), 405

    @app.errorhandler(413)
    def tratar_arquivo_grande(_erro):
        return (
            jsonify(
                {
                    "erro": "arquivo_invalido",
                    "mensagem": f"O arquivo passa do limite de {Config.TAMANHO_MAXIMO_MB} MB.",
                }
            ),
            413,
        )

    @app.errorhandler(429)
    def tratar_excesso(_erro):
        return (
            jsonify(
                {
                    "erro": "limite_excedido",
                    "mensagem": "Muitas requisicoes em pouco tempo. Aguarde um instante.",
                }
            ),
            429,
        )

    @app.errorhandler(Exception)
    def tratar_inesperado(erro: Exception):
        # O detalhe fica no log do servidor; o usuario recebe mensagem generica.
        logger.exception("erro inesperado: %s", type(erro).__name__)
        return (
            jsonify(
                {
                    "erro": "erro_interno",
                    "mensagem": "Algo deu errado do nosso lado. Tente de novo.",
                }
            ),
            500,
        )

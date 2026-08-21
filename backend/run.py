"""Ponto de entrada do back-end do Docsy.

Uso:
    python run.py
"""

from app import criar_app
from app.config import Config

app = criar_app()

if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORTA,
        debug=Config.DEBUG,
        threaded=True,
    )

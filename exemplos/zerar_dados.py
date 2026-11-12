"""
Apaga os dados de teste (adotantes, perfis, sessões, animais, pedidos e acompanhamentos)
e mantém os critérios de compatibilidade. Use antes da apresentação e depois rode:

    python exemplos/zerar_dados.py
    python exemplos/carregar_exemplos.py

Usa o mesmo banco da API (variável DATABASE_URL), inclusive no Codespaces.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import Base, engine  # noqa: E402
import models  # noqa: E402,F401  (registra as tabelas)
import main  # noqa: E402  (pasta das fotos)

MANTER = {"criterio_compatibilidade"}

with engine.begin() as conexao:
    for tabela in reversed(Base.metadata.sorted_tables):
        if tabela.name not in MANTER:
            conexao.execute(tabela.delete())

shutil.rmtree(main.PASTA_FOTOS, ignore_errors=True)
print("Dados de teste apagados. Para recolocar os animais de exemplo: python exemplos/carregar_exemplos.py")

"""
Match Pets - modo demonstração (um comando, sem PostgreSQL).

    python iniciar_demo.py          (Windows: py iniciar_demo.py)

Precisa só do Python 3.10 ou mais novo. Na primeira vez instala as dependências
numa pasta .venv-demo (alguns minutos); depois inicia em segundos.
Usa um banco SQLite local (matchpet_demo.db), carrega os animais de exemplo
com foto e abre o navegador. Para recomeçar do zero: python iniciar_demo.py --zerar
Para encerrar: Ctrl+C.
"""
import os
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

PASTA = Path(__file__).resolve().parent
VENV = PASTA / ".venv-demo"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
BANCO = PASTA / "matchpet_demo.db"
PORTA = 8000
URL = f"http://localhost:{PORTA}"


def passo(texto):
    print(f"\n==== {texto}", flush=True)


def main():
    if sys.version_info < (3, 10):
        sys.exit("É preciso Python 3.10 ou mais novo.")
    os.chdir(PASTA)

    if "--zerar" in sys.argv:
        BANCO.unlink(missing_ok=True)
        print("Banco de demonstração apagado.")

    if not PY.exists():
        passo("Preparando o ambiente (só na primeira vez)")
        venv.EnvBuilder(with_pip=True).create(VENV)
    passo("Verificando as dependências")
    subprocess.run([str(PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", "backend/requirements.txt"],
                   check=True)

    passo("Iniciando o Match Pets")
    ambiente = dict(os.environ, DATABASE_URL=f"sqlite:///{BANCO}", FOTOS_DIR=str(PASTA / "fotos_acompanhamento"),
                    PYTHONDONTWRITEBYTECODE="1")
    api = subprocess.Popen([str(PY), "-m", "uvicorn", "main:app", "--app-dir", "backend", "--port", str(PORTA)], env=ambiente)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"{URL}/status", timeout=2)
                break
            except OSError:
                if api.poll() is not None:
                    sys.exit("A API não iniciou. Veja as mensagens acima (a porta 8000 pode estar em uso).")
                time.sleep(1)
        subprocess.run([str(PY), "exemplos/carregar_exemplos.py", "--url", URL], check=False)
        webbrowser.open(f"{URL}/inicio.html")
        print(f"\nMatch Pets rodando em {URL}  (Ctrl+C para encerrar)")
        print(f"Área do responsável: {URL}/gestao.html   |   API: {URL}/docs")
        api.wait()
    except KeyboardInterrupt:
        pass
    finally:
        api.terminate()
        print("\nMatch Pets encerrado.")


if __name__ == "__main__":
    main()

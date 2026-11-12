"""
Carrega os animais de exemplo (com foto) na API do Match Pets, para demonstração.

    python exemplos/carregar_exemplos.py                 # API em http://localhost:8000
    python exemplos/carregar_exemplos.py --aguardar 120  # espera a API subir (Codespaces)

Não duplica nada: só cadastra um animal se ainda não existir outro com o mesmo nome,
e só envia a foto para animais de exemplo que ainda estão sem foto.
Usa apenas a biblioteca padrão do Python.
"""
import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

FOTOS = Path(__file__).resolve().parent / "fotos"
PADRAO = dict(convive_criancas=True, convive_outros_animais=True, disponivel=True)
EXEMPLOS = [
    dict(nome="Mel", especie="cao", porte="pequeno", idade_anos=3, nivel_energia="medio", tolerancia_sozinho="alta",
         exige_experiencia=False, descricao="Beagle dócil, vacinada e castrada. Adora um cochilo."),
    dict(nome="Nina", especie="gato", porte="pequeno", idade_anos=2, nivel_energia="baixo", tolerancia_sozinho="alta",
         exige_experiencia=False, descricao="Gatinha calma e carinhosa."),
    dict(nome="Luna", especie="cao", porte="medio", idade_anos=4, nivel_energia="alto", tolerancia_sozinho="media",
         exige_experiencia=False, descricao="Adora correr e brincar de bolinha."),
    dict(nome="Thor", especie="cao", porte="grande", idade_anos=5, nivel_energia="alto", tolerancia_sozinho="media",
         exige_experiencia=True, descricao="Pastor grandão e protetor, precisa de espaço."),
    dict(nome="Bob", especie="cao", porte="medio", idade_anos=6, nivel_energia="medio", tolerancia_sozinho="alta",
         exige_experiencia=False, convive_outros_animais=False,
         descricao="Buldogue tranquilo; prefere ser o único animal da casa."),
    dict(nome="Fred", especie="gato", porte="pequeno", idade_anos=4, nivel_energia="alto", tolerancia_sozinho="media",
         exige_experiencia=False, descricao="Laranja, curioso e brincalhão."),
    dict(nome="Pipoca", especie="gato", porte="pequeno", idade_anos=3, nivel_energia="alto", tolerancia_sozinho="alta",
         exige_experiencia=True, descricao="Bengal muito ativa; precisa de tutor com experiência."),
]


def chamar(url, dados=None, corpo=None, tipo="application/json"):
    if dados is not None:
        corpo = json.dumps(dados).encode()
    req = urllib.request.Request(url, data=corpo, headers={"Content-Type": tipo} if corpo else {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def enviar_foto(url, caminho):
    fronteira = uuid.uuid4().hex
    corpo = (
        f'--{fronteira}\r\nContent-Disposition: form-data; name="foto"; filename="{caminho.name}"\r\n'
        "Content-Type: image/jpeg\r\n\r\n"
    ).encode() + caminho.read_bytes() + f"\r\n--{fronteira}--\r\n".encode()
    return chamar(url, corpo=corpo, tipo=f"multipart/form-data; boundary={fronteira}")


def aguardar_api(base, segundos):
    limite = time.time() + segundos
    while True:
        try:
            chamar(f"{base}/status")
            return
        except (urllib.error.URLError, ConnectionError, OSError):
            if time.time() > limite:
                raise SystemExit(f"A API não respondeu em {base} dentro de {segundos} s.")
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8000", help="endereço da API")
    parser.add_argument("--aguardar", type=int, default=0, help="segundos para esperar a API subir")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    if args.aguardar:
        aguardar_api(base, args.aguardar)

    existentes = {a["nome"].lower(): a for a in chamar(f"{base}/animais")}
    novos = 0
    for exemplo in EXEMPLOS:
        if exemplo["nome"].lower() not in existentes:
            criado = chamar(f"{base}/animais", {**PADRAO, **exemplo})
            existentes[criado["nome"].lower()] = criado
            novos += 1

    fotos = 0
    for exemplo in EXEMPLOS:
        animal = existentes[exemplo["nome"].lower()]
        caminho = FOTOS / f"{exemplo['nome'].lower()}.jpg"
        if not animal.get("foto_url") and caminho.is_file():
            enviar_foto(f"{base}/animais/{animal['id']}/foto", caminho)
            fotos += 1

    print(f"Animais de exemplo: {novos} cadastrado(s), {fotos} foto(s) enviada(s).")


if __name__ == "__main__":
    main()

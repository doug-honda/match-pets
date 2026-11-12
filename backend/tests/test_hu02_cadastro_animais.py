"""HU02 - Cadastro de animais: um teste por cenário dos critérios de aceite."""
from conftest import campos_com_erro, dados_animal


def nomes_disponiveis(client):
    return [a["nome"] for a in client.get("/animais", params={"disponivel": "true"}).json()]


def test_cenario1_animal_cadastrado_aparece_entre_os_disponiveis(client):
    resposta = client.post("/animais", json=dados_animal())

    assert resposta.status_code == 201
    assert nomes_disponiveis(client) == ["Mel"]


def test_cenario2_cadastro_incompleto_bloqueia_e_aponta_os_campos(client):
    dados = dados_animal(nome="")
    del dados["porte"]
    resposta = client.post("/animais", json=dados)

    assert resposta.status_code == 422
    assert {"nome", "porte"} <= campos_com_erro(resposta)
    assert client.get("/animais").json() == []


def test_cenario3_animal_marcado_indisponivel_sai_da_lista_de_disponiveis(client):
    mel = client.post("/animais", json=dados_animal()).json()
    client.post("/animais", json=dados_animal(nome="Nina", especie="gato"))

    resposta = client.patch(f"/animais/{mel['id']}/disponibilidade", json={"disponivel": False})

    assert resposta.status_code == 200
    assert nomes_disponiveis(client) == ["Nina"]


# Foto opcional do animal (mostrada nos cards de compatibilidade e da lista).
PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_foto_do_animal_aparece_no_cadastro(client):
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]
    assert client.get(f"/animais/{animal_id}").json()["foto_url"] is None

    resposta = client.post(f"/animais/{animal_id}/foto", files={"foto": ("mel.png", PNG_MINIMO, "image/png")})

    assert resposta.status_code == 200
    foto_url = resposta.json()["foto_url"]
    assert client.get(foto_url).content == PNG_MINIMO
    assert client.get("/animais").json()[0]["foto_url"] == foto_url


def test_foto_do_animal_em_formato_invalido_e_recusada(client):
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]

    resposta = client.post(f"/animais/{animal_id}/foto", files={"foto": ("a.png", b"texto", "image/png")})

    assert resposta.status_code == 422
    assert client.get(f"/animais/{animal_id}").json()["foto_url"] is None

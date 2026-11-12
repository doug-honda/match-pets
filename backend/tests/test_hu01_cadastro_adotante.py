"""HU01 - Cadastro do adotante: um teste por cenário dos critérios de aceite."""
from conftest import campos_com_erro, dados_adotante


def test_cenario1_cadastro_valido_cria_adotante(client):
    resposta = client.post("/adotantes", json=dados_adotante())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome_completo"] == "Maria Exemplo da Silva"
    assert corpo["email"] == "maria.exemplo@teste.com"
    assert "senha" not in corpo and "senha_hash" not in corpo
    assert client.get(f"/adotantes/{corpo['id']}").status_code == 200


def test_cenario2_campo_obrigatorio_vazio_bloqueia_e_aponta_o_campo(client):
    resposta = client.post("/adotantes", json=dados_adotante(nome_completo="   "))

    assert resposta.status_code == 422
    assert "nome_completo" in campos_com_erro(resposta)


def test_cenario2_campo_obrigatorio_ausente_bloqueia_e_aponta_o_campo(client):
    dados = dados_adotante()
    del dados["senha"]
    resposta = client.post("/adotantes", json=dados)

    assert resposta.status_code == 422
    assert "senha" in campos_com_erro(resposta)


def test_cenario3_email_ja_cadastrado_bloqueia_com_campo_email(client):
    client.post("/adotantes", json=dados_adotante())
    resposta = client.post("/adotantes", json=dados_adotante(cpf="111.444.777-35"))

    assert resposta.status_code == 409
    assert resposta.json()["detail"]["campo"] == "email"


def test_cpf_ja_cadastrado_bloqueia_com_campo_cpf(client):
    client.post("/adotantes", json=dados_adotante())
    resposta = client.post("/adotantes", json=dados_adotante(email="outra.pessoa@teste.com"))

    assert resposta.status_code == 409
    assert resposta.json()["detail"]["campo"] == "cpf"

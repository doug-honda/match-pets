"""HU05 - Solicitação de adoção: um teste por cenário dos critérios de aceite, mais login e RISK06."""
from conftest import dados_adotante, dados_animal


def cadastrar_e_logar(client, **alteracoes):
    dados = dados_adotante(**alteracoes)
    adotante_id = client.post("/adotantes", json=dados).json()["id"]
    login = client.post("/login", json={"email": dados["email"], "senha": dados["senha"]}).json()
    return adotante_id, {"Authorization": f"Bearer {login['token']}"}


def test_login_com_senha_errada_e_recusado(client):
    client.post("/adotantes", json=dados_adotante())

    resposta = client.post("/login", json={"email": "maria.exemplo@teste.com", "senha": "errada123"})

    assert resposta.status_code == 401


def test_sem_login_a_solicitacao_e_bloqueada(client):
    adotante_id = client.post("/adotantes", json=dados_adotante()).json()["id"]
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]

    resposta = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id})

    assert resposta.status_code == 401


def test_cenario1_solicitacao_registrada_ligando_adotante_e_animal(client):
    adotante_id, cabecalho = cadastrar_e_logar(client)
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]

    resposta = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id}, headers=cabecalho)

    assert resposta.status_code == 201
    assert resposta.json()["adotante_id"] == adotante_id
    assert resposta.json()["animal_id"] == animal_id


def test_cenario2_confirmacao_e_solicitacao_mantida_para_acompanhamento(client):
    adotante_id, cabecalho = cadastrar_e_logar(client)
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]

    criada = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id}, headers=cabecalho).json()

    assert criada["status"] == "pendente"
    lista = client.get(f"/solicitacoes?adotante_id={adotante_id}").json()
    assert [s["id"] for s in lista] == [criada["id"]]
    assert lista[0]["animal_nome"] == "Mel"


def test_cenario3_animal_indisponivel_bloqueia_a_solicitacao(client):
    adotante_id, cabecalho = cadastrar_e_logar(client)
    animal_id = client.post("/animais", json=dados_animal(disponivel=False)).json()["id"]

    resposta = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id}, headers=cabecalho)

    assert resposta.status_code == 409
    assert "não está mais disponível" in resposta.json()["detail"]
    assert client.get("/solicitacoes").json() == []


def test_risk06_segundo_pedido_pelo_mesmo_animal_recebe_indisponivel(client):
    primeiro_id, cab1 = cadastrar_e_logar(client)
    segundo_id, cab2 = cadastrar_e_logar(client, email="joao@teste.com", cpf="111.444.777-35")
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]

    r1 = client.post("/solicitacoes", json={"adotante_id": primeiro_id, "animal_id": animal_id}, headers=cab1)
    r2 = client.post("/solicitacoes", json={"adotante_id": segundo_id, "animal_id": animal_id}, headers=cab2)

    assert r1.status_code == 201
    assert r2.status_code == 409
    assert client.get(f"/animais/{animal_id}").json()["disponivel"] is False


def test_solicitacao_recusada_devolve_o_animal_para_a_lista(client):
    adotante_id, cabecalho = cadastrar_e_logar(client)
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]
    solicitacao_id = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id}, headers=cabecalho).json()["id"]

    resposta = client.patch(f"/solicitacoes/{solicitacao_id}", json={"status": "recusada"})

    assert resposta.json()["status"] == "recusada"
    assert client.get(f"/animais/{animal_id}").json()["disponivel"] is True

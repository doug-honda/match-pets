"""HU06 - Acompanhamento pós-adoção: um teste por cenário dos critérios de aceite, mais RISK07 (fotos)."""
from conftest import dados_adotante, dados_animal

PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG_MINIMO = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def adocao_concluida(client, aprovar=True):
    dados = dados_adotante()
    adotante_id = client.post("/adotantes", json=dados).json()["id"]
    token = client.post("/login", json={"email": dados["email"], "senha": dados["senha"]}).json()["token"]
    cabecalho = {"Authorization": f"Bearer {token}"}
    animal_id = client.post("/animais", json=dados_animal()).json()["id"]
    solicitacao_id = client.post("/solicitacoes", json={"adotante_id": adotante_id, "animal_id": animal_id}, headers=cabecalho).json()["id"]
    if aprovar:
        client.patch(f"/solicitacoes/{solicitacao_id}", json={"status": "aprovada"})
    return solicitacao_id, cabecalho


def enviar(client, solicitacao_id, cabecalho, descricao="Mel já se adaptou e dorme no sofá.", foto=("mel.png", PNG_MINIMO, "image/png")):
    arquivos = {"foto": foto} if foto else None
    return client.post(
        f"/solicitacoes/{solicitacao_id}/acompanhamentos",
        data={"descricao": descricao}, files=arquivos, headers=cabecalho,
    )


def test_cenario1_atualizacao_com_foto_registrada_no_historico_da_adocao(client):
    solicitacao_id, cabecalho = adocao_concluida(client)

    resposta = enviar(client, solicitacao_id, cabecalho)

    assert resposta.status_code == 201
    assert resposta.json()["solicitacao_id"] == solicitacao_id
    foto = client.get(resposta.json()["foto_url"])
    assert foto.status_code == 200 and foto.content == PNG_MINIMO


def test_cenario2_historico_mostra_as_atualizacoes_da_adocao(client):
    solicitacao_id, cabecalho = adocao_concluida(client)
    enviar(client, solicitacao_id, cabecalho, descricao="Primeira semana: tímida.")
    enviar(client, solicitacao_id, cabecalho, descricao="Segundo mês: brincalhona.", foto=("mel.jpg", JPG_MINIMO, "image/jpeg"))

    historico = client.get(f"/solicitacoes/{solicitacao_id}/acompanhamentos").json()

    assert [h["descricao"] for h in historico] == ["Segundo mês: brincalhona.", "Primeira semana: tímida."]
    assert all(h["solicitacao_id"] == solicitacao_id for h in historico)


def test_cenario3_envio_sem_foto_e_bloqueado(client):
    solicitacao_id, cabecalho = adocao_concluida(client)

    resposta = enviar(client, solicitacao_id, cabecalho, foto=None)

    assert resposta.status_code == 422
    assert [e["campo"] for e in resposta.json()["detail"]] == ["foto"]
    assert client.get(f"/solicitacoes/{solicitacao_id}/acompanhamentos").json() == []


def test_cenario3_envio_sem_descricao_e_bloqueado(client):
    solicitacao_id, cabecalho = adocao_concluida(client)

    resposta = enviar(client, solicitacao_id, cabecalho, descricao="   ")

    assert resposta.status_code == 422
    assert [e["campo"] for e in resposta.json()["detail"]] == ["descricao"]


def test_risk07_formato_e_tamanho_da_foto_sao_validados(client):
    solicitacao_id, cabecalho = adocao_concluida(client)

    texto = enviar(client, solicitacao_id, cabecalho, foto=("nota.png", b"isto nao e imagem", "image/png"))
    grande = enviar(client, solicitacao_id, cabecalho, foto=("grande.png", PNG_MINIMO + b"\x00" * (5 * 1024 * 1024), "image/png"))

    assert texto.status_code == 422 and "JPG, PNG ou WEBP" in texto.json()["detail"][0]["mensagem"]
    assert grande.status_code == 422 and "5 MB" in grande.json()["detail"][0]["mensagem"]


def test_acompanhamento_so_depois_da_adocao_concluida(client):
    solicitacao_id, cabecalho = adocao_concluida(client, aprovar=False)

    resposta = enviar(client, solicitacao_id, cabecalho)

    assert resposta.status_code == 409

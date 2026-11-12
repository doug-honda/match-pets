"""
Configuração dos testes: cada teste usa um banco SQLite em memória, novo e vazio,
no lugar do PostgreSQL. Assim os testes rodam sem banco instalado e não tocam nos dados locais.
"""
import os

# Precisa vir antes de importar a aplicação: main.py cria as tabelas ao ser importado.
os.environ["DATABASE_URL"] = "sqlite://"
# Fotos do acompanhamento (HU06) vão para uma pasta temporária, fora do projeto.
import tempfile
os.environ["FOTOS_DIR"] = tempfile.mkdtemp(prefix="matchpet-fotos-")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessaoTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db_teste():
        db = SessaoTeste()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_db_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def dados_adotante(**alteracoes):
    """Cadastro válido de adotante; os testes alteram só o que interessa ao cenário."""
    dados = {
        "nome_completo": "Maria Exemplo da Silva",
        "cpf": "529.982.247-25",
        "email": "maria.exemplo@teste.com",
        "telefone": "(11) 91234-5678",
        "data_nascimento": "1998-05-14",
        "senha": "senhaSegura123",
        "cep": "09850-901",
        "logradouro": "Av. Humberto de Alencar Castelo Branco",
        "numero": "3972",
        "complemento": "",
        "bairro": "Assunção",
        "cidade": "São Bernardo do Campo",
        "estado": "SP",
    }
    dados.update(alteracoes)
    return dados


def dados_animal(**alteracoes):
    """Cadastro válido de animal (HU02)."""
    dados = {
        "nome": "Mel",
        "especie": "cao",
        "porte": "pequeno",
        "idade_anos": 3,
        "nivel_energia": "medio",
        "convive_criancas": True,
        "convive_outros_animais": True,
        "tolerancia_sozinho": "alta",
        "exige_experiencia": False,
        "disponivel": True,
        "descricao": "Cadelinha dócil, vacinada e castrada.",
    }
    dados.update(alteracoes)
    return dados


def dados_perfil(**alteracoes):
    """Perfil de adoção completo (HU03), com os 8 campos."""
    dados = {
        "tipo_moradia": "apartamento",
        "tem_criancas": False,
        "tem_outros_animais": True,
        "nivel_atividade": "medio",
        "horas_sozinho": "4_a_8",
        "ja_teve_pet": True,
        "especie_preferida": "cao",
        "porte_preferido": "pequeno",
    }
    dados.update(alteracoes)
    return dados


def campos_com_erro(resposta):
    """Nomes dos campos apontados num erro 422 do FastAPI."""
    return {erro["loc"][-1] for erro in resposta.json()["detail"]}

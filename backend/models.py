"""
Modelos ORM: adotante, animal, perfil_adotante (Sprint 1) e
criterio_compatibilidade, solicitacao_adocao, acompanhamento (Sprint 2).
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, ForeignKey, func
from database import Base


class Adotante(Base):
    __tablename__ = "adotante"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(150), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    telefone = Column(String(20), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    senha_hash = Column(String(255), nullable=False)

    cep = Column(String(9), nullable=False)
    logradouro = Column(String(150), nullable=False)
    numero = Column(String(10), nullable=False)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)

    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Animal(Base):
    __tablename__ = "animal"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    especie = Column(String(10), nullable=False)
    porte = Column(String(10), nullable=False)
    idade_anos = Column(Integer, nullable=False)
    nivel_energia = Column(String(10), nullable=False)
    convive_criancas = Column(Boolean, nullable=False)
    convive_outros_animais = Column(Boolean, nullable=False)
    tolerancia_sozinho = Column(String(10), nullable=False)
    exige_experiencia = Column(Boolean, nullable=False)
    disponivel = Column(Boolean, nullable=False, default=True)
    descricao = Column(Text, nullable=True)
    foto_arquivo = Column(String(80), nullable=True)  # foto opcional do animal

    criado_em = Column(DateTime, server_default=func.now())

    @property
    def foto_url(self) -> str | None:
        return f"/fotos/{self.foto_arquivo}" if self.foto_arquivo else None


class PerfilAdotante(Base):
    """Perfil de adoção (HU03): rotina, moradia, ambiente familiar e preferências.
    Um perfil por adotante; os campos são os usados no cálculo de compatibilidade (HU04)."""
    __tablename__ = "perfil_adotante"

    id = Column(Integer, primary_key=True, index=True)
    adotante_id = Column(
        Integer, ForeignKey("adotante.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    tipo_moradia = Column(String(20), nullable=False)
    tem_criancas = Column(Boolean, nullable=False)
    tem_outros_animais = Column(Boolean, nullable=False)
    nivel_atividade = Column(String(10), nullable=False)
    horas_sozinho = Column(String(10), nullable=False)
    ja_teve_pet = Column(Boolean, nullable=False)
    especie_preferida = Column(String(12), nullable=False)
    porte_preferido = Column(String(12), nullable=False)

    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CriterioCompatibilidade(Base):
    """Critérios e pesos do cálculo de compatibilidade (HU04).
    Ficam no banco para a PO poder ajustar os pesos sem mudar o código."""
    __tablename__ = "criterio_compatibilidade"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(12), nullable=False)  # "eliminatorio" ou "pontuacao"
    peso = Column(Integer, nullable=False, default=0)
    descricao = Column(Text, nullable=False)


class SolicitacaoAdocao(Base):
    """Solicitação de adoção (HU05). Status: pendente -> aprovada (adoção concluída) ou recusada."""
    __tablename__ = "solicitacao_adocao"

    id = Column(Integer, primary_key=True, index=True)
    adotante_id = Column(Integer, ForeignKey("adotante.id", ondelete="CASCADE"), nullable=False, index=True)
    animal_id = Column(Integer, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(10), nullable=False, default="pendente")
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Acompanhamento(Base):
    """Atualização pós-adoção (HU06): texto sobre a adaptação e uma foto."""
    __tablename__ = "acompanhamento"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(
        Integer, ForeignKey("solicitacao_adocao.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao = Column(Text, nullable=False)
    foto_arquivo = Column(String(80), nullable=False)
    criado_em = Column(DateTime, server_default=func.now())


class Sessao(Base):
    """Sessão de login: token aleatório ligado ao adotante (HU05 exige adotante autenticado)."""
    __tablename__ = "sessao"

    token = Column(String(64), primary_key=True)
    adotante_id = Column(Integer, ForeignKey("adotante.id", ondelete="CASCADE"), nullable=False, index=True)
    criado_em = Column(DateTime, server_default=func.now())

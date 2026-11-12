-- =========================================================
-- MatchPet - Schema do banco de dados
-- HU01 - Cadastro do Adotante
-- =========================================================

CREATE TABLE IF NOT EXISTS adotante (
    id              SERIAL PRIMARY KEY,
    nome_completo   VARCHAR(150)        NOT NULL,
    cpf             VARCHAR(11)         NOT NULL UNIQUE,
    email           VARCHAR(150)        NOT NULL UNIQUE,
    telefone        VARCHAR(20)         NOT NULL,
    data_nascimento DATE                NOT NULL,
    senha_hash      VARCHAR(255)        NOT NULL,

    -- Endereço
    cep             VARCHAR(9)          NOT NULL,
    logradouro      VARCHAR(150)        NOT NULL,
    numero          VARCHAR(10)         NOT NULL,
    complemento     VARCHAR(100),
    bairro          VARCHAR(100)        NOT NULL,
    cidade          VARCHAR(100)        NOT NULL,
    estado          CHAR(2)             NOT NULL,

    criado_em       TIMESTAMP           NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP           NOT NULL DEFAULT NOW()
);

-- Índices auxiliares para busca
CREATE INDEX IF NOT EXISTS idx_adotante_email ON adotante (email);
CREATE INDEX IF NOT EXISTS idx_adotante_cpf ON adotante (cpf);

-- Trigger para atualizar "atualizado_em" automaticamente
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualizar_adotante ON adotante;
CREATE TRIGGER trg_atualizar_adotante
BEFORE UPDATE ON adotante
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp();


-- =========================================================
-- HU02 - Cadastro do Animal
-- =========================================================
CREATE TABLE IF NOT EXISTS animal (
    id                      SERIAL PRIMARY KEY,
    nome                    VARCHAR(100) NOT NULL,
    especie                 VARCHAR(10)  NOT NULL CHECK (especie IN ('cao', 'gato')),
    porte                   VARCHAR(10)  NOT NULL CHECK (porte IN ('pequeno', 'medio', 'grande')),
    idade_anos              INTEGER      NOT NULL CHECK (idade_anos BETWEEN 0 AND 30),
    nivel_energia           VARCHAR(10)  NOT NULL CHECK (nivel_energia IN ('baixo', 'medio', 'alto')),
    convive_criancas        BOOLEAN      NOT NULL,
    convive_outros_animais  BOOLEAN      NOT NULL,
    tolerancia_sozinho      VARCHAR(10)  NOT NULL CHECK (tolerancia_sozinho IN ('baixa', 'media', 'alta')),
    exige_experiencia       BOOLEAN      NOT NULL,
    disponivel              BOOLEAN      NOT NULL DEFAULT TRUE,
    descricao               TEXT,
    criado_em               TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- =========================================================
-- HU03 - Perfil do Adotante (um perfil por adotante)
-- =========================================================
CREATE TABLE IF NOT EXISTS perfil_adotante (
    id                  SERIAL PRIMARY KEY,
    adotante_id         INTEGER      NOT NULL UNIQUE REFERENCES adotante (id) ON DELETE CASCADE,
    tipo_moradia        VARCHAR(20)  NOT NULL CHECK (tipo_moradia IN ('apartamento', 'casa_sem_quintal', 'casa_com_quintal')),
    tem_criancas        BOOLEAN      NOT NULL,
    tem_outros_animais  BOOLEAN      NOT NULL,
    nivel_atividade     VARCHAR(10)  NOT NULL CHECK (nivel_atividade IN ('baixo', 'medio', 'alto')),
    horas_sozinho       VARCHAR(10)  NOT NULL CHECK (horas_sozinho IN ('ate_4', '4_a_8', 'mais_de_8')),
    ja_teve_pet         BOOLEAN      NOT NULL,
    especie_preferida   VARCHAR(12)  NOT NULL CHECK (especie_preferida IN ('cao', 'gato', 'indiferente')),
    porte_preferido     VARCHAR(12)  NOT NULL CHECK (porte_preferido IN ('pequeno', 'medio', 'grande', 'indiferente')),
    criado_em           TIMESTAMP    NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMP    NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_atualizar_perfil_adotante ON perfil_adotante;
CREATE TRIGGER trg_atualizar_perfil_adotante
BEFORE UPDATE ON perfil_adotante
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp();

-- =========================================================
-- HU04 - Compatibilidade: critérios e pesos (ajustáveis pela PO)
-- 4 filtros eliminatórios + 5 critérios de pontuação (soma 100)
-- =========================================================
-- Foto opcional do animal (mostrada nos cards). Em bancos criados antes, a coluna é adicionada aqui.
ALTER TABLE animal ADD COLUMN IF NOT EXISTS foto_arquivo VARCHAR(80);

CREATE TABLE IF NOT EXISTS criterio_compatibilidade (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(30)  NOT NULL UNIQUE,
    nome        VARCHAR(100) NOT NULL,
    tipo        VARCHAR(12)  NOT NULL CHECK (tipo IN ('eliminatorio', 'pontuacao')),
    peso        INTEGER      NOT NULL DEFAULT 0 CHECK (peso BETWEEN 0 AND 100),
    descricao   TEXT         NOT NULL
);

INSERT INTO criterio_compatibilidade (codigo, nome, tipo, peso, descricao) VALUES
    ('disponibilidade',    'Disponibilidade',                'eliminatorio', 0,  'Animal indisponível não aparece na lista.'),
    ('especie',            'Espécie preferida',              'eliminatorio', 0,  'Se o adotante escolheu cão ou gato, animais da outra espécie não aparecem.'),
    ('criancas',           'Convivência com crianças',       'eliminatorio', 0,  'Casa com crianças: animais que não convivem bem com crianças não aparecem.'),
    ('outros_animais',     'Convivência com outros animais', 'eliminatorio', 0,  'Casa com outros animais: animais que não convivem bem com eles não aparecem.'),
    ('espaco_porte',       'Espaço x porte',                 'pontuacao',    30, 'Tipo de moradia comparado ao porte do cão. Gatos pontuam o máximo.'),
    ('atividade_energia',  'Atividade x energia',            'pontuacao',    25, 'Nível de atividade do adotante comparado ao nível de energia do animal.'),
    ('sozinho_tolerancia', 'Tempo sozinho x tolerância',     'pontuacao',    20, 'Horas que o animal ficará sozinho comparadas à tolerância dele.'),
    ('experiencia',        'Experiência',                    'pontuacao',    15, 'Animal que exige experiência pontua só se o adotante já teve animal.'),
    ('porte_preferido',    'Porte preferido',                'pontuacao',    10, 'Porte do animal comparado ao porte que o adotante prefere.')
ON CONFLICT (codigo) DO NOTHING;

-- =========================================================
-- Login: sessões do adotante (HU05 exige adotante autenticado)
-- =========================================================
CREATE TABLE IF NOT EXISTS sessao (
    token        VARCHAR(64) PRIMARY KEY,
    adotante_id  INTEGER     NOT NULL REFERENCES adotante (id) ON DELETE CASCADE,
    criado_em    TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- =========================================================
-- HU05 - Solicitação de adoção
-- =========================================================
CREATE TABLE IF NOT EXISTS solicitacao_adocao (
    id             SERIAL PRIMARY KEY,
    adotante_id    INTEGER     NOT NULL REFERENCES adotante (id) ON DELETE CASCADE,
    animal_id      INTEGER     NOT NULL REFERENCES animal (id) ON DELETE CASCADE,
    status         VARCHAR(10) NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'recusada')),
    criado_em      TIMESTAMP   NOT NULL DEFAULT NOW(),
    atualizado_em  TIMESTAMP   NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_atualizar_solicitacao ON solicitacao_adocao;
CREATE TRIGGER trg_atualizar_solicitacao
BEFORE UPDATE ON solicitacao_adocao
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp();

-- =========================================================
-- HU06 - Acompanhamento pós-adoção (texto + foto)
-- =========================================================
CREATE TABLE IF NOT EXISTS acompanhamento (
    id              SERIAL PRIMARY KEY,
    solicitacao_id  INTEGER     NOT NULL REFERENCES solicitacao_adocao (id) ON DELETE CASCADE,
    descricao       TEXT        NOT NULL,
    foto_arquivo    VARCHAR(80) NOT NULL,
    criado_em       TIMESTAMP   NOT NULL DEFAULT NOW()
);

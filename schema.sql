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

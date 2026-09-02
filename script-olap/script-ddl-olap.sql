-- ============================================================
-- SCRIPT DDL - MODELO OLAP COM DUAS FATOS (ORACLE DATABASE)
-- ============================================================

-- 1. TABELAS DE DIMENSÃO

CREATE TABLE DIM_Produto (
    ID_Produto NUMBER,
    Categoria  NUMBER,
    Valor      NUMBER(15, 2),
    CONSTRAINT PK_DIM_Produto PRIMARY KEY (ID_Produto)
);

CREATE TABLE DIM_Tempo (
    ID_Data      NUMBER,
    Ano          NUMBER(4),
    Quadrimestre NUMBER(1),
    CONSTRAINT PK_DIM_Tempo PRIMARY KEY (ID_Data)
);

CREATE TABLE DIM_Cliente (
    ID_Cliente   NUMBER,
    Estado_Civil NUMBER,
    CONSTRAINT PK_DIM_Cliente PRIMARY KEY (ID_Cliente)
);

CREATE TABLE DIM_Filial (
    ID_Filial NUMBER,
    Nome      VARCHAR2(100),
    Cidade    VARCHAR2(100),
    CONSTRAINT PK_DIM_Filial PRIMARY KEY (ID_Filial)
);

-- 2. TABELAS FATO

-- 2.1. Fato Venda
CREATE TABLE FATO_Venda (
    ID_Venda   NUMBER,
    ID_Produto NUMBER NOT NULL,
    ID_Data    NUMBER NOT NULL,
    ID_Cliente NUMBER NOT NULL,
    ID_Filial  NUMBER NOT NULL,
    Quantidade NUMBER,
    Valor      NUMBER(15, 2),
    
    CONSTRAINT PK_FATO_Venda PRIMARY KEY (ID_Venda),
    CONSTRAINT FK_FATO_Venda_DIM_Produto FOREIGN KEY (ID_Produto) REFERENCES DIM_Produto (ID_Produto),
    CONSTRAINT FK_FATO_Venda_DIM_Tempo   FOREIGN KEY (ID_Data)    REFERENCES DIM_Tempo (ID_Data),
    CONSTRAINT FK_FATO_Venda_DIM_Cliente FOREIGN KEY (ID_Cliente) REFERENCES DIM_Cliente (ID_Cliente),
    CONSTRAINT FK_FATO_Venda_DIM_Filial  FOREIGN KEY (ID_Filial)  REFERENCES DIM_Filial (ID_Filial)
);

-- 2.2. Fato Concorrente
CREATE TABLE FATO_Concorrente (
    ID_Concorrente NUMBER,
    ID_Data        NUMBER NOT NULL,
    Ano            NUMBER(4),
    Mes            NUMBER(2),
    Descricao      VARCHAR2(100),
    
    CONSTRAINT PK_FATO_Concorrente PRIMARY KEY (ID_Concorrente),
    CONSTRAINT FK_FATO_Concorrente_DIM_Tempo FOREIGN KEY (ID_Data) REFERENCES DIM_Tempo (ID_Data)
);

-- 3. ÍNDICES DE PERFORMANCE PARA CONSULTAS (OLAP)

-- Índices para FATO_Venda
CREATE INDEX IX_FATO_Venda_Produto ON FATO_Venda(ID_Produto);
CREATE INDEX IX_FATO_Venda_Tempo   ON FATO_Venda(ID_Data);
CREATE INDEX IX_FATO_Venda_Cliente ON FATO_Venda(ID_Cliente);
CREATE INDEX IX_FATO_Venda_Filial  ON FATO_Venda(ID_Filial);

-- Índice para FATO_Concorrente
CREATE INDEX IX_FATO_Concorrente_Tempo ON FATO_Concorrente(ID_Data);
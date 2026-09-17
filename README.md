# DarkAumigos

Pipeline de ETL para extrair dados do MongoDB Atlas e gerar uma carga SQL
compatível com o modelo dimensional Oracle OLAP do projeto de Mineração de
Dados.

## Status

**ETL concluída.** A extração, a validação básica, a transformação para
`INSERTs`, a combinação de fontes e a carga opcional em Oracle estão
implementadas. A execução em um Oracle real continua dependendo das credenciais,
do DDL e do ambiente de cada instalação.

## Arquitetura

```text
main.py                         # Ponto de entrada compatível
script-olap/                    # Scripts do banco OLAP (referência apenas)
src/
├── cli.py                      # Argumentos, execução e mensagens da CLI
├── config.py                   # Variáveis de ambiente e constantes
├── utilitarios.py              # Formatação SQL, datas e documentos
├── leitores/
│   ├── dados.py                # Escolha da fonte e orquestração da leitura
│   ├── json_reader.py          # Leitura de arquivos JSON locais
│   └── mongo.py                # Leitura das coleções do MongoDB Atlas
│   ├── postgresql.py           # PostgreSQL/Supabase -> Oracle (opcional)
│   ├── oracle.py               # Leitura do Oracle de origem
│   └── Excel.py                # Leitura de vendas de concorrentes em Excel
├── transformacoes/
│   ├── cliente.py              # DIM_Cliente
│   ├── concorrente.py          # FATO_Concorrente
│   ├── filial.py               # DIM_Filial padrão
│   ├── mapas.py                # Códigos de categoria e estado civil
│   ├── produto.py              # DIM_Produto
│   ├── tempo.py                # DIM_Tempo
│   └── venda.py                # FATO_Venda
├── validacao/
│   └── chaves.py               # Referências de clientes e produtos
└── sql/
	 ├── gerador.py              # Montagem ordenada do arquivo SQL
	 └── loader.py               # Execução do SQL no Oracle
```

Os módulos relacionados às tabelas usam nomes em português para facilitar a
divisão do trabalho e a comunicação do grupo.

## Requisitos

- Python 3.10 ou superior
- Acesso ao MongoDB Atlas ou arquivos JSON locais
- Oracle para executar o SQL gerado

Também é possível extrair de PostgreSQL/Supabase quando configurado via
variáveis de ambiente (veja seção de exemplo de `.env` abaixo).

Instale as dependências:

```bash
pip install -r requirements.txt
```

Para usar o Atlas, copie `.env.example` para `.env` e preencha:

```env
MONGODB_URI="mongodb+srv://..."
MONGODB_DB="DarkAumigos"
OUTPUT_SQL="carga_oracle.sql"
# Opcional: PostgreSQL / Supabase
POSTGRES_HOST="db.seu-projeto.supabase.co"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="sua_senha"
POSTGRES_SSLMODE="require"
ORACLE_USER="usuario_destino"
ORACLE_PASSWORD="sua_senha"
ORACLE_DSN="host:1521/servico"
# Alternativa ao ORACLE_DSN:
# ORACLE_HOST="host"
# ORACLE_PORT="1521"
# ORACLE_SERVICE="servico"
ORACLE_ORIGEM_USER="usuario_origem"
ORACLE_ORIGEM_PASSWORD="sua_senha"
ORACLE_ORIGEM_DSN="host:1521/servico"
```

O arquivo `.env` não deve ser versionado.

## Utilização

Com MongoDB Atlas configurado:

```bash
python main.py
```

Sem conexão com o banco, crie uma pasta com os arquivos:

```text
dados/
├── 05_Feira_Clientes.json
├── 06_Feira_Produtos.json
├── 07_Feira_Pedidos.json
└── 08_Feira_concorrentes.json  # opcional
```

Execute:

```bash
python main.py --json-dir ./dados --output ./output/carga_oracle.sql
```

Para extrair do PostgreSQL/Supabase e gerar o arquivo SQL (garanta as
variáveis `POSTGRES_*` preenchidas):

```bash
python main.py --postgresql
```

Para gerar o SQL e carregá-lo diretamente no Oracle destino, use
`--load-oracle` com qualquer fluxo de entrada:

```bash
python main.py --load-oracle
python main.py --postgresql --load-oracle
```

Para combinar MongoDB, PostgreSQL e Oracle e carregar o resultado diretamente
no Oracle, use o atalho:

```bash
python main.py --carga-completa
```

Esse comando equivale a `python main.py --todas-fontes --load-oracle`.

O parâmetro `--todas-fontes` combina MongoDB/JSON, PostgreSQL e Oracle de
origem. A pipeline remapeia IDs conflitantes entre as fontes, preserva um
produto de serviço com o ID reservado `18` e elimina registros de concorrentes
duplicados. Quando existe um arquivo `.xlsx` em `Dados`, ele é usado para os
dados de `FATO_CONCORRENTE` no lugar dos concorrentes vindos de JSON ou MongoDB.

Ou usar as funções do módulo diretamente em um script Python:

```python
from src.leitores.postgresql import salvar_sql_postgresql

salvar_sql_postgresql("./output/carga_oracle_itabuna.sql")
```

O arquivo gerado contém os `INSERTs` na ordem das chaves estrangeiras e um
`COMMIT` ao final. A coleção de concorrentes é opcional.

## Leitor Excel - FATO_CONCORRENTE

Foi adicionado um fluxo para leitura de dados de vendas de concorrentes a partir de
um arquivo Excel e geração de `INSERTs` compatíveis com a tabela Oracle
`FATO_CONCORRENTE`.

### Estrutura de pastas

O leitor Python fica em `src/leitores/Excel.py` e utiliza a raiz do projeto para
localizar automaticamente as pastas `Dados` e `output`:

```text
DarkAumigos/
├── Dados/
│   └── 08_Vendas_Concorrente.xlsx
├── output/
│   └── excel_output.sql
└── src/
    └── leitores/
		└── Excel.py
```

O arquivo Excel é procurado automaticamente dentro da pasta `Dados`. Se houver
mais de um arquivo `.xlsx`, o programa apresenta uma lista para que o usuário
escolha qual arquivo deve ser utilizado.

### Formato esperado do Excel

O arquivo Excel deve possuir as seguintes colunas obrigatórias:

- `Ano`
- `Mês`
- `Vendas (R$)`

Os meses podem ser informados tanto de forma abreviada (`Jan`, `Fev`, `Mar`,
etc.) quanto por extenso (`Janeiro`, `Fevereiro`, `Março`, etc.).

### Geração dos INSERTs

Os dados são convertidos para comandos SQL destinados à tabela
`FATO_CONCORRENTE`, utilizando as colunas:

```text
ID_CONCORRENTE
ID_DATA
ANO
MES
DESCRICAO
```

O campo `Mês` do Excel é convertido para seu respectivo número. O valor de
`Vendas (R$)` é convertido para um formato numérico compatível com Oracle.

O `ID_CONCORRENTE` é gerado sequencialmente a partir de `1`. O `ID_DATA` usa a
chave do período no formato `ANO * 10 + QUADRIMESTRE`, garantindo que todas as
vendas do mesmo ano e quadrimestre apontem para a mesma linha da `DIM_TEMPO`.

> **Atenção:** o `ID_DATA` precisa corresponder aos registros existentes na
> `DIM_TEMPO`; ele não representa mais a data completa da venda.

### Arquivo de saída

O arquivo SQL auxiliar é gerado automaticamente na pasta `output`:
```text
output/excel_output.sql
```

A pasta `output` também é criada automaticamente caso ainda não exista.

Exemplo de `INSERT` gerado:

```sql
INSERT INTO FATO_CONCORRENTE
(ID_CONCORRENTE, ID_DATA, ANO, MES, DESCRICAO)
VALUES (1, 20241, 2024, 1, 185000);
```

### Observação sobre `DESCRICAO`

Na estrutura Oracle utilizada neste fluxo, `DESCRICAO` está definida como
`NUMBER(15,2)`. Por isso, o código utiliza essa coluna para receber o valor de
`Vendas (R$)` da planilha.

Caso o modelo Oracle seja alterado para representar esse valor como `VENDAS`,
o `INSERT` e o código Python deverão ser ajustados para utilizar o novo nome da
coluna.

## Estado atual e próximos passos

1. **Validar o contrato dos dados:** conferir nomes, tipos, campos obrigatórios
	 e datas das coleções reais contra o DDL Oracle.
	- Status: Implementado para o contrato usado pela pipeline, com checagens
	  básicas em `src/validacao/chaves.py`. A validação final continua dependente
	  do DDL e dos dados reais de cada ambiente.

2. **Validar o SQL no Oracle:** executar o arquivo em um ambiente de teste e
	 corrigir diferenças entre o DDL e os documentos de origem.
	- Status: Implementado — o gerador de SQL (`src/sql/gerador.py`) cria o
	  script e `src/sql/loader.py` permite executá-lo com `--load-oracle`.
	  A homologação ainda exige testes práticos e os privilégios adequados no
	  Oracle.

3. **Concluir a carga (idempotência e estratégia):** definir se a execução
	 será manual ou automatizada, e implementar proteção contra duplicação de
	 dimensões/fatos em reexecuções.
	- Status: Parcial — a combinação de fontes elimina concorrentes duplicados e
	  remapeia IDs conflitantes, mas os `INSERTs` não implementam deduplicação
	  geral para reexecuções.

4. **Completar concorrentes:** confirmar os campos da coleção e sua relação
	 com `FATO_Concorrente`.
	- Status: Implementado — o fluxo aceita concorrentes de JSON/MongoDB ou
	  planilha Excel e gera `FATO_CONCORRENTE`.

5. **Adicionar testes:** testar leitores, mapeamentos e validações.
	- Status: Recomendado — ampliar a cobertura de testes para leitores,
	  mapeamentos, combinações de fontes e carga Oracle.

6. **Documentar o DDL e o processo:** registrar o esquema Oracle, responsáveis
	 por cada componente e o procedimento de homologação.
	- Status: Parcial — este README documenta o processo e as variáveis de
	  ambiente; o DDL e os privilégios específicos devem ser registrados conforme
	  o ambiente Oracle usado.

---

Limitações operacionais conhecidas:

- **O loader separa comandos pelo caractere `;`**; scripts com blocos PL/SQL ou
	semântica mais complexa exigem tratamento adicional.
- **A CLI não oferece `--dry-run`, retry ou timeout configurável.** Essas opções
	podem ser adicionadas caso sejam necessárias para operação em produção.
- **A execução exige `oracledb`, credenciais válidas e os privilégios Oracle**
	necessários para os `INSERTs` e o `COMMIT`.
- **A carga é executada comando a comando.** Para volumes grandes, uma estratégia
	de lotes ou `executemany` ainda pode melhorar o consumo de memória e o tempo.

Notas:
- O loader em `src/sql/loader.py` registra comandos, confirma a transação e faz
	rollback em caso de falha.
- Testes unitários e de integração continuam recomendados para homologação.

## Observações sobre o leitor PostgreSQL

O projeto passou a incluir suporte a PostgreSQL/Supabase via
`src/leitores/postgresql.py`. As principais melhorias aplicadas a esse módulo
incluem:

- Removido hardcoding de credenciais; uso exclusivo de variáveis de ambiente.
- Conexão centralizada e encerrada corretamente.
- Funções internas separadas por responsabilidade.
- Validação de identificadores SQL.
- Conversão de tipos Python -> Oracle concentrada em uma função utilitária.
- Uso de `with` para o cursor.
- Geração do SQL desacoplada da gravação do arquivo e caminho de saída
	configurável.
- Dependência sugerida: `psycopg2-binary` para facilitar instalação.

### Observação sobre `FATO_Venda`

No leitor PostgreSQL os itens de venda existem como `itens_venda`, enquanto o
modelo destino Oracle utiliza `ID_Venda` como chave do fato. Nesta implementação
`id_item` foi usado como `ID_Venda` para garantir unicidade por linha do fato.
Essa decisão deve ser confirmada contra o DDL Oracle antes da carga final.

## Divisão sugerida do grupo

- **Pessoa 1:** configuração, CLI e documentação.
- **Pessoa 2:** leitores JSON e MongoDB.
- **Pessoa 3:** dimensões e mapeamentos.
- **Pessoa 4:** fatos de venda e concorrente.
- **Pessoa 5:** validação, testes e homologação no Oracle.
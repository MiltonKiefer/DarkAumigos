# DarkAumigos

Pipeline de ETL para extrair dados do MongoDB Atlas e gerar uma carga SQL
compatível com o modelo dimensional Oracle OLAP do projeto de Mineração de
Dados.

## Status

**ETL parcial.** A extração, a validação básica e a transformação para
`INSERTs` já estão implementadas. Ainda falta validar e executar a carga em um
Oracle real, além de concluir os testes e os ajustes finais do modelo.

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
│   ├── json_reader.py                 # Leitura de arquivos JSON locais
│   └── mongo.py                # Leitura das coleções do MongoDB Atlas
│   └── postgresql.py           # PostgreSQL/Supabase -> Oracle (opcional)
├── transformacoes/
│   ├── cliente.py              # DIM_Cliente
│   ├── concorrente.py           # FATO_Concorrente
│   ├── filial.py               # DIM_Filial padrão
│   ├── mapas.py                # Códigos de categoria e estado civil
│   ├── produto.py              # DIM_Produto
│   ├── tempo.py                # DIM_Tempo
│   └── venda.py                # FATO_Venda
├── validacao/
│   └── chaves.py               # Referências de clientes e produtos
└── sql/
	 └── gerador.py              # Montagem ordenada do arquivo SQL
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

O leitor Python fica em `src/leitores` e utiliza a raiz do projeto para localizar
automaticamente as pastas `Dados` e `Output`:

```text
DarkAumigos/
├── Dados/
│   └── 08_Vendas_Concorrente.xlsx
├── Output/
│   └── insert_fato_concorrente.sql
└── src/
    └── leitores/
        └── concorrente.py
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

O `ID_CONCORRENTE` e o `ID_DATA` são gerados sequencialmente a partir de `1`,
acompanhando a ordem dos registros da planilha.

> **Atenção:** o `ID_DATA` precisa corresponder aos registros existentes na
> `DIM_TEMPO`. A sequência automática (`1, 2, 3...`) somente é válida se os IDs
> da dimensão estiverem organizados dessa mesma forma.

### Arquivo de saída

O arquivo SQL é gerado automaticamente na pasta `Output`:

```text
Output/insert_fato_concorrente.sql
```

A pasta `Output` também é criada automaticamente caso ainda não exista.

Exemplo de `INSERT` gerado:

```sql
INSERT INTO FATO_CONCORRENTE
(ID_CONCORRENTE, ID_DATA, ANO, MES, DESCRICAO)
VALUES (1, 1, 2024, 1, 185000);
```

### Observação sobre `DESCRICAO`

Na estrutura Oracle utilizada neste fluxo, `DESCRICAO` está definida como
`NUMBER(15,2)`. Por isso, o código utiliza essa coluna para receber o valor de
`Vendas (R$)` da planilha.

Caso o modelo Oracle seja alterado para representar esse valor como `VENDAS`,
o `INSERT` e o código Python deverão ser ajustados para utilizar o novo nome da
coluna.

## Próximos passos do ETL

1. **Validar o contrato dos dados:** conferir nomes, tipos, campos obrigatórios
	 e datas das coleções reais contra o DDL Oracle.
	- Status: Parcial — existe `src/validacao/chaves.py` para checagens básicas,
	  mas a validação completa contra o DDL Oracle não foi automatizada.

2. **Validar o SQL no Oracle:** executar o arquivo em um ambiente de teste e
	 corrigir diferenças entre o DDL e os documentos de origem.
	- Status: Parcial — o gerador de SQL (`src/sql/gerador.py`) cria o script;
	  foi adicionado um loader inicial (`src/sql/loader.py`), porém exige testes
	  práticos, tratamento de blocos PL/SQL e verificação de dependências do
	  cliente Oracle (Instant Client) antes da homologação.

3. **Concluir a carga (idempotência e estratégia):** definir se a execução
	 será manual ou automatizada, e implementar proteção contra duplicação de
	 dimensões/fatos em reexecuções.
	- Status: Pendente — geração de INSERTs está pronta; políticas de deduplicação
	  e reexecução devem ser definidas e implementadas.

4. **Completar concorrentes:** confirmar os campos da coleção e sua relação
	 com `FATO_Concorrente`.
	- Status: Parcial — existe `src/transformacoes/concorrente.py`, mas os campos
	  e o mapeamento devem ser validados com os dados reais.

5. **Adicionar testes:** testar leitores, mapeamentos e validações.
	- Status: Pendente (não essencial para entrega imediata; recomendado).

6. **Documentar o DDL e o processo:** registrar o esquema Oracle, responsáveis
	 por cada componente e o procedimento de homologação.
	- Status: Pendente — documentação do DDL e do processo de carga precisa ser
	  completada.

---

Pendências técnicas essenciais para a carga Oracle (novas / re-priorizadas):

- **Testar a conexão Oracle com `oracledb`** e verificar credenciais/DSN.
- **Tratar corretamente PL/SQL e blocos contendo `;`** (o parser atual é
  ingênuo e pode quebrar blocos PL/SQL ou scripts que dependam de `;`).
- **Melhorar logging e tratamento de erros/rollback** no loader (relatórios,
  retries e mensagens úteis em falhas).
- **Adicionar opções CLI úteis para execução no Oracle:** `--dry-run`,
  `--load-oracle --retry N` e timeout configurável.
- **Verificar e documentar requisitos do cliente Oracle (Instant Client)** e
  privilégios necessários no usuário Oracle para executar os INSERTs/COMMIT.
- **Implementar execução em lotes/bulk** (usar `executemany` ou estratégias de
  batching) para suportar grandes volumes sem consumir muita memória.

Notas:
- O loader inicial foi adicionado em `src/sql/loader.py`, e facilita testes
  locais, mas ainda falta robustez (parsing, logging, batched execution).
- Os testes unitários/integration são desejáveis, mas não foram adicionados aqui
  conforme sua orientação; foquei nas pendências operacionais essenciais.

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
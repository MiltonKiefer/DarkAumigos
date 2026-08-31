# DarkAumigos

Pipeline ETL para extrair dados de **MongoDB Atlas ou PostgreSQL/Supabase** e
gerar comandos `INSERT` compatíveis com o modelo dimensional Oracle do projeto.

## Estrutura

```text
DarkAumigos/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências Python
├── .env.example             # Modelo de configuração
├── README.md
└── src/
    ├── cli.py               # Interface de linha de comando
    ├── config.py            # Configurações compartilhadas
    ├── utilitarios.py       # Funções auxiliares
    ├── leitores/
    │   ├── dados.py         # Seleção/orquestração das fontes
    │   ├── json.py          # Leitura de JSON
    │   ├── mongo.py         # Leitura do MongoDB Atlas
    │   └── postgresql.py    # PostgreSQL/Supabase -> Oracle
    ├── transformacoes/      # Transformações das dimensões e fatos
    ├── validacao/           # Validações de chaves
    └── sql/                 # Geração do SQL Oracle
```

O `postgresql.py` foi colocado em `src/leitores/`, junto aos demais módulos de
entrada, em vez de ficar na raiz do projeto. As credenciais não ficam mais
hardcoded: são carregadas por variáveis de ambiente.

## Instalação

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha as credenciais.

> **Importante:** nunca faça commit do `.env` ou de senhas reais.

## MongoDB Atlas

```bash
python main.py
```

Ou usando JSON local:

```bash
python main.py --json-dir ./dados --output ./output/carga_oracle.sql
```

## PostgreSQL / Supabase

O módulo PostgreSQL pode ser usado diretamente:

```python
from src.leitores.postgresql import salvar_sql_postgresql

salvar_sql_postgresql("./output/carga_oracle_itabuna.sql")
```

Também é possível gerar a string SQL sem criar o arquivo:

```python
from src.leitores.postgresql import gerar_sql_postgresql

sql = gerar_sql_postgresql()
```

### Variáveis necessárias

```env
POSTGRES_HOST="db.seu-projeto.supabase.co"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="sua_senha"
POSTGRES_SSLMODE="require"
```

## Melhorias aplicadas ao `postgresql.py`

- Movido para `src/leitores/postgresql.py`.
- Removidas credenciais e configurações sensíveis do código.
- Conexão centralizada e encerrada corretamente.
- Funções internas separadas por responsabilidade.
- Validação de identificadores SQL.
- Conversão de tipos Python -> Oracle concentrada em uma função.
- Uso de `with` para o cursor.
- Remoção de imports e variáveis sem utilização.
- Geração do SQL desacoplada da gravação do arquivo.
- Caminho de saída configurável.
- Dependência alterada para `psycopg2-binary`, mais simples de instalar em ambientes de desenvolvimento.

## Observação sobre `FATO_Venda`

O PostgreSQL possui itens de venda, enquanto o modelo Oracle utiliza `ID_Venda`
como chave do fato. Nesta implementação, `id_item` é utilizado como
`ID_Venda` para manter uma chave única por linha do fato. Essa decisão deve ser
confirmada contra o DDL Oracle antes da carga definitiva.

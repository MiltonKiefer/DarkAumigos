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
src/
├── cli.py                      # Argumentos, execução e mensagens da CLI
├── config.py                   # Variáveis de ambiente e constantes
├── utilitarios.py              # Formatação SQL, datas e documentos
├── leitores/
│   ├── dados.py                # Escolha da fonte e orquestração da leitura
│   ├── json.py                 # Leitura de arquivos JSON locais
│   └── mongo.py                # Leitura das coleções do MongoDB Atlas
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

Instale as dependências:

```bash
pip install -r requirements.txt
```

Para usar o Atlas, copie `.env.example` para `.env` e preencha:

```env
MONGODB_URI="mongodb+srv://..."
MONGODB_DB="DarkAumigos"
OUTPUT_SQL="carga_oracle.sql"
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

O arquivo gerado contém os `INSERTs` na ordem das chaves estrangeiras e um
`COMMIT` ao final. A coleção de concorrentes é opcional.

## Próximos passos do ETL

1. **Validar o contrato dos dados:** conferir nomes, tipos, campos obrigatórios
	e datas das coleções reais contra o DDL Oracle.
2. **Validar o SQL no Oracle:** executar o arquivo em um ambiente de teste e
	corrigir diferenças entre o DDL e os documentos do Atlas.
3. **Concluir a carga:** definir se a execução será manual ou automatizada e
	tratar reexecuções sem duplicar dimensões e fatos.
4. **Completar concorrentes:** confirmar os campos da coleção e sua relação
	com `FATO_Concorrente`.
5. **Adicionar testes:** testar leitores, mapeamentos, validação e comparar
	uma saída SQL conhecida com a saída gerada.
6. **Documentar o DDL e o processo:** registrar o esquema Oracle, responsáveis
	por cada componente e o procedimento de homologação.

## Divisão sugerida do grupo

- **Pessoa 1:** configuração, CLI e documentação.
- **Pessoa 2:** leitores JSON e MongoDB.
- **Pessoa 3:** dimensões e mapeamentos.
- **Pessoa 4:** fatos de venda e concorrente.
- **Pessoa 5:** validação, testes e homologação no Oracle.

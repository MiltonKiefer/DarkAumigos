"""Interface de linha de comando da pipeline."""

import argparse
import os
import unicodedata
from pathlib import Path

from src.leitores.dados import carregar_dados
from src.sql.gerador import gerar_sql, dados_oracle_para_contrato
from src.transformacoes.mapas import criar_mapa_categorias, criar_mapa_estado_civil


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"


def _caminho_saida(valor: str) -> Path:
    caminho = Path(valor)
    if not caminho.is_absolute() and caminho.parts[:1] != (OUTPUT_DIR.name,):
        caminho = OUTPUT_DIR / caminho
    return caminho


def _texto_produto(produto: dict) -> str:
    valores = []
    for valor in produto.values():
        if isinstance(valor, (str, int, float)):
            valores.append(str(valor))
    return " ".join(valores)


def _produto_e_servico(produto: dict) -> bool:
    texto = unicodedata.normalize("NFKD", _texto_produto(produto))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    palavras = texto.casefold().split()
    return any(palavra.startswith(("servico", "servicos")) for palavra in palavras)


def _combinar_fontes(fontes: list[dict[str, list[dict]]]) -> dict[str, list[dict]]:
    """Combina fontes mantendo IDs e referências isolados por origem."""
    combinado = {
        "clientes": [],
        "produtos": [],
        "pedidos": [],
        "concorrentes": [],
        "filiais": [],
    }
    ids_clientes: set[int] = set()
    ids_pedidos: set[int] = set()
    produtos_por_id: dict[int, dict] = {}

    def remapear_ids(registros, campo, ids_usados, nome_fonte):
        mapa = {}
        proximo_id = max(ids_usados, default=0) + 1
        for registro in registros:
            antigo = int(registro[campo])
            if antigo in mapa:
                raise ValueError(
                    f"A fonte {nome_fonte} possui IDs duplicados em '{campo}': {antigo}."
                )
            novo = antigo
            if novo in ids_usados or novo <= 0:
                while proximo_id in ids_usados:
                    proximo_id += 1
                novo = proximo_id
                proximo_id += 1
            mapa[antigo] = novo
            ids_usados.add(novo)
        return mapa

    for indice_fonte, fonte in enumerate(fontes, 1):
        clientes = list(fonte.get("clientes", []))
        produtos = list(fonte.get("produtos", []))
        pedidos = list(fonte.get("pedidos", []))
        nome_fonte = str(fonte.get("nome_fonte", f"#{indice_fonte}"))
        mapa_clientes = remapear_ids(
            clientes, "id_cliente", ids_clientes, nome_fonte
        )
        mapa_produtos: dict[int, int] = {}
        for produto in produtos:
            antigo = int(produto["id_produto"])
            novo = 18 if _produto_e_servico(produto) else antigo
            if novo == 18 and antigo != 18 and 18 in produtos_por_id:
                raise ValueError(
                    f"A fonte {nome_fonte} possui mais de um produto de serviço."
                )
            if novo in produtos_por_id and _produto_e_servico(produto) != _produto_e_servico(produtos_por_id[novo]):
                raise ValueError(
                    f"Conflito no ID do produto {novo}: serviço e produto comum."
                )
            mapa_produtos[antigo] = novo
            produtos_por_id[novo] = {**produtos_por_id.get(novo, {}), **produto, "id_produto": novo}
        mapa_pedidos = remapear_ids(
            pedidos, "id_pedido", ids_pedidos, nome_fonte
        )
        combinado["filiais"].extend(fonte.get("filiais", []))

        for cliente in clientes:
            antigo = int(cliente["id_cliente"])
            combinado["clientes"].append({
                **cliente,
                "id_cliente": mapa_clientes[antigo],
            })
        for pedido in pedidos:
            itens = [
                {**item, "id_produto": mapa_produtos[int(item["id_produto"])]}
                for item in pedido.get("itens", [])
            ]
            combinado["pedidos"].append({
                **pedido,
                "id_pedido": mapa_pedidos[int(pedido["id_pedido"])],
                "id_cliente": mapa_clientes[int(pedido["id_cliente"])],
                "id_filial": int(pedido.get("id_filial", 3)),
                "itens": itens,
            })
        combinado["concorrentes"].extend(fonte.get("concorrentes", []))

    combinado["produtos"] = [produtos_por_id[id_produto] for id_produto in sorted(produtos_por_id)]

    concorrentes_unicos = {
        (item.get("data"), item.get("vendas")): item
        for item in combinado["concorrentes"]
    }
    combinado["concorrentes"] = list(concorrentes_unicos.values())
    combinado["filiais"] = list({
        int(filial["id_filial"]): filial
        for filial in combinado["filiais"]
    }.values())
    return combinado


def _buscar_dados_oracle(buscar_dados, conectar_origem):
    conexao = conectar_origem()
    try:
        return buscar_dados(conexao)
    finally:
        conexao.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Converte dados MongoDB Atlas em INSERTs Oracle.")
    parser.add_argument(
        "--json-dir",
        help="Diretório contendo os 3 JSONs de exemplo. Se omitido, conecta ao MongoDB Atlas.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT_SQL", str(OUTPUT_DIR / "carga_oracle.sql")),
        help="Arquivo SQL de saída.",
    )
    parser.add_argument(
        "--postgresql",
        action="store_true",
        help="Extrai do PostgreSQL/Supabase em vez do MongoDB/JSON.",
    )
    parser.add_argument(
        "--todas-fontes",
        action="store_true",
        help="Combina MongoDB, PostgreSQL e Oracle antes de gerar a carga.",
    )
    parser.add_argument(
        "--load-oracle",
        action="store_true",
        help="Após gerar o SQL, executar o script no banco Oracle usando vars ORACLE_*.",
    )
    args = parser.parse_args()

    if args.todas_fontes:
        from src.leitores.oracle import buscar_dados, conectar_origem
        from src.leitores.postgresql import carregar_dados_postgresql

        dados_oracle = dados_oracle_para_contrato(
            _buscar_dados_oracle(buscar_dados, conectar_origem)
        )
        dados_mongo = carregar_dados(args)
        dados_postgresql = carregar_dados_postgresql()
        dados = _combinar_fontes([
            {**dados_mongo, "nome_fonte": "MongoDB"},
            {**dados_postgresql, "nome_fonte": "PostgreSQL"},
            {**dados_oracle, "nome_fonte": "Oracle"},
        ])
        sql = gerar_sql(dados)
        caminho = _caminho_saida(args.output)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(sql, encoding="utf-8")
        print(f"Todas as fontes combinadas! SQL gerado: {caminho.resolve()}")
        if args.load_oracle:
            from src.sql.loader import execute_file
            print("Executando carga no Oracle...")
            execute_file(caminho)
            print("Carga no Oracle concluída.")
        return

    if args.postgresql:
        from src.leitores.postgresql import carregar_dados_postgresql
        from src.sql.loader import execute_file

        dados = carregar_dados_postgresql()
        sql = gerar_sql(dados)
        caminho = _caminho_saida(args.output)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(sql, encoding="utf-8")
        print(f"Conversão PostgreSQL concluída! SQL gerado: {caminho.resolve()}")
        if args.load_oracle:
            print("Executando carga no Oracle...")
            execute_file(caminho)
            print("Carga no Oracle concluída.")
        return

    dados = carregar_dados(args)
    sql = gerar_sql(dados)
    caminho_saida = _caminho_saida(args.output)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(sql, encoding="utf-8")
    quantidade_itens = sum(len(pedido.get("itens", [])) for pedido in dados["pedidos"])
    print("Conversão concluída!")
    print(f"Clientes:     {len(dados['clientes'])}")
    print(f"Produtos:     {len(dados['produtos'])}")
    print(f"Pedidos:      {len(dados['pedidos'])}")
    print(f"Itens/vendas: {quantidade_itens}")
    print(f"SQL gerado:   {caminho_saida.resolve()}")
    mapa_categorias = criar_mapa_categorias(dados["produtos"])
    mapa_estado_civil = criar_mapa_estado_civil(dados["clientes"])
    if mapa_categorias:
        print("\nMapa Categoria (texto -> número):")
        for texto, codigo in mapa_categorias.items():
            print(f"  {codigo}: {texto}")
    if mapa_estado_civil:
        print("\nMapa Estado_Civil (texto -> número):")
        for texto, codigo in mapa_estado_civil.items():
            print(f"  {codigo}: {texto}")
    if args.load_oracle:
        from src.sql.loader import execute_file

        print("Executando carga no Oracle...")
        execute_file(caminho_saida)
        print("Carga no Oracle concluída.")
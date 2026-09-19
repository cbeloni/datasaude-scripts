"""CLI do pipeline Gestantes Uruguaiana/RS.

Uso (a partir da raiz do projeto):
    python -m uruguaiana.run_pipeline --etapa 0      # cria as 3 tabelas
    python -m uruguaiana.run_pipeline --etapa 1      # extrai + saneia datas
    python -m uruguaiana.run_pipeline --etapa 3      # geocodifica
    python -m uruguaiana.run_pipeline --etapa 4      # carrega gestantes
    python -m uruguaiana.run_pipeline --etapa 5      # coleta Open-Meteo
    python -m uruguaiana.run_pipeline --etapa 6      # agrega exposição diária
    python -m uruguaiana.run_pipeline --etapa 7      # carrega exposição
    python -m uruguaiana.run_pipeline --todas
    python -m uruguaiana.run_pipeline --validar

Opções:
    --force          ignora o cache de geocodificação
    --simular        não grava nada no banco (etapas 4 e 7)
"""

import argparse
import sys
import time

from uruguaiana.config_uruguaiana import TABELAS_DO_CONTEXTO


def etapa0_criar_tabelas():
    from uruguaiana.repositorio import criar_tabelas

    print("=" * 78)
    print("[E0] Criando as tabelas do contexto (tabelas existentes são ignoradas)")
    print("=" * 78)
    criar_tabelas()
    from uruguaiana.repositorio import tabelas_existentes

    existentes = tabelas_existentes()
    print(f"   presentes agora: {sorted(t for t in TABELAS_DO_CONTEXTO if t in existentes)}")


def etapa1():
    from uruguaiana.extrair_gestantes import executar as rodar

    print("=" * 78)
    print("[E1+E2] Extração, unificação e saneamento de datas")
    print("=" * 78)
    return rodar()


def etapa3(force=False, simular=False):
    from uruguaiana.geocode_client import executar, persistir_cache_da_execucao

    print("=" * 78)
    print("[E3] Geocodificação via OpenCage")
    print("=" * 78)
    saida = executar(force=force)

    if simular:
        print("   [simular] cache não persistido no banco")
    else:
        # Persiste a partir do cache em memória da própria execução.
        # NÃO reler o espelho local: ele pode estar ausente, desatualizado ou
        # ter sido reescrito por outra ferramenta, e itens incompletos
        # violariam o NOT NULL de `endereco_original`.
        persistir_cache_da_execucao()
    return saida


def etapa4(simular=False):
    from uruguaiana.carregar_dados import carregar_gestantes

    print("=" * 78)
    print("[E4] Carga de gestantes_uruguaiana")
    print("=" * 78)
    if simular:
        print("   [simular] nada foi gravado")
        return 0
    return carregar_gestantes()


def etapa5():
    import pandas as pd

    from uruguaiana.config_uruguaiana import CSV_03_GEOCODE
    from uruguaiana.openmeteo_client import (
        OpenMeteoIndisponivel,
        chave_grade,
        coletar_ar,
        coletar_temperatura,
        contar_blocos,
    )

    print("=" * 78)
    print("[E5] Coleta das séries horárias na Open-Meteo (uma vez por célula)")
    print("=" * 78)

    gestantes = pd.read_csv(CSV_03_GEOCODE)
    inicio = pd.to_datetime(gestantes["janela_inicio"]).min().date().isoformat()
    fim = pd.to_datetime(gestantes["data_referencia"]).max().date().isoformat()

    gestantes["grade"] = [
        chave_grade(lat, lng)
        for lat, lng in zip(gestantes["latitude"], gestantes["longitude"])
    ]

    celulas = sorted(gestantes["grade"].unique())
    blocos = contar_blocos(inicio, fim)
    print(f"   intervalo global: {inicio} -> {fim}")
    print(f"   células distintas: {len(celulas)} (de {len(gestantes)} gestantes)")
    print(f"   blocos por API: {blocos} | requisições previstas: "
          f"{len(celulas) * 2 * blocos} (no máximo)")

    falhas: list[tuple[str, str]] = []

    for i, celula in enumerate(celulas, start=1):
        linha = gestantes[gestantes["grade"] == celula].iloc[0]
        lat, lng = float(linha["latitude"]), float(linha["longitude"])
        n = int((gestantes["grade"] == celula).sum())

        try:
            corpo_ar = coletar_ar(lat, lng, inicio, fim)
            corpo_temp = coletar_temperatura(lat, lng, inicio, fim)
        except OpenMeteoIndisponivel as erro:
            print(f"   [{i}/{len(celulas)}] célula {celula} ({n} gestantes) FALHOU")
            print(f"      {erro}")
            falhas.append((celula, str(erro)))
            continue

        print(
            f"   [{i}/{len(celulas)}] célula {celula} ({n} gestantes) "
            f"| ar: {len(corpo_ar['hourly']['time'])} h @ "
            f"({corpo_ar['latitude']}, {corpo_ar['longitude']}) "
            f"| meteo: {len(corpo_temp['hourly']['time'])} h @ "
            f"({corpo_temp['latitude']}, {corpo_temp['longitude']})"
        )

    if falhas:
        print()
        print(f"   ATENÇÃO: {len(falhas)} de {len(celulas)} células não foram baixadas.")
        print("   As células que deram certo ficaram em cache. Rode novamente")
        print("   apenas esta etapa para buscar o que falta:")
        print("       ./uruguaiana/executar_pipeline.sh --etapa 5")
        print()
        for celula, motivo in falhas:
            print(f"     - {celula}: {motivo[:110]}")
        raise SystemExit(1)

    print(f"   todas as {len(celulas)} células coletadas com sucesso")


def etapa6():
    from uruguaiana.agregar_exposicao import executar as rodar

    print("=" * 78)
    print("[E6] Agregação diária da exposição")
    print("=" * 78)
    return rodar()


def etapa7(simular=False):
    from uruguaiana.carregar_dados import carregar_exposicao

    print("=" * 78)
    print("[E7] Carga de gestantes_exposicao_diaria")
    print("=" * 78)
    if simular:
        print("   [simular] nada foi gravado")
        return 0
    return carregar_exposicao()


def validar():
    from uruguaiana.carregar_dados import resumo_banco

    print("=" * 78)
    print("[VALIDAÇÃO] Critérios de aceite (PLANEJAMENTO §10)")
    print("=" * 78)
    r = resumo_banco()

    def marca(cond, texto):
        print(f"   {'OK ' if cond else 'FALHA'}  {texto}")

    print(f"   gestantes: {r['gestantes']} | por grupo: {r['por_grupo']}")
    print(f"   data_status: {r['data_status']}")
    print(f"   geo_status: {r['geo_status']}")
    print(f"   geo_default: {r['geo_default']}")
    print(f"   exposição: {r['exposicao']} linhas "
          f"| {r['gestantes_com_exposicao']} gestantes distintas")
    print(f"   geocode_cache: {r['geocode_cache']} endereços")
    print(f"   dias_janela: {r['dias_janela']}")
    print(
        f"   contiguidade: mes não contíguo={r['mes_nao_contiguo']} | "
        f"sem 9 meses={r['gestantes_sem_9_meses']} | "
        f"dias não contíguos={r['dias_nao_contiguos']} | "
        f"coleta fora do mês 9={r['coleta_fora_do_mes_9']}"
    )
    print()

    marca(r["gestantes"] == 708, "gestantes = 708")
    marca(r["por_grupo"].get("Grupo1") == 504, "Grupo1 = 504")
    marca(r["por_grupo"].get("Grupo_2") == 204, "Grupo_2 = 204")
    marca(r["sem_coordenada"] == 0, "nenhuma latitude/longitude nula")
    marca(r["sem_exposicao_status"] == 0, "exposicao_status preenchido em todos")
    marca(r["gestantes_com_exposicao"] == 708, "todas as 708 gestantes têm exposição")
    marca(
        abs(r["exposicao"] - 194877) <= 194877 * 0.01,
        f"exposição ≈ 194.877 (obtido: {r['exposicao']})",
    )
    marca(r["dias_janela"][0] == 274 and r["dias_janela"][1] == 277,
          f"dias_janela entre 274 e 277 (obtido: {r['dias_janela']})")
    marca(r["data_status"].get("OK") == 686, "data_status OK = 686")
    marca(r["data_status"].get("FALLBACK_CARIMBO") == 21, "FALLBACK_CARIMBO = 21")
    marca(r["data_status"].get("CORRIGIDA") == 1, "CORRIGIDA = 1")
    marca(r["geo_status"].get("SEM_ENDERECO") == 154, "SEM_ENDERECO = 154")
    marca(r["mes_nao_contiguo"] == 0, "mes_relativo monotônico, sem saltos")
    marca(r["gestantes_sem_9_meses"] == 0, "9 meses distintos por gestante")
    marca(r["dias_nao_contiguos"] == 0, "série diária contígua (sem buracos)")
    marca(r["coleta_fora_do_mes_9"] == 0, "dia da coleta sempre no mês 9")


ETAPAS = {
    "0": lambda a: etapa0_criar_tabelas(),
    "1": lambda a: etapa1(),
    "3": lambda a: etapa3(force=a.force, simular=a.simular),
    "4": lambda a: etapa4(simular=a.simular),
    "5": lambda a: etapa5(),
    "6": lambda a: etapa6(),
    "7": lambda a: etapa7(simular=a.simular),
}

ORDEM = ["0", "1", "3", "4", "5", "6", "7"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pipeline Gestantes Uruguaiana/RS")
    parser.add_argument("--etapa", choices=ORDEM, help="Executa uma etapa")
    parser.add_argument("--todas", action="store_true", help="Executa todas as etapas")
    parser.add_argument("--validar", action="store_true", help="Roda os critérios de aceite")
    parser.add_argument("--force", action="store_true", help="Ignora o cache de geocodificação")
    parser.add_argument("--simular", action="store_true", help="Não grava no banco (E4/E7)")
    args = parser.parse_args(argv)

    if args.validar:
        validar()
        return 0

    etapas = ORDEM if args.todas else ([args.etapa] if args.etapa else [])
    if not etapas:
        parser.print_help()
        return 1

    inicio = time.time()
    for numero in etapas:
        marco = time.time()
        ETAPAS[numero](args)
        print(f"   (etapa {numero} levou {time.time() - marco:.1f}s)\n")

    print(f"Tempo total: {time.time() - inicio:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

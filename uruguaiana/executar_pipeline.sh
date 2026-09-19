#!/usr/bin/env bash
# =============================================================================
# Pipeline — Gestantes Uruguaiana/RS
# =============================================================================
# Lê Dados_gestantes.xlsx (2 abas), geocodifica os endereços via OpenCage,
# coleta a exposição ambiental (PM10, PM2.5, temperatura) na Open-Meteo e
# persiste em duas tabelas do MySQL `datasaude`.
#
# TABELAS GERENCIADAS (somente estas são tocadas):
#   gestantes_uruguaiana · gestantes_exposicao_diaria · geocode_cache
# Nenhuma outra tabela é lida, alterada ou removida por este script.
#
# -----------------------------------------------------------------------------
# USO
# -----------------------------------------------------------------------------
#   ./uruguaiana/executar_pipeline.sh                    # executa TUDO
#   ./uruguaiana/executar_pipeline.sh --validar          # só os critérios de aceite
#   ./uruguaiana/executar_pipeline.sh --etapa 3          # só a etapa 3
#   ./uruguaiana/executar_pipeline.sh --de 3             # da etapa 3 em diante
#
# OPÇÕES
#   --etapa N        executa apenas a etapa N (0,1,3,4,5,6,7)
#   --de N           executa da etapa N até o fim
#   --ate N          executa da etapa 0 até a etapa N
#   --force          ignora o cache de geocodificação (gasta quota da API!)
#   --simular        não grava nas etapas 4 e 7
#   --sem-pausa      não pausa entre as etapas
#   --ajuda          mostra esta mensagem
#
# As etapas são retomáveis. Reexecutar o pipeline inteiro é seguro:
# todas as cargas usam UPSERT e todas as APIs têm cache.
# =============================================================================

set -Eeuo pipefail

# ------------------------------------------------------------------ caminhos
DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ_PROJETO="$(cd "${DIR_SCRIPT}/.." && pwd)"
DIR_OUTPUT="${DIR_SCRIPT}/output"
ARQUIVO_LOG="${DIR_OUTPUT}/pipeline_$(date '+%Y%m%d_%H%M%S').log"

mkdir -p "${DIR_OUTPUT}"

# ------------------------------------------------------------------- opções
ETAPA_UNICA=""
ETAPA_DE="0"
ETAPA_ATE="7"
FORCE=""
SIMULAR=""
PAUSA="1"
VALIDAR_APENAS=""

ORDEM=(0 1 3 4 5 6 7)

uso() {
    sed -n '2,31p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --etapa)    ETAPA_UNICA="${2:-}"; shift 2 ;;
        --de)       ETAPA_DE="${2:-}"; shift 2 ;;
        --ate)      ETAPA_ATE="${2:-}"; shift 2 ;;
        --force)    FORCE="--force"; shift ;;
        --simular)  SIMULAR="--simular"; shift ;;
        --sem-pausa) PAUSA="0"; shift ;;
        --validar)  VALIDAR_APENAS="1"; shift ;;
        -h|--help|--ajuda) uso ;;
        *) echo "Opção desconhecida: $1" >&2; echo "Use --ajuda." >&2; exit 2 ;;
    esac
done

# ------------------------------------------------------------------ logging
exec > >(tee -a "${ARQUIVO_LOG}") 2>&1

titulo() {
    printf '\n'
    printf '=%.0s' {1..78}; printf '\n'
    printf '  %s\n' "$1"
    printf '=%.0s' {1..78}; printf '\n'
}

info()  { printf '   %s\n' "$1"; }
aviso() { printf '   !! %s\n' "$1"; }
erro()  { printf '\n   ERRO: %s\n' "$1" >&2; }

falhou() {
    local codigo=$?
    erro "falha na linha ${1} (código ${codigo}). Log: ${ARQUIVO_LOG}"
    exit "${codigo}"
}
trap 'falhou ${LINENO}' ERR

# ------------------------------------------------------------------- python
PYTHON=""

detectar_python() {
    local candidatos=(
        "${RAIZ_PROJETO}/.venv/bin/python"
        "${VIRTUAL_ENV:-}/bin/python"
        "$(command -v python3 2>/dev/null || true)"
    )
    local cand
    for cand in "${candidatos[@]}"; do
        [[ -n "${cand}" && -x "${cand}" ]] || continue
        if "${cand}" -c 'import pandas, mysql.connector, requests, dotenv, dateutil' 2>/dev/null; then
            PYTHON="${cand}"
            return 0
        fi
    done
    return 1
}

# ------------------------------------------------------------- verificações
verificar_ambiente() {
    titulo "VERIFICAÇÃO DO AMBIENTE"

    if ! detectar_python; then
        erro "Nenhum Python com as dependências necessárias foi encontrado."
        info "Esperado: ${RAIZ_PROJETO}/.venv/bin/python"
        info "Instale com: ./install_deps_uv.sh   (ou uv pip install -r requirements.txt)"
        exit 1
    fi
    info "python : ${PYTHON}"

    if [[ ! -f "${RAIZ_PROJETO}/.env" ]]; then
        erro "Arquivo .env não encontrado em ${RAIZ_PROJETO}"
        exit 1
    fi
    info ".env   : ok"

    if ! grep -q '^OPENCAGE_API_KEY=' "${RAIZ_PROJETO}/.env"; then
        aviso "OPENCAGE_API_KEY ausente no .env — a etapa 3 vai falhar."
    else
        info "chave  : OPENCAGE_API_KEY presente"
    fi

    local xlsx="/Users/cauebeloni/Documents/Projeto Pensi/dados/uruguaiana-rs/Dados_gestantes.xlsx"
    if [[ ! -f "${xlsx}" ]]; then
        erro "Planilha não encontrada: ${xlsx}"
        exit 1
    fi
    if ls /Users/cauebeloni/Documents/Projeto\ Pensi/dados/uruguaiana-rs/.~lock.* >/dev/null 2>&1; then
        aviso "A planilha parece ABERTA no Excel (arquivo .~lock presente)."
        aviso "Feche o Excel antes de continuar, senão a leitura pode falhar."
    fi
    info "planilha: ok"
}

# ------------------------------------------------------------------ etapas
rodar_etapa() {
    local numero="$1"
    local inicio fim duracao

    inicio=$(date +%s)

    case "${numero}" in
        0) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 0 ;;
        1) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 1 ;;
        3)
            aviso "A etapa 3 faz ~547 chamadas à OpenCage com throttle de 1 req/s."
            aviso "Duração esperada: 10 a 15 minutos. Não interrompa."
            "${PYTHON}" -m uruguaiana.run_pipeline --etapa 3 ${FORCE} ${SIMULAR}
            ;;
        4) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 4 ${SIMULAR} ;;
        5) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 5 ;;
        6) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 6 ;;
        7) "${PYTHON}" -m uruguaiana.run_pipeline --etapa 7 ${SIMULAR} ;;
    esac

    fim=$(date +%s)
    duracao=$((fim - inicio))
    titulo "ETAPA ${numero} CONCLUÍDA em ${duracao}s"
}

pausar() {
    [[ "${PAUSA}" == "1" ]] || return 0
    [[ -t 0 ]] || return 0
    printf '\n   Pressione ENTER para continuar (ou Ctrl+C para abortar)... '
    read -r _ || true
}

descricao_etapa() {
    case "$1" in
        0) echo "Criar as 3 tabelas no MySQL (existentes são ignoradas)" ;;
        1) echo "Extrair as 2 abas e sanear as datas (E1 + E2)" ;;
        3) echo "Geocodificar os endereços via OpenCage (E3)" ;;
        4) echo "Carregar gestantes_uruguaiana (E4)" ;;
        5) echo "Coletar séries horárias na Open-Meteo, por célula de grade (E5)" ;;
        6) echo "Agregar a exposição diária dos 9 meses (E6)" ;;
        7) echo "Carregar gestantes_exposicao_diaria (E7)" ;;
    esac
}

# ------------------------------------------------------------------ execução
validar_apenas() {
    titulo "VALIDAÇÃO DOS CRITÉRIOS DE ACEITE"
    "${PYTHON}" -m uruguaiana.run_pipeline --validar
    titulo "FIM"
    info "Log completo: ${ARQUIVO_LOG}"
}

executar() {
    local etapas=()

    if [[ -n "${ETAPA_UNICA}" ]]; then
        etapas=("${ETAPA_UNICA}")
    else
        local n
        for n in "${ORDEM[@]}"; do
            if (( n >= ETAPA_DE && n <= ETAPA_ATE )); then
                etapas+=("${n}")
            fi
        done
    fi

    if [[ ${#etapas[@]} -eq 0 ]]; then
        erro "Nenhuma etapa selecionada (--de ${ETAPA_DE} --ate ${ETAPA_ATE})."
        exit 2
    fi

    titulo "PIPELINE GESTANTES URUGUAIANA/RS"
    info "projeto : ${RAIZ_PROJETO}"
    info "log     : ${ARQUIVO_LOG}"
    info "etapas  : ${etapas[*]}"
    [[ -n "${FORCE}" ]]   && aviso "MODO --force: o cache de geocodificação será ignorado"
    [[ -n "${SIMULAR}" ]] && aviso "MODO --simular: nada será gravado nas etapas 4 e 7"

    verificar_ambiente

    local total_inicio total_fim numero indice
    total_inicio=$(date +%s)

    indice=0
    for numero in "${etapas[@]}"; do
        indice=$((indice + 1))
        printf '\n\n'
        printf '>>> ETAPA %s — %s\n' "${numero}" "$(descricao_etapa "${numero}")"
        rodar_etapa "${numero}"
        # a última etapa não precisa de pausa
        if (( indice < ${#etapas[@]} )); then
            pausar
        fi
    done

    total_fim=$(date +%s)

    titulo "PIPELINE CONCLUÍDO em $((total_fim - total_inicio))s"

    printf '\n'
    "${PYTHON}" -m uruguaiana.run_pipeline --validar

    printf '\n'
    info "Artefatos gerados em: ${DIR_OUTPUT}"
    info "Log completo      : ${ARQUIVO_LOG}"
    printf '\n'
}

cd "${RAIZ_PROJETO}"

if [[ -n "${VALIDAR_APENAS}" ]]; then
    detectar_python || { erro "Python com dependências não encontrado."; exit 1; }
    validar_apenas
else
    executar
fi

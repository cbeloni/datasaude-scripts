import numpy as np
import pandas as pd


def _read_nhanes_csv(path: str) -> pd.DataFrame:
    """Lê CSVs NHANES com delimitador automático e UTF-8/Latin-1."""
    try:
        return pd.read_csv(path, sep=None, engine='python', encoding='utf-8-sig')
    except UnicodeDecodeError:
        return pd.read_csv(path, sep=None, engine='python', encoding='latin-1')


def process_nhanes_diabetes_data(
    demographic_path: str,
    examination_path: str,
    medications_path: str,
    diet_path: str,
    labs_path: str,
    questionnaire_path: str,
    output_path: str = "nhanes_diabetes_processed.csv"
) -> pd.DataFrame:
    """
    Carrega, mescla e limpa os CSVs consolidados do NHANES para predição de
    diabetes.

    Os campos usados pelo modelo estão distribuídos desta forma:
    - demographic.csv: idade, gênero, raça/etnia e renda relativa
    - examination.csv: medidas corporais e pressão arterial
    - diet.csv: calorias e macronutrientes
    - labs.csv: glicose, colesterol, creatinina e enzimas hepáticas
    - questionnaire.csv: diabetes, histórico familiar, hipertensão e álcool

    medications.csv é recebido e validado junto com os demais arquivos, mas
    não é incorporado às variáveis atuais para evitar duplicação por paciente
    e possível vazamento do diagnóstico por nomes de medicamentos.
    """
    # 1. Carregamento dos arquivos consolidados
    files = {
        'demographic.csv': demographic_path,
        'examination.csv': examination_path,
        'medications.csv': medications_path,
        'diet.csv': diet_path,
        'labs.csv': labs_path,
        'questionnaire.csv': questionnaire_path,
    }
    dataframes = {name: _read_nhanes_csv(path) for name, path in files.items()}

    # 2. Validar a localização dos campos esperados antes de selecionar colunas
    expected_fields = {
        'demographic.csv': [
            'SEQN', 'RIDAGEYR', 'RIAGENDR', 'RIDRETH1', 'INDFMPIR'
        ],
        'examination.csv': [
            'SEQN', 'BMXWT', 'BMXHT', 'BMXBMI', 'BMXWAIST', 'BPXPLS',
            'BPXSY1', 'BPXDI1'
        ],
        'diet.csv': [
            'SEQN', 'DR1TKCAL', 'DR1TPROT', 'DR1TCARB', 'DR1TSUGR',
            'DR1TFIBE', 'DR1TTFAT'
        ],
        'labs.csv': ['SEQN', 'LBXSGL', 'LBXSCH', 'LBXSCR', 'LBXSAL', 'LBXSATSI'],
        'questionnaire.csv': ['SEQN', 'DIQ010', 'MCQ300C', 'BPQ020', 'ALQ101'],
    }
    missing_fields = {
        filename: [field for field in fields if field not in dataframes[filename].columns]
        for filename, fields in expected_fields.items()
    }
    missing_fields = {filename: fields for filename, fields in missing_fields.items() if fields}
    if missing_fields:
        details = '; '.join(
            f"{filename}: {', '.join(fields)}"
            for filename, fields in missing_fields.items()
        )
        raise ValueError(f"Campos esperados não encontrados nos arquivos: {details}")

    print("Campos esperados validados:")
    for filename, fields in expected_fields.items():
        print(f"- {filename}: {', '.join(fields)}")

    demo = dataframes['demographic.csv'][
        ['SEQN', 'RIDAGEYR', 'RIAGENDR', 'RIDRETH1', 'INDFMPIR']
    ]
    examination = dataframes['examination.csv'][
        ['SEQN', 'BMXWT', 'BMXHT', 'BMXBMI', 'BMXWAIST', 'BPXPLS', 'BPXSY1', 'BPXDI1']
    ]
    diet = dataframes['diet.csv'][
        ['SEQN', 'DR1TKCAL', 'DR1TPROT', 'DR1TCARB', 'DR1TSUGR', 'DR1TFIBE', 'DR1TTFAT']
    ]
    labs = dataframes['labs.csv'][
        ['SEQN', 'LBXSGL', 'LBXSCH', 'LBXSCR', 'LBXSAL', 'LBXSATSI']
    ]
    questionnaire = dataframes['questionnaire.csv'][
        ['SEQN', 'DIQ010', 'MCQ300C', 'BPQ020', 'ALQ101']
    ]

    # 3. Merge dos dataframes através do ID único (SEQN)
    df = (demo.merge(examination, on='SEQN', how='inner')
          .merge(diet, on='SEQN', how='inner')
          .merge(labs, on='SEQN', how='inner')
          .merge(questionnaire, on='SEQN', how='inner'))

    # 4. Regra Binarização da Variável Alvo (DIQ010)
    # 1 = Yes -> 1
    # 2 = No -> 0
    # 3 (Borderline), 7 (Refused), 9 (Don't know) -> Descartados para treino supervisionado
    df = df[df['DIQ010'].isin([1, 2])].copy()
    df['diabetes'] = np.where(df['DIQ010'] == 1, 1, 0)
    df.drop(columns=['DIQ010'], inplace=True)

    # 5. Tratar Histórico Familiar (MCQ300C: 1=Sim, 2=Não)
    df = df[df['MCQ300C'].isin([1, 2])].copy()
    df['family_history'] = np.where(df['MCQ300C'] == 1, 1, 0)
    df.drop(columns=['MCQ300C'], inplace=True)

    # 6. Tratamento de Ausentes: campos sem valor serão preenchidos com zero
    df.fillna(0, inplace=True)

    # 7. Renomear colunas para padrão limpo
    df.rename(columns={
        'RIDAGEYR': 'age',
        'RIAGENDR': 'gender',
        'RIDRETH1': 'race_ethnicity',
        'INDFMPIR': 'income_poverty_ratio',
        'BMXWT': 'weight_kg',
        'BMXHT': 'height_cm',
        'BMXBMI': 'bmi',
        'BMXWAIST': 'waist_circ',
        'BPXPLS': 'pulse',
        'BPXSY1': 'systolic_bp',
        'BPXDI1': 'diastolic_bp',
        'DR1TKCAL': 'diet_kcal',
        'DR1TPROT': 'diet_protein',
        'DR1TCARB': 'diet_carbohydrate',
        'DR1TSUGR': 'diet_sugar',
        'DR1TFIBE': 'diet_fiber',
        'DR1TTFAT': 'diet_total_fat',
        'LBXSGL': 'glucose',
        'LBXSCH': 'total_cholesterol',
        'LBXSCR': 'creatinine',
        'LBXSAL': 'albumin',
        'LBXSATSI': 'ast',
        'BPQ020': 'hypertension_history',
        'ALQ101': 'alcohol_use'
    }, inplace=True)

    # Reordenar mantendo a coluna diabetes no final
    features = [
        'SEQN', 'age', 'gender', 'race_ethnicity', 'income_poverty_ratio',
        'weight_kg', 'height_cm', 'bmi', 'waist_circ', 'pulse', 'systolic_bp',
        'diastolic_bp', 'diet_kcal', 'diet_protein', 'diet_carbohydrate',
        'diet_sugar', 'diet_fiber', 'diet_total_fat', 'glucose',
        'total_cholesterol', 'creatinine', 'albumin', 'ast',
        'hypertension_history', 'alcohol_use', 'family_history', 'diabetes'
    ]
    df = df[features]

    # Exportar arquivo final
    df.to_csv(output_path, index=False, sep='|')
    print(f"Dataset processado com sucesso! Total de registros: {len(df)}")
    print(f"Distribuição da variável alvo (diabetes):\n{df['diabetes'].value_counts()}")

    return df

# Exemplo de execução:
df_final = process_nhanes_diabetes_data(
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/demographic.csv',
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/examination.csv',
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/medications.csv',
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/diet.csv',
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/labs.csv',
    '/Users/cauebeloni/Documents/Projeto Pensi/artigo/dataset/NHANES/questionnaire.csv',
    output_path='nhanes_diabetes_processed.csv',
)

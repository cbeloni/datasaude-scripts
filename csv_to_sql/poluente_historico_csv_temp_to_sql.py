import os
from datetime import datetime

def process_csv_file(csv_file_path):
    codigo_estacao = None
    nome_estacao = None
    dados = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        if len(lines) > 3:
            codigo_line = lines[3].strip()
            if 'Código da estação' in codigo_line or 'Cdigo da estao' in codigo_line:
                codigo_estacao = codigo_line.split(';')[1].strip().replace(',', '')
        
        if len(lines) > 4:
            nome_line = lines[4].strip()
            if 'Nome da estação' in nome_line or 'Nome da estao' in nome_line:
                nome_estacao = nome_line.split(';')[1].strip()
        
        if len(lines) > 8:
            for i in range(8, len(lines)):
                line = lines[i].strip()
                if line and ';' in line:
                    parts = line.split(';')
                    if len(parts) >= 3:
                        data = parts[0].strip()
                        hora = parts[1].strip()
                        valor = parts[2].strip()
                        valor_int = valor.split(',')[0] if ',' in valor else valor
                        dados.append({
                            'data': data,
                            'hora': hora,
                            'valor': valor_int
                        })
                        
    
    return codigo_estacao, nome_estacao, dados

def main():
    csv_temp_folder = 'csv_temp'
        
    csv_files = [f for f in os.listdir(csv_temp_folder) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(csv_temp_folder, csv_file)
        print(f"\nProcessando arquivo: {csv_file}")
        
        try:
            codigo_estacao, nome_estacao, dados = process_csv_file(csv_path)
            
            print(f"Código da Estação: {codigo_estacao}")
            print(f"Nome da Estação: {nome_estacao}")
            print(f"Total de registros: {len(dados)}")
            
            for i, registro in enumerate(dados):
                print(f"Registro {i+1}: Data: {registro['data']}, Hora: {registro['hora']}, Valor: {registro['valor']}")
            
                
        except Exception as e:
            print(f"Erro ao processar {csv_file}: {str(e)}")

if __name__ == "__main__":
    main()
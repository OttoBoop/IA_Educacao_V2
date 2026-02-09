#!/usr/bin/env python3
import requests
import json

BASE = 'https://ia-educacao-v2.onrender.com'

print('=== VERIFICANDO SISTEMA ONLINE ===')

# 1. Verificar matérias
try:
    r = requests.get(f'{BASE}/api/materias', timeout=30)
    print(f'Matérias - Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'  Total: {len(data)} matérias')
        if data:
            print(f'  Exemplo: {data[0]["nome"]} (ID: {data[0]["id"]})')
    else:
        print(f'  Erro: {r.text}')
except Exception as e:
    print(f'  Erro de conexão: {e}')

# 2. Verificar turmas
try:
    r = requests.get(f'{BASE}/api/turmas', timeout=30)
    print(f'Turmas - Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'  Total: {len(data)} turmas')
        if data:
            print(f'  Exemplo: {data[0]["nome"]} (ID: {data[0]["id"]})')
    else:
        print(f'  Erro: {r.text}')
except Exception as e:
    print(f'  Erro de conexão: {e}')

# 3. Verificar atividades
try:
    r = requests.get(f'{BASE}/api/atividades', timeout=30)
    print(f'Atividades - Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'  Total: {len(data)} atividades')
        if data:
            print(f'  Exemplo: {data[0]["nome"]} (ID: {data[0]["id"]})')
    else:
        print(f'  Erro: {r.text}')
except Exception as e:
    print(f'  Erro de conexão: {e}')

print('\n=== TENTANDO GERAR RELATÓRIO ===')

# Se houver atividades, tentar gerar relatório
try:
    r_atividades = requests.get(f'{BASE}/api/atividades', timeout=30)
    if r_atividades.status_code == 200:
        atividades = r_atividades.json()
        if atividades:
            atividade_id = atividades[0]["id"]
            print(f'Tentando gerar relatório para atividade: {atividade_id}')

            # Tentar gerar relatório
            payload = {
                "atividade_id": atividade_id,
                "tipos_relatorios": ["ranking", "estatisticas"],
                "formato": "json"
            }

            r_relatorio = requests.post(f'{BASE}/api/pipeline/gerar-relatorios',
                                     json=payload, timeout=60)
            print(f'Relatório - Status: {r_relatorio.status_code}')
            if r_relatorio.status_code == 200:
                data = r_relatorio.json()
                print('Relatório gerado com sucesso!')
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
            else:
                print(f'Erro: {r_relatorio.text}')
        else:
            print('Nenhuma atividade encontrada')
    else:
        print('Erro ao buscar atividades')
except Exception as e:
    print(f'Erro ao gerar relatório: {e}')
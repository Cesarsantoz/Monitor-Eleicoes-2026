#!/usr/bin/env python3
"""Consulta pública e neutra da totalização presidencial do TSE."""
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = 'https://resultados.tse.jus.br/oficial/ele2026/6258/dados/br/br-c0001-e006258-u.json'
BASE = Path(__file__).resolve().parent
HISTORY = BASE / 'dados' / 'historico.csv'
LATEST = BASE / 'dados' / 'ultimo.json'


def fetch():
    req = Request(URL, headers={'User-Agent': 'MonitorTSE2026/1.0 (consulta pública)', 'Accept': 'application/json'})
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def format_number(n):
    return f'{n:,}'.replace(',', '.')


def extract(data):
    if str(data.get('ele')) != '6258' or str(data.get('t')) != '2' or data.get('f') != 'o':
        raise ValueError('Arquivo não corresponde ao segundo turno presidencial oficial de 2026')
    cargos = [c for c in data['carg'] if str(c.get('cd')) == '1']
    if len(cargos) != 1:
        raise ValueError('Cargo Presidente ausente ou duplicado')
    cand = []
    for agr in cargos[0].get('agr', []):
        for partido in agr.get('par', []):
            for c in partido.get('cand', []):
                cand.append({'numero': str(c['n']), 'nome': c.get('nmu') or c.get('nm'), 'votos': int(c['vap']),
                             'percentual': float(str(c['pvap']).replace(',', '.'))})
    if not cand:
        raise ValueError('Nenhum candidato encontrado')
    cand.sort(key=lambda c: int(c['numero']))
    sections = data.get('s', {})
    result = {'fonte': URL, 'data_tse': data.get('dt'), 'hora_tse': data.get('ht'),
              'consultado_em_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'secoes_totalizadas': int(sections.get('st', 0)),
              'secoes_totalizadas_pct': str(sections.get('pst', '0')),
              'candidatos': cand}
    if len(cand) == 2:
        result['diferenca_votos'] = abs(cand[0]['votos'] - cand[1]['votos'])
        result['diferenca_pontos_percentuais'] = round(abs(cand[0]['percentual'] - cand[1]['percentual']), 2)
    return result


def send_telegram(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat = os.getenv('TELEGRAM_CHAT_ID', '')
    if not token or not chat:
        return
    from urllib.parse import urlencode
    body = urlencode({'chat_id': chat, 'text': message}).encode()
    req = Request(f'https://api.telegram.org/bot{token}/sendMessage', data=body, method='POST')
    with urlopen(req, timeout=20) as response:
        payload = json.load(response)
        if not payload.get('ok'):
            raise ValueError('Telegram não confirmou o envio')


def main():
    data = extract(fetch())
    prev = json.loads(LATEST.read_text(encoding='utf-8')) if LATEST.exists() else None
    # Não usar só o horário: registra mudança efetiva de votos/seções.
    def signature(item):
        return [(c['numero'], c['votos']) for c in item['candidatos']], item['secoes_totalizadas']
    changed = prev is None or signature(prev) != signature(data)
    rows = [f"{c['nome']} ({c['numero']}): {format_number(c['votos'])} votos ({c['percentual']:.2f}%)" for c in data['candidatos']]
    msg = ('TSE • Presidente • 2º turno (2026)\n' + '\n'.join(rows) +
           f"\nDiferença: {format_number(data.get('diferenca_votos', 0))} votos / {data.get('diferenca_pontos_percentuais', 0):.2f} p.p." +
           f"\nSeções totalizadas: {data['secoes_totalizadas_pct']}%" +
           f"\nDados do TSE: {data['data_tse']} {data['hora_tse']}" +
           f"\nFonte: {URL}")
    print(msg)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write('## Apuração presidencial — TSE\n\n' + msg.replace('\n', '  \n') + '\n')
    if changed:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        exists = HISTORY.exists() and HISTORY.stat().st_size > 0
        with HISTORY.open('a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(['consulta_utc', 'data_tse', 'hora_tse', 'secoes_pct', 'numero', 'nome', 'votos', 'percentual'])
            for c in data['candidatos']:
                w.writerow([data['consultado_em_utc'], data['data_tse'], data['hora_tse'],
                            data['secoes_totalizadas_pct'], c['numero'], c['nome'], c['votos'], c['percentual']])
        LATEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        send_telegram(msg)
        print('Mudança detectada e registrada.')
    else:
        print('Sem alteração nos votos/seções; nenhum alerta enviado.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Erro na consulta: {exc}', file=sys.stderr)
        sys.exit(1)

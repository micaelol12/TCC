"""Explicit, bounded integration check with real providers. Uses a synthetic text."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys
from time import monotonic


def main():
    parser = argparse.ArgumentParser(description='Verifica os modos Lab com um texto sintético curto. Consome chamadas dos provedores.')
    parser.add_argument('--live', action='store_true', required=True, help='Autoriza as chamadas reais deste teste.')
    parser.add_argument('--llm-model', help='Verifica somente o modo alto com este modelo permitido.')
    arguments = parser.parse_args()
    if not arguments.live:
        return 1
    os.environ['APP_ENV'] = 'lab'
    os.environ['EXPERIMENTAL_CONFIG_ENABLED'] = 'true'
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from fastapi.testclient import TestClient
    from app.main import app
    text = ('Defendo serviços públicos universais financiados por impostos progressivos, cooperação pacífica entre países, '
            'proteção das liberdades civis e igualdade de direitos para todas as pessoas.')
    report = {'kind': 'live-lab-providers', 'synthetic_text': True, 'results': []}
    with TestClient(app, raise_server_exceptions=False) as client:
        for provider in ('typesafe', 'maritaca', 'gemini'):
            key = getpass(f'Chave {provider} (vazio para pular): ').strip()
            if key:
                response = client.post('/api/lab/api-keys', json={'provider': provider, 'api_key': key})
                if response.status_code != 200:
                    print(f'Não foi possível cadastrar a chave {provider}.')
                    client.delete('/api/lab/session')
                    return 1
                client.headers['X-Lab-Session'] = response.json()['session_token']
            key = ''
        caps = client.get('/api/capabilities').json()
        for mode in (('high',) if arguments.llm_model else ('low', 'medium', 'high')):
            ready = caps['modes'][mode]
            if arguments.llm_model:
                provider = caps['experimental']['model_providers'].get(arguments.llm_model)
                ready = bool(provider and caps['experimental']['providers'][provider])
            if not ready:
                report['results'].append({'mode': mode, 'status': 'skipped-missing-credentials'})
                continue
            start = monotonic()
            # One chunk per mode; force medium review when the JEV confidence is below 1.
            config = {'level_confidence_min': 1.0} if mode == 'medium' else {}
            if arguments.llm_model:
                config['llm_model'] = arguments.llm_model
            response = client.post('/api/analyze', json={'text': text, 'processing_level': mode, 'experiment_config': config})
            result = {'mode': mode, 'http_status': response.status_code, 'seconds': round(monotonic() - start, 2)}
            if response.status_code == 200:
                data = response.json()
                result.update(status='ok' if not data['warnings'] else 'provider-warning', models_used=data['models_used'],
                    logical_calls=data['logical_calls'], warnings=data['warnings'], config_recorded=bool(data.get('config_hash')))
            else:
                result['status'] = 'failed'
            report['results'].append(result)
        client.delete('/api/lab/session')
    output = Path(__file__).resolve().parents[2] / 'test-results' / 'lab-live-providers-report.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return int(any(item['status'] in ('failed', 'provider-warning') for item in report['results']))


if __name__ == '__main__':
    raise SystemExit(main())

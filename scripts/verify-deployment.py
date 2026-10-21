"""Live API smoke check; run with a writable, ignored runtime directory."""
from pathlib import Path
import argparse
import json
import os
import secrets
import time
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:14242')
    parser.add_argument('--runtime-dir', default='data/deployment-check')
    parser.add_argument('--output', default='data/deployment-check/result.json')
    args = parser.parse_args()
    runtime = Path(args.runtime_dir)
    runtime.mkdir(parents=True, exist_ok=True)
    credentials_path = runtime / 'credentials.json'
    if credentials_path.exists():
        credentials = json.loads(credentials_path.read_text())
    else:
        credentials = {'email': 'deployment-check@bnbu.edu.cn', 'password': secrets.token_urlsafe(24)}
        credentials_path.write_text(json.dumps(credentials), encoding='utf-8')
        credentials_path.chmod(0o600)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = None

    def api(method, path, body=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(args.url + path, data=json.dumps(body).encode() if body is not None else None,
                                         headers=headers, method=method)
        with opener.open(request, timeout=360) as response:
            content = response.read()
            return json.loads(content) if response.headers.get_content_type() == 'application/json' else content

    results = {'url': args.url, 'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    results['health'] = api('GET','/health')
    ui = api('GET','/ui/')
    assert b'<html' in ui.lower()
    results['ui'] = 'PASS'
    try:
        api('POST','/api/auth/register', {**credentials, 'confirm_password': credentials['password']})
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
    login = api('POST','/api/auth/login', credentials)
    token = login['token']
    results['auth'] = 'PASS'
    profiles = api('GET','/api/settings/model-profiles')
    profile = profiles[0] if profiles else api('PUT','/api/settings/model-profiles/default', {
        'display_name': 'Deployment verification',
        'provider': 'openai_compatible',
        'base_url': os.getenv('MODEL_BASE_URL', 'https://maas.qianwenaiapi.com/compatible-mode/v1'),
        'model': os.getenv('MODEL_NAME', 'qwen3.6-flash'),
        'context_window_hint': int(os.getenv('MODEL_CONTEXT_WINDOW', '1000000')),
        'supports_streaming': True,
    })
    results['model'] = {'model': profile['model'], 'base_url': profile['base_url']}
    results['model_connection'] = api('POST','/api/settings/model-profiles/test', {})
    run = api('POST','/api/runs', {
        'task_text':'Create a minimal Python function add(a, b) returning a + b and two assert statements. No external dependencies or web search.',
        'intent':'code_homework', 'output_preference':'py', 'search_mode':'off',
        'model_profile_id':profile['id'], 'options':{}})
    run_id = run.get('id') or run.get('run_id')
    assert run_id, run
    for _ in range(120):
        state = api('GET','/api/runs/' + run_id)
        if state['status'] in ('succeeded','failed','cancelled'):
            break
        time.sleep(2)
    results['generation'] = {'run_id':run_id,'status':state['status']}
    assert state['status'] == 'succeeded', state.get('error') or state.get('status')
    artifacts = api('GET',f'/api/runs/{run_id}/artifacts')
    items = artifacts['artifacts']
    source = next(item for item in items if item['path'].endswith('solution.py'))
    source_bytes = api('GET',source['url'])
    assert b'def add' in source_bytes and len(source_bytes) > 20
    manifest = next(item for item in items if item['path'] == 'manifest.json')
    manifest_body = api('GET',manifest['url'])
    assert manifest_body['status'] == 'succeeded'
    results['artifact_download'] = 'PASS'
    results['artifacts'] = artifacts
    results['result'] = 'PASS'
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in results.items() if key != 'artifacts'},indent=2))


if __name__ == '__main__':
    main()

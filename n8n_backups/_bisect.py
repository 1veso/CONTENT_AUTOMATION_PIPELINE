"""
Bisect a pipeline JSON to find which node triggers the
"Cannot read properties of undefined (reading 'execute')" error.

Strategy: import the original snapshot + one node at a time, checking
that PUT returns 200. Snapshot+restore between each test.
"""
import json, uuid, subprocess, sys, copy, time

sys.stdout.reconfigure(encoding='utf-8')

KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMmIwN2MxNy02MjNlLTQ5ODQtYmMzZi1iNTFjY2E2OWY4ZjciLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzc4NjkzNzU0fQ.D8DtiKkYXy7oiPotzGAwmGu4EiJeu9T5BH3aPGP0oWg'
URL = 'https://ops.getautomata.ai/api/v1/workflows/SmtkmTgfCTLZPlN4'

ALLOWED_SETTINGS = {'executionOrder','saveDataErrorExecution','saveDataSuccessExecution',
                    'saveExecutionProgress','saveManualExecutions','executionTimeout','timezone'}

UNRECOGNIZED = {
    '@n8n/n8n-nodes-langchain.googleGemini',
    '@n8n/n8n-nodes-langchain.lmChatGoogleGemini',
}
TYPE_VERSION_CAPS = {'@n8n/n8n-nodes-langchain.agent': 2}


def runc(args):
    return subprocess.run(args, capture_output=True).stdout.decode('utf-8', 'replace')


def get_live():
    return json.loads(runc(['curl', '-s', URL, '-H', f'X-N8N-API-KEY: {KEY}']))


def put_live(wf, label='bisect'):
    payload = {
        'name': wf['name'],
        'nodes': wf['nodes'],
        'connections': wf['connections'],
        'settings': {k: v for k, v in wf.get('settings', {}).items() if k in ALLOWED_SETTINGS}
    }
    tmp = fr'C:\CONTENT_PIPELINE\n8n_backups\_bisect_{label}.json'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    out = runc(['curl', '-s', '-X', 'PUT', URL,
                '-H', f'X-N8N-API-KEY: {KEY}',
                '-H', 'Content-Type: application/json',
                '--data-binary', f'@{tmp}', '-w', '\n%{http_code}'])
    parts = out.rsplit('\n', 1)
    code = parts[-1].strip()
    body = parts[0] if len(parts) > 1 else ''
    return code == '200', body


def patch_node(n, x_off=-2000, y_off=20000):
    """Strip creds, regen id, optionally cap typeVersion, normalize position."""
    new = {k: v for k, v in n.items() if k not in ('credentials', 'webhookId')}
    new['id'] = str(uuid.uuid4())
    new['name'] = n['name'] + ' [BISECT]'
    new['position'] = [x_off, y_off]
    cap = TYPE_VERSION_CAPS.get(n.get('type'))
    if cap is not None and new.get('typeVersion', 1) > cap:
        new['typeVersion'] = cap
    return new


def bisect(json_path):
    snapshot = get_live()
    print(f"Snapshot: {len(snapshot['nodes'])} nodes")

    with open(json_path, encoding='utf-8') as f:
        p = json.load(f)
    src_nodes = [n for n in p['nodes'] if n.get('type') not in UNRECOGNIZED]

    bad = []
    for i, n in enumerate(src_nodes):
        wf = copy.deepcopy(snapshot)
        new_node = patch_node(n)
        wf['nodes'].append(new_node)
        ok, body = put_live(wf, label=f'b{i}')
        status = 'OK' if ok else 'BAD'
        print(f"  [{i+1:3}/{len(src_nodes)}] {status:3} {n['name']:40}  type={n.get('type')} v{n.get('typeVersion')}")
        if not ok:
            print(f"      body={body[:300]}")
            bad.append((n['name'], n.get('type'), n.get('typeVersion'), body[:200]))
            # Force restore
            put_live(snapshot, label=f'rb{i}')
            time.sleep(0.5)
        # else: leave it (we'll remove all in final restore)
    # Always restore
    put_live(snapshot, label='final_rb')
    print(f"\nBad nodes ({len(bad)}):")
    for name, t, v, b in bad:
        print(f"  - {name} | {t} v{v} | {b}")
    return bad


if __name__ == '__main__':
    path = sys.argv[1]
    bisect(path)

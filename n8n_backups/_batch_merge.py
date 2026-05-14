"""
Batch merger: import multiple pipelines into the live canvas in one PUT.

Applies known n8n instance compatibility fixes:
- @n8n/n8n-nodes-langchain.agent: cap typeVersion at 2
- @n8n/n8n-nodes-langchain.googleGemini: replace with TODO sticky (unrecognized on instance)

Strips credentials from all imported nodes (operator binds via UI post-merge).
Strips webhookId from triggers (n8n auto-generates on import).
Prefixes node names with [<slot>] for canvas readability.
Regenerates all UUIDs to avoid collisions.
Normalizes pipeline positions to (0,0) origin then offsets to slot location.
"""
import json, uuid, subprocess, sys, os, copy
sys.stdout.reconfigure(encoding='utf-8')

KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMmIwN2MxNy02MjNlLTQ5ODQtYmMzZi1iNTFjY2E2OWY4ZjciLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzc4NjkzNzU0fQ.D8DtiKkYXy7oiPotzGAwmGu4EiJeu9T5BH3aPGP0oWg'
URL = 'https://ops.getautomata.ai/api/v1/workflows/SmtkmTgfCTLZPlN4'

ALLOWED_SETTINGS = {'executionOrder','saveDataErrorExecution','saveDataSuccessExecution','saveExecutionProgress','saveManualExecutions','executionTimeout','timezone'}

TYPE_VERSION_CAPS = {'@n8n/n8n-nodes-langchain.agent': 2}
UNRECOGNIZED_TYPES = {'@n8n/n8n-nodes-langchain.googleGemini'}

DEFAULT_X_OFFSET = -1200


def runc(args):
    return subprocess.run(args, capture_output=True).stdout.decode('utf-8', 'replace')


def get_live():
    return json.loads(runc(['curl', '-s', URL, '-H', f'X-N8N-API-KEY: {KEY}']))


def put_live(wf):
    payload = {
        'name': wf['name'],
        'nodes': wf['nodes'],
        'connections': wf['connections'],
        'settings': {k: v for k, v in wf.get('settings', {}).items() if k in ALLOWED_SETTINGS}
    }
    tmp = r'C:\CONTENT_PIPELINE\n8n_backups\_batch_put.json'
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


def prep_pipeline(json_path, slot_letter, y_offset, section_title, x_offset=DEFAULT_X_OFFSET):
    """Transform a pipeline JSON into nodes/connections ready to merge."""
    with open(json_path, 'r', encoding='utf-8') as f:
        p = json.load(f)
    src_nodes = p.get('nodes', [])
    src_conns = p.get('connections', {})
    xs = [n['position'][0] for n in src_nodes]
    ys = [n['position'][1] for n in src_nodes]
    min_x, min_y = min(xs), min(ys)

    id_map, name_map = {}, {}
    new_nodes = []

    # Section header sticky
    new_nodes.append({
        'id': str(uuid.uuid4()),
        'name': f"[{slot_letter}] §{slot_letter} HEADER",
        'type': 'n8n-nodes-base.stickyNote',
        'typeVersion': 1,
        'position': [x_offset, y_offset - 100],
        'parameters': {
            'content': f"# §{slot_letter} — {section_title}",
            'height': 80, 'width': 800, 'color': 5
        }
    })

    for n in src_nodes:
        new_id = str(uuid.uuid4())
        id_map[n['id']] = new_id
        new_name = f"[{slot_letter}] {n['name']}"
        base = new_name; suffix = 2
        while new_name in name_map.values():
            new_name = f"{base} #{suffix}"; suffix += 1
        name_map[n['name']] = new_name

        if n['type'] in UNRECOGNIZED_TYPES:
            # Replace with TODO sticky at same position
            new_pos = [n['position'][0] - min_x + x_offset,
                       n['position'][1] - min_y + y_offset]
            new_nodes.append({
                'id': new_id,
                'name': new_name + ' (TODO unrecognized)',
                'type': 'n8n-nodes-base.stickyNote',
                'typeVersion': 1,
                'position': new_pos,
                'parameters': {
                    'content': f"# TODO: {n['type']} not on this n8n\n## Original: {n['name']}\nInstall the langchain pack OR replace with HTTP node to the underlying API.",
                    'height': 220, 'width': 340, 'color': 4
                }
            })
            continue

        new = {k: v for k, v in n.items() if k not in ('credentials', 'webhookId')}
        new['id'] = new_id
        new['name'] = new_name
        new['position'] = [n['position'][0] - min_x + x_offset,
                           n['position'][1] - min_y + y_offset]
        # Apply typeVersion cap
        cap = TYPE_VERSION_CAPS.get(n['type'])
        if cap is not None and new.get('typeVersion', 1) > cap:
            new['typeVersion'] = cap
        new_nodes.append(new)

    # Connections — only keep edges where BOTH endpoints survived (none of the
    # unrecognized nodes appear as src/tgt in connections after replacement,
    # since their new_id is the sticky id; downstream gracefully ends there).
    new_conns = {}
    for src_name, outputs in src_conns.items():
        new_src = name_map.get(src_name, src_name)
        new_conns[new_src] = {}
        for output_type, targets_list in outputs.items():
            new_conns[new_src][output_type] = []
            for target_group in targets_list:
                new_group = [{**t, 'node': name_map.get(t['node'], t['node'])}
                             for t in target_group]
                new_conns[new_src][output_type].append(new_group)

    return new_nodes, new_conns


def merge_many(plan, dry_run=False):
    """plan = list of dicts {path, slot, y_offset, title, [x_offset]}"""
    wf = get_live()
    initial = len(wf['nodes'])
    summaries = []
    existing_ids = {n['id'] for n in wf['nodes']}
    existing_names = {n['name'] for n in wf['nodes']}
    existing_conns_keys = set(wf['connections'].keys())

    for entry in plan:
        nodes, conns = prep_pipeline(
            entry['path'], entry['slot'], entry['y_offset'],
            entry['title'], entry.get('x_offset', DEFAULT_X_OFFSET)
        )
        # Collision checks
        id_coll = [n['id'] for n in nodes if n['id'] in existing_ids]
        name_coll = [n['name'] for n in nodes if n['name'] in existing_names]
        if id_coll or name_coll:
            print(f'!! skipping {entry["slot"]}: collisions ids={id_coll[:3]} names={name_coll[:3]}')
            continue
        wf['nodes'].extend(nodes)
        existing_ids.update(n['id'] for n in nodes)
        existing_names.update(n['name'] for n in nodes)
        for k, v in conns.items():
            if k in existing_conns_keys:
                print(f'!! conn key collision in {entry["slot"]}: {k}')
                continue
            wf['connections'][k] = v
            existing_conns_keys.add(k)
        summaries.append({'slot': entry['slot'], 'title': entry['title'],
                          'nodes_added': len(nodes),
                          'conns_added': len(conns)})

    print(f'Initial nodes: {initial} -> staged total: {len(wf["nodes"])}')
    for s in summaries:
        print(f"  §{s['slot']}: +{s['nodes_added']:3} nodes, +{s['conns_added']:2} conn-groups  -- {s['title']}")

    if dry_run:
        print('(dry run — not PUTting)')
        return summaries, None
    ok, body = put_live(wf)
    print(f'PUT result: {"OK" if ok else "FAIL"}')
    if not ok:
        print('Error body:', body[:400])
    return summaries, body


if __name__ == '__main__':
    # Pipelines to merge in this batch (n31 and R46 already done/present)
    PLAN = [
        {'path': r'C:\CONTENT_PIPELINE\R34_veorobo\R34_airtable.json',
         'slot': 'C', 'y_offset': 2740, 'title': 'R34 — VeoRobo (3-scene Veo3)'},
        {'path': r'C:\CONTENT_PIPELINE\n30_product_videography\n30 _ Product Videography (by RoboNuggets) (1).json',
         'slot': 'I', 'y_offset': 9940, 'title': 'n30 — Product Videography'},
        {'path': r'C:\CONTENT_PIPELINE\R51_creative_cloner\R51_airtable.json',
         'slot': 'B', 'y_offset': 1540, 'title': 'R51 — Creative Cloner'},
        {'path': r'C:\CONTENT_PIPELINE\n3_voice_and_subs\n3 - Monetizable Tiktoks AI Machine with voice and subs.json',
         'slot': 'K', 'y_offset': 12340, 'title': 'n3 — Voice & Subs'},
        {'path': r'C:\CONTENT_PIPELINE\n16_narrative_chaining\🍳 Veo3 - Narrative Chaining (n16).json',
         'slot': 'D', 'y_offset': 3940, 'title': 'n16 — Narrative Chaining'},
        {'path': r'C:\CONTENT_PIPELINE\n16.1_auto_subtitled_videos\ElevenLabs_to_NCA_Toolkit.json',
         'slot': 'E', 'y_offset': 5140, 'title': 'n16.1 — Auto Subtitles'},
        {'path': r'C:\CONTENT_PIPELINE\R39_split_ai_system\(template) 🥚 Split AI System - by RoboNuggets (R39).json',
         'slot': 'F', 'y_offset': 6340, 'title': 'R39 — Split AI Images'},
        {'path': r'C:\CONTENT_PIPELINE\n19_ultimate_video_ads\🍌 Split AI System extended (by RoboNuggets) _ n19.json',
         'slot': 'G', 'y_offset': 7540, 'title': 'n19 — Ultimate Video Ads'},
        {'path': r'C:\CONTENT_PIPELINE\n21_infinite_ugcs\n21 - Ultimate UGC Creator (by RoboNuggets).json',
         'slot': 'H', 'y_offset': 8740, 'title': 'n21 — Ultimate UGC Creator'},
        {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a Tiktok, 🔻get a Sora Vid  _ n29 by RoboNuggets.json',
         'slot': 'L1', 'y_offset': 13540, 'title': 'n29-Sora — TikTok→Sora'},
        {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a YT Long, 🔻get a LI or X post _ n29 by RoboNuggets.json',
         'slot': 'L2', 'y_offset': 14640, 'title': 'n29-Long — YT Long→LI/X'},
        {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a YT Short, 🔻get a Script _ n29 by RoboNuggets.json',
         'slot': 'L3', 'y_offset': 15740, 'title': 'n29-Short — YT Short→Script'},
    ]
    dry = '--dry' in sys.argv
    merge_many(PLAN, dry_run=dry)

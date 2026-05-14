"""
Import remaining 5 pipelines (n16, R39, n19, n21, n30) + n29x3 with rollback.

Compatibility fixes applied:
- @n8n/n8n-nodes-langchain.googleGemini -> TODO sticky (unrecognized)
- @n8n/n8n-nodes-langchain.agent: cap typeVersion at 2
- @n8n/n8n-nodes-langchain.lmChatGoogleGemini -> TODO sticky if present
- telegramTrigger / telegram credentials -> bind to lux_bot (WoB3AsOoB9cIKUrI)
- n8n-nodes-base.executeWorkflow with placeholder sub-workflow ids -> TODO sticky
- All credentials stripped except telegramApi -> lux_bot binding
- webhookId stripped on triggers (n8n regenerates)
- All UUIDs regenerated to avoid collisions

Each pipeline import is atomic: snapshot -> mutate -> PUT -> if fail, restore.
"""
import json, uuid, subprocess, sys, copy, time

sys.stdout.reconfigure(encoding='utf-8')

KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMmIwN2MxNy02MjNlLTQ5ODQtYmMzZi1iNTFjY2E2OWY4ZjciLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzc4NjkzNzU0fQ.D8DtiKkYXy7oiPotzGAwmGu4EiJeu9T5BH3aPGP0oWg'
URL = 'https://ops.getautomata.ai/api/v1/workflows/SmtkmTgfCTLZPlN4'

LUX_BOT_CRED_ID = 'WoB3AsOoB9cIKUrI'
LUX_BOT_NAME = 'lux_bot'

ALLOWED_SETTINGS = {'executionOrder','saveDataErrorExecution','saveDataSuccessExecution',
                    'saveExecutionProgress','saveManualExecutions','executionTimeout','timezone'}

TYPE_VERSION_CAPS = {
    '@n8n/n8n-nodes-langchain.agent': 2,
    'n8n-nodes-base.googleSheets': 4.6,
    'n8n-nodes-base.switch': 3.2,
}

UNRECOGNIZED_TYPES = {
    '@n8n/n8n-nodes-langchain.googleGemini',
    '@n8n/n8n-nodes-langchain.lmChatGoogleGemini',
    '@n8n/n8n-nodes-langchain.embeddingsGoogleGemini',
}

TELEGRAM_TYPES = {
    'n8n-nodes-base.telegram',
}
# telegramTrigger cannot be imported via public PUT — webhook registration
# step is missing. Stub as TODO; operator wires manually in UI to lux_bot.
TELEGRAM_TRIGGER_TYPE = 'n8n-nodes-base.telegramTrigger'

DEFAULT_X_OFFSET = -1200


def runc(args, input_bytes=None):
    return subprocess.run(args, capture_output=True, input=input_bytes).stdout.decode('utf-8', 'replace')


def get_live():
    return json.loads(runc(['curl', '-s', URL, '-H', f'X-N8N-API-KEY: {KEY}']))


def put_live(wf, label='put'):
    payload = {
        'name': wf['name'],
        'nodes': wf['nodes'],
        'connections': wf['connections'],
        'settings': {k: v for k, v in wf.get('settings', {}).items() if k in ALLOWED_SETTINGS}
    }
    tmp = fr'C:\CONTENT_PIPELINE\n8n_backups\_put_{label}.json'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f)
    out = runc(['curl', '-s', '-X', 'PUT', URL,
                '-H', f'X-N8N-API-KEY: {KEY}',
                '-H', 'Content-Type: application/json',
                '--data-binary', f'@{tmp}', '-w', '\n%{http_code}'])
    parts = out.rsplit('\n', 1)
    code = parts[-1].strip()
    body = parts[0] if len(parts) > 1 else ''
    return code == '200', body, code


def restore_snapshot(snapshot, label='rollback'):
    """Force-restore live workflow to snapshot state."""
    ok, body, code = put_live(snapshot, label=label)
    if not ok:
        # Idempotent retry once
        time.sleep(1)
        ok, body, code = put_live(snapshot, label=label + '2')
    return ok


def prep_pipeline(json_path, slot_letter, y_offset, section_title,
                  x_offset=DEFAULT_X_OFFSET, executeworkflow_handling='sticky'):
    """Transform a pipeline JSON into nodes/connections ready to merge."""
    with open(json_path, 'r', encoding='utf-8') as f:
        p = json.load(f)
    src_nodes = p.get('nodes', [])
    src_conns = p.get('connections', {})
    if not src_nodes:
        return [], {}, []
    xs = [n['position'][0] for n in src_nodes]
    ys = [n['position'][1] for n in src_nodes]
    min_x, min_y = min(xs), min(ys)

    id_map, name_map = {}, {}
    new_nodes = []
    notes = []  # For surfacing what got TODO'd

    # Section header sticky
    new_nodes.append({
        'id': str(uuid.uuid4()),
        'name': f"[{slot_letter}] HEADER",
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
        new_pos = [n['position'][0] - min_x + x_offset,
                   n['position'][1] - min_y + y_offset]

        node_type = n.get('type', '')

        # Telegram trigger -> TODO sticky (public PUT can't register webhook)
        if node_type == TELEGRAM_TRIGGER_TYPE:
            params_brief = json.dumps(n.get('parameters', {}), ensure_ascii=False)[:200]
            new_nodes.append({
                'id': new_id,
                'name': new_name + ' (TODO add in UI)',
                'type': 'n8n-nodes-base.stickyNote',
                'typeVersion': 1,
                'position': new_pos,
                'parameters': {
                    'content': (f"# TODO: telegramTrigger\n"
                                f"## Original: {n['name']}\n"
                                f"Add manually in n8n UI, bind to **lux_bot** "
                                f"(cred id `{LUX_BOT_CRED_ID}`).\n"
                                f"params: `{params_brief}`"),
                    'height': 240, 'width': 360, 'color': 4
                }
            })
            notes.append(f"  -> TODO telegramTrigger {n['name']} (manual bind in UI)")
            continue

        # Replace unrecognized types with TODO sticky
        if node_type in UNRECOGNIZED_TYPES:
            new_nodes.append({
                'id': new_id,
                'name': new_name + ' (TODO unrecognized)',
                'type': 'n8n-nodes-base.stickyNote',
                'typeVersion': 1,
                'position': new_pos,
                'parameters': {
                    'content': (f"# TODO: {node_type} not on this n8n\n"
                                f"## Original node: {n['name']}\n"
                                f"Replace with HTTP node calling underlying API "
                                f"or install langchain pack."),
                    'height': 220, 'width': 340, 'color': 4
                }
            })
            notes.append(f"  -> TODO sticky for {n['name']} ({node_type})")
            continue

        # n21 executeWorkflow: stub the call (sub-workflow ids are external)
        if (node_type == 'n8n-nodes-base.executeWorkflow'
                and executeworkflow_handling == 'sticky'):
            sub_ref = n.get('parameters', {}).get('workflowId', {})
            sub_id = sub_ref.get('value') if isinstance(sub_ref, dict) else sub_ref
            new_nodes.append({
                'id': new_id,
                'name': new_name + ' (TODO sub-workflow)',
                'type': 'n8n-nodes-base.stickyNote',
                'typeVersion': 1,
                'position': new_pos,
                'parameters': {
                    'content': (f"# TODO: executeWorkflow sub-id missing\n"
                                f"## Original node: {n['name']}\n"
                                f"## Original sub-workflow id: {sub_id}\n"
                                f"Create the sub-workflow first, then patch this id."),
                    'height': 240, 'width': 340, 'color': 6
                }
            })
            notes.append(f"  -> TODO sub-workflow for {n['name']} (id={sub_id})")
            continue

        # Build the node, stripping creds + webhookId
        new = {k: v for k, v in n.items() if k not in ('credentials', 'webhookId')}
        new['id'] = new_id
        new['name'] = new_name
        new['position'] = new_pos
        # Apply typeVersion cap
        cap = TYPE_VERSION_CAPS.get(node_type)
        if cap is not None and new.get('typeVersion', 1) > cap:
            new['typeVersion'] = cap

        # Bind telegram nodes to lux_bot
        if node_type in TELEGRAM_TYPES:
            new['credentials'] = {
                'telegramApi': {'id': LUX_BOT_CRED_ID, 'name': LUX_BOT_NAME}
            }
            notes.append(f"  -> {n['name']}: bound to lux_bot")

        new_nodes.append(new)

    # Connections — remap source/target names
    new_conns = {}
    for src_name, outputs in src_conns.items():
        new_src = name_map.get(src_name)
        if new_src is None:
            continue
        new_conns[new_src] = {}
        for output_type, targets_list in outputs.items():
            new_conns[new_src][output_type] = []
            for target_group in targets_list:
                new_group = []
                for t in target_group:
                    tgt_name = name_map.get(t['node'])
                    if tgt_name is None:
                        continue
                    new_group.append({**t, 'node': tgt_name})
                new_conns[new_src][output_type].append(new_group)

    return new_nodes, new_conns, notes


def import_one(entry):
    """Import a single pipeline entry with snapshot+rollback."""
    print(f"\n{'='*70}\n=== Importing §{entry['slot']} — {entry['title']}\n{'='*70}")
    snapshot = get_live()
    pre_count = len(snapshot['nodes'])
    print(f"Pre-import: {pre_count} nodes on canvas")

    nodes, conns, notes = prep_pipeline(
        entry['path'], entry['slot'], entry['y_offset'],
        entry['title'], entry.get('x_offset', DEFAULT_X_OFFSET),
        entry.get('executeworkflow_handling', 'sticky')
    )
    if notes:
        print(f"Compatibility patches:")
        for note in notes:
            print(note)

    # Collision checks
    existing_ids = {n['id'] for n in snapshot['nodes']}
    existing_names = {n['name'] for n in snapshot['nodes']}
    id_coll = [n['id'] for n in nodes if n['id'] in existing_ids]
    name_coll = [n['name'] for n in nodes if n['name'] in existing_names]
    if id_coll:
        print(f"!! ID collisions ({len(id_coll)}); regenerating")
        for n in nodes:
            if n['id'] in existing_ids:
                n['id'] = str(uuid.uuid4())
    if name_coll:
        print(f"!! Name collisions ({len(name_coll)}): {name_coll[:3]}; suffixing")
        for n in nodes:
            if n['name'] in existing_names:
                n['name'] = n['name'] + f" #{entry['slot']}"

    new_wf = copy.deepcopy(snapshot)
    new_wf['nodes'].extend(nodes)
    for k, v in conns.items():
        if k in new_wf['connections']:
            print(f"!! conn key collision: {k}; skipping")
            continue
        new_wf['connections'][k] = v

    print(f"Adding {len(nodes)} nodes, {len(conns)} connection groups")
    ok, body, code = put_live(new_wf, label=f'imp_{entry["slot"]}')
    if not ok:
        print(f"FAIL HTTP {code}: {body[:500]}")
        print("Rolling back to snapshot...")
        rok = restore_snapshot(snapshot, label=f'rb_{entry["slot"]}')
        print(f"Rollback: {'OK' if rok else 'FAILED — manual intervention required'}")
        return False

    # Idempotent re-PUT to confirm state stuck
    time.sleep(1)
    confirm = get_live()
    confirm_count = len(confirm['nodes'])
    expected = pre_count + len(nodes)
    print(f"Post-import: {confirm_count} nodes (expected {expected})")
    if confirm_count != expected:
        print(f"!! Node count mismatch — likely partial state")
        restore_snapshot(snapshot, label=f'rb2_{entry["slot"]}')
        return False
    ok2, body2, code2 = put_live(confirm, label=f'idem_{entry["slot"]}')
    if not ok2:
        print(f"!! Idempotent re-PUT failed HTTP {code2}: {body2[:300]}")
        restore_snapshot(snapshot, label=f'rb3_{entry["slot"]}')
        return False

    print(f"OK §{entry['slot']} imported and idempotent.")
    return True


PLAN = [
    {'path': r'C:\CONTENT_PIPELINE\n16_narrative_chaining\🍳 Veo3 - Narrative Chaining (n16).json',
     'slot': 'D', 'y_offset': 3940, 'title': 'n16 — Narrative Chaining'},
    {'path': r'C:\CONTENT_PIPELINE\R39_split_ai_system\(template) 🥚 Split AI System - by RoboNuggets (R39).json',
     'slot': 'F', 'y_offset': 6340, 'title': 'R39 — Split AI Images'},
    {'path': r'C:\CONTENT_PIPELINE\n19_ultimate_video_ads\🍌 Split AI System extended (by RoboNuggets) _ n19.json',
     'slot': 'G', 'y_offset': 7540, 'title': 'n19 — Ultimate Video Ads'},
    {'path': r'C:\CONTENT_PIPELINE\n21_infinite_ugcs\n21 - Ultimate UGC Creator (by RoboNuggets).json',
     'slot': 'H', 'y_offset': 8740, 'title': 'n21 — Ultimate UGC Creator'},
    {'path': r'C:\CONTENT_PIPELINE\n30_product_videography\n30 _ Product Videography (by RoboNuggets) (1).json',
     'slot': 'I', 'y_offset': 9940, 'title': 'n30 — Product Videography'},
]

N29_PLAN = [
    {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a Tiktok, 🔻get a Sora Vid  _ n29 by RoboNuggets.json',
     'slot': 'L1', 'y_offset': 13540, 'title': 'n29-Sora — TikTok→Sora'},
    {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a YT Long, 🔻get a LI or X post _ n29 by RoboNuggets.json',
     'slot': 'L2', 'y_offset': 14640, 'title': 'n29-Long — YT Long→LI/X'},
    {'path': r'C:\CONTENT_PIPELINE\n29_templates\🔺Send a YT Short, 🔻get a Script _ n29 by RoboNuggets.json',
     'slot': 'L3', 'y_offset': 15740, 'title': 'n29-Short — YT Short→Script'},
]


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'phase4'
    if target == 'phase4':
        plan = PLAN
    elif target == 'n29':
        plan = N29_PLAN
    else:
        plan = [e for e in PLAN + N29_PLAN if e['slot'] == target]
    if not plan:
        print(f"No plan for target {target}")
        sys.exit(1)
    results = {}
    for entry in plan:
        results[entry['slot']] = import_one(entry)
    print('\n========== SUMMARY ==========')
    for slot, ok in results.items():
        print(f"  §{slot}: {'OK' if ok else 'FAILED'}")

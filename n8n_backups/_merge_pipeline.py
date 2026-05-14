"""
Pipeline merger for GetAutomata_W01-W05 _Content Pipeline (id: SmtkmTgfCTLZPlN4).

Reads the current workflow state from a working file, imports a pipeline JSON
with normalized positions, fresh UUIDs, stripped credentials, and a section
sticky header. Writes a new payload ready to PUT to /api/v1/workflows/<id>.

Usage from CLI (or imported as a module):
    python _merge_pipeline.py <pipeline_json> <slot_letter> <slot_y_offset> <section_title>

slot_y_offset is the absolute Y where this section's top edge sits on the canvas.
"""
import json, uuid, sys, os, re

ALLOWED_SETTINGS = {
    'executionOrder','saveDataErrorExecution','saveDataSuccessExecution',
    'saveExecutionProgress','saveManualExecutions','executionTimeout','timezone'
}

# Per-pipeline X anchor (keeps each section's left edge aligned consistently).
# Existing R46 occupies X = [-1000, 700]. New sections start at X=-1200 to leave
# margin and keep pipelines from overlapping horizontally.
DEFAULT_X_OFFSET = -1200

WORKING_FILE = r'C:\CONTENT_PIPELINE\n8n_backups\_working_workflow.json'
BACKUP_FILE = r'C:\CONTENT_PIPELINE\n8n_backups\GetAutomata_W01-W05_backup_2026-05-13.json'


def load_working():
    """Load current state of the workflow we're building toward."""
    path = WORKING_FILE if os.path.exists(WORKING_FILE) else BACKUP_FILE
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_working(wf):
    with open(WORKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(wf, f, indent=2)


def normalize_pipeline(pipeline_json_path, slot_letter, y_offset, section_title,
                       x_offset=DEFAULT_X_OFFSET):
    """Read a pipeline JSON, return (nodes, connections) ready to merge.

    - Strips inactive/triggers' webhook IDs (will be regenerated on import).
    - Generates fresh UUIDs for every node and rewires connections.
    - Normalizes positions to (0,0) origin, then shifts to (x_offset, y_offset).
    - Strips `credentials` blocks (operator binds via UI post-import).
    - Prefixes every node name with "[<slot_letter>] " for canvas readability.
    - Adds a section header sticky note at the top-left of the slot.
    """
    with open(pipeline_json_path, 'r', encoding='utf-8') as f:
        p = json.load(f)
    src_nodes = p.get('nodes', [])
    src_conns = p.get('connections', {})

    # Normalize position origin
    xs = [n['position'][0] for n in src_nodes]
    ys = [n['position'][1] for n in src_nodes]
    min_x, min_y = min(xs), min(ys)

    # ID remap: old_id -> new_id, and old_name -> new_name (connections key by name)
    id_map, name_map = {}, {}
    new_nodes = []
    for n in src_nodes:
        new_id = str(uuid.uuid4())
        id_map[n['id']] = new_id
        new_name = f"[{slot_letter}] {n['name']}"
        # Deduplicate names if collision (rare)
        base = new_name
        suffix = 2
        while new_name in name_map.values():
            new_name = f"{base} #{suffix}"
            suffix += 1
        name_map[n['name']] = new_name
        # Build new node
        new = {k: v for k, v in n.items() if k not in ('credentials','webhookId')}
        new['id'] = new_id
        new['name'] = new_name
        new['position'] = [n['position'][0] - min_x + x_offset,
                           n['position'][1] - min_y + y_offset]
        new_nodes.append(new)

    # Rewire connections (n8n keys connections by source NODE NAME, not id)
    new_conns = {}
    for src_name, outputs in src_conns.items():
        new_src = name_map.get(src_name, src_name)  # fallback if missing
        new_conns[new_src] = {}
        for output_type, targets_list in outputs.items():
            new_conns[new_src][output_type] = []
            for target_group in targets_list:
                new_group = []
                for target in target_group:
                    new_target_name = name_map.get(target['node'], target['node'])
                    new_group.append({**target, 'node': new_target_name})
                new_conns[new_src][output_type].append(new_group)

    # Section header sticky
    section_sticky = {
        'id': str(uuid.uuid4()),
        'name': f"[{slot_letter}] SECTION HEADER",
        'type': 'n8n-nodes-base.stickyNote',
        'typeVersion': 1,
        'position': [x_offset, y_offset - 80],
        'parameters': {
            'content': f"# §{slot_letter} — {section_title}",
            'height': 60, 'width': 600, 'color': 5
        }
    }
    new_nodes.insert(0, section_sticky)

    return new_nodes, new_conns


def merge_pipeline_into_workflow(pipeline_json_path, slot_letter, y_offset,
                                  section_title, x_offset=DEFAULT_X_OFFSET):
    """Merge pipeline into current working workflow, write updated working file,
    and return summary stats."""
    wf = load_working()
    p_nodes, p_conns = normalize_pipeline(
        pipeline_json_path, slot_letter, y_offset, section_title, x_offset
    )
    # Check name collisions with existing canvas
    existing_names = {n['name'] for n in wf['nodes']}
    collisions = [n['name'] for n in p_nodes if n['name'] in existing_names]
    if collisions:
        raise RuntimeError(f"Name collisions: {collisions}")
    # Check id collisions
    existing_ids = {n['id'] for n in wf['nodes']}
    id_collisions = [n['id'] for n in p_nodes if n['id'] in existing_ids]
    if id_collisions:
        raise RuntimeError(f"ID collisions: {id_collisions}")
    # Merge
    wf['nodes'].extend(p_nodes)
    for k, v in p_conns.items():
        if k in wf['connections']:
            # Should never happen given name-collision check, but be safe
            raise RuntimeError(f"Connection key collision: {k}")
        wf['connections'][k] = v
    save_working(wf)
    return {
        'pipeline': os.path.basename(pipeline_json_path),
        'slot': slot_letter,
        'y_offset': y_offset,
        'nodes_added': len(p_nodes),
        'connections_added': len(p_conns),
        'total_nodes_now': len(wf['nodes']),
    }


def build_put_payload(out_path):
    """Build the final PUT-ready payload from working file."""
    wf = load_working()
    payload = {
        'name': wf['name'],
        'nodes': wf['nodes'],
        'connections': wf['connections'],
        'settings': {k: v for k, v in wf.get('settings', {}).items() if k in ALLOWED_SETTINGS},
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return out_path, len(payload['nodes'])


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: _merge_pipeline.py <pipeline_json> <slot_letter> <y_offset> <section_title>")
        sys.exit(1)
    result = merge_pipeline_into_workflow(
        sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    )
    print(json.dumps(result, indent=2))

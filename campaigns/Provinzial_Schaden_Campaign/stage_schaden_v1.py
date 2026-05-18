"""Stage Airtable rows for Provinzial Schaden v1.

Dry-run is the default. This helper only prepares Airtable queue rows for
R57 and R61; it never calls generation providers, webhooks, or Blotato.

Usage:
    python campaigns/Provinzial_Schaden_Campaign/stage_schaden_v1.py --dry-run
    python campaigns/Provinzial_Schaden_Campaign/stage_schaden_v1.py --apply
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_DIR = Path(__file__).resolve().parent
CAMPAIGN_ID = "Schaden_2026_05"
MANIFEST_PATH = CAMPAIGN_DIR / f"staged_records_{CAMPAIGN_ID}.json"
R57_AD_PREFIX = "Schaden v1 - R57 -"
R61_AD_PREFIX = "Schaden v1 - R61 -"

sys.path.insert(0, str(ROOT / "R57_content_engine"))
from tools import airtable as r57_airtable  # noqa: E402


def _load_r61_airtable():
    path = ROOT / "R61_video_pipeline" / "tools" / "airtable_video.py"
    spec = importlib.util.spec_from_file_location("r61_airtable_video", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load R61 Airtable helper at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r61_airtable = _load_r61_airtable()


SCENARIOS = [
    (1, "Wohnen / Hausrat", "Wasserrohrbruch um 3 Uhr nachts - wen rufst du an?"),
    (2, "Wohnen / Hausrat", "Nachbar ueberschwemmt - wer zahlt deinen Boden?"),
    (3, "Wohnen / Hausrat", "Einbruch im Urlaub - was zaehlt wirklich versichert?"),
    (4, "Wohnen / Hausrat", "Sturm reisst Dachziegel - ist das Hausrat oder Gebaeude?"),
    (5, "Wohnen / Hausrat", "Glasbruch in der Kueche - kleine Sache, grosse Rechnung"),
    (6, "Wohnen / Hausrat", "Fahrrad geklaut vor dem Bahnhof - Hausrat versichert?"),
    (7, "Wohnen / Hausrat", "Brand am Herd - was bezahlt die Versicherung wirklich?"),
    (8, "Wohnen / Hausrat", "Schimmel im Bad - Versicherung oder Vermieter?"),
    (9, "Wohnen / Hausrat", "Laptop vom Tisch gefallen - gilt das?"),
    (10, "Wohnen / Hausrat", "Handy in die Kloschuessel - wann zahlt die Hausrat?"),
    (11, "Kfz", "Auffahrunfall an der Ampel - wer macht den Schaden?"),
    (12, "Kfz", "Marderbiss am Kabel - was muss ich vor Ort machen?"),
    (13, "Kfz", "Steinschlag in der Frontscheibe - sofort handeln oder warten?"),
    (14, "Kfz", "Parkrempler ohne Notiz - was tun?"),
    (15, "Kfz", "Hagelschaden - wann sollte ich melden?"),
    (16, "Kfz", "Vandalismus ueber Nacht - wer hilft sofort?"),
    (17, "Kfz", "Erste Fahrt mit dem neuen Auto - was muss ich wissen?"),
    (18, "Kfz", "Wildunfall im Dunkeln - Sofort-Checkliste"),
    (19, "Kfz", "Reifen kaputt auf der Autobahn - Pannenhilfe oder selbst?"),
    (20, "Kfz", "Vollkasko vs Teilkasko - der 30-Sekunden-Test"),
    (21, "Haftpflicht", "Kind wirft Ball ins Nachbarauto"),
    (22, "Haftpflicht", "Hund beisst Brieftraeger - was jetzt?"),
    (23, "Haftpflicht", "Glas umgekippt im Restaurant - wer zahlt?"),
    (24, "Haftpflicht", "Beim Umzug Moebel beschaedigt - Mitschuld?"),
    (25, "Haftpflicht", "Schluessel verloren - Schliessanlage neu?"),
    (26, "Haftpflicht", "Beim Sport Mitspieler verletzt"),
    (27, "Haftpflicht", "Fahrrad faellt auf parkendes Auto"),
    (28, "Haftpflicht", "Wer traegt was bei einem Mietschaden?"),
    (29, "Haftpflicht", "Privathaftpflicht fuer die ganze Familie?"),
    (30, "Haftpflicht", "Hund im Wald reisst fremdes Wild"),
    (31, "Sach", "Smartphone-Display kaputt - alle Tarife reichen?"),
    (32, "Sach", "Laptop bei Diebstahl - Hausrat-Sublimit erklaert"),
    (33, "Sach", "Fotoausruestung auf Reise - extra absichern?"),
    (34, "Sach", "Werkzeug im Keller - versichert?"),
    (35, "Sach", "Schmuck-Tresor - pauschal oder einzeln?"),
    (36, "Privatpersonen-Stories", "Mein erster Wasserschaden mit 28 - Erfahrungsbericht"),
    (37, "Privatpersonen-Stories", "So lief mein Schaden in 24h - Kunden-POV"),
    (38, "Privatpersonen-Stories", "Was ich heute anders versichern wuerde - Lehrer Frank, 48"),
    (39, "Privatpersonen-Stories", "Schaden waehrend der Hochzeitsreise - Anna & Tom"),
    (40, "Privatpersonen-Stories", "Mein Sturmschaden im Februar 2026 - echte Geschichte"),
    (41, "Service-Pillar", "Schaden melden in 60 Sekunden - App-Demo"),
    (42, "Service-Pillar", "WhatsApp-Schadenmeldung - wer kann das?"),
    (43, "Service-Pillar", "Was passiert, nachdem ich den Schaden melde?"),
    (44, "Service-Pillar", "Persoenlicher Schadenbearbeiter vs Hotline - Unterschied?"),
    (45, "Service-Pillar", "Provinzial-App: Foto rein, Antrag raus"),
    (46, "Service-Pillar", "Wenn ich nicht zu Hause bin - wer geht hin?"),
    (47, "Service-Pillar", "Welche Unterlagen brauche ich beim Schaden?"),
    (48, "Service-Pillar", "Warum Regional-Versicherer schneller reagieren"),
    (49, "Service-Pillar", "24/7 Schaden-Hotline - wirklich erreichbar?"),
    (50, "Service-Pillar", "Die Sorglos-Garantie erklaert in 30 Sekunden"),
]


R57_FIELDS = [
    "Index", "Ad Name", "Product", "Image Prompt", "Image Status",
    "Caption", "Scheduled Date", "Campaign ID",
]
R61_FIELDS = [
    "Index", "Ad Name", "Pillar", "Content Pillar", "Video Status",
    "Caption", "Voiceover Script", "Voice Tone", "Campaign ID",
]
R57_CORE_FIELDS = ["Index", "Ad Name", "Product", "Image Prompt", "Image Status", "Caption"]
R61_CORE_FIELDS = ["Index", "Ad Name", "Video Status"]


def _headers(api_key):
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def get_field_names(api_key, base_id, table_name):
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    resp = requests.get(url, headers=_headers(api_key), timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Airtable schema query failed ({resp.status_code}): {resp.text}")
    for table in resp.json().get("tables", []):
        if table.get("name") == table_name or table.get("id") == table_name:
            return {field["name"] for field in table.get("fields", [])}
    raise RuntimeError(f"Airtable table not found in schema: {table_name}")


def max_index(records):
    highest = 0
    for record in records:
        value = record.get("fields", {}).get("Index")
        if value is None:
            continue
        try:
            highest = max(highest, int(value))
        except (TypeError, ValueError):
            continue
    return highest


def count_ad_prefix(records, prefix):
    count = 0
    for record in records:
        ad_name = record.get("fields", {}).get("Ad Name") or ""
        if ad_name.startswith(prefix):
            count += 1
    return count


def slug(text, max_words=7):
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-zA-Z0-9]+", normalized.lower())
    return "-".join(words[:max_words]) or "schaden"


def caption_for(scenario):
    return (
        f"{scenario}\n"
        "Wenn etwas passiert, zaehlt ein ruhiger naechster Schritt.\n"
        "Provinzial ist da, wenn es darauf ankommt.\n"
        "#Provinzial #Schaden"
    )


def prompt_for(category, scenario):
    return (
        "9:16. Realistische deutsche Alltagsszene nach einem Schadenmoment: "
        f"{scenario}. Kategorie: {category}. Zeige nicht die Katastrophe, "
        "sondern den ruhigen Moment danach: eine Person sortiert Unterlagen, "
        "macht ein Foto fuer die Schadenmeldung oder telefoniert entspannt mit "
        "einem regionalen Ansprechpartner. Warme natuerliche Beleuchtung, echte "
        "Wohnung, Strasse oder Kueche in NRW, authentische Menschen 25-55, "
        "Provinzial-Gruen #005940 subtil im Umfeld, gelber Fluegel-Watermark "
        "unten rechts, keine Angstbilder, kein Text im Bild."
    )


def voice_seed(scenario):
    return (
        f"Heute geht es um: {scenario}. Im Schadenfall hilft zuerst Klarheit: "
        "kurz dokumentieren, Schaden melden und persoenlich klaeren lassen, "
        "welcher Schutz greift. Ruhig bleiben, Provinzial ansprechen."
    )


def voice_tone(category):
    return "familie" if category in {"Wohnen / Hausrat", "Haftpflicht"} else "ernst"


def filter_existing(fields, field_names):
    return {key: value for key, value in fields.items() if key in field_names}


def build_r57_rows(start_index, field_names):
    planned = []
    for offset, (num, category, scenario) in enumerate(SCENARIOS[:40]):
        fields = {
            "Index": start_index + offset,
            "Ad Name": f"Schaden v1 - R57 - {num:02d} - {slug(scenario)}",
            "Product": "Provinzial Schaden",
            "Image Prompt": prompt_for(category, scenario),
            "Image Status": "Pending",
            "Caption": caption_for(scenario),
            "Scheduled Date": "",
            "Campaign ID": CAMPAIGN_ID,
        }
        planned.append({
            "scenario_number": num,
            "scenario": scenario,
            "fields": filter_existing(fields, field_names),
        })
    return planned


def build_r61_rows(start_index, field_names):
    planned = []
    pillar_field = "Pillar" if "Pillar" in field_names else "Content Pillar"
    for offset, (num, category, scenario) in enumerate(SCENARIOS[:25]):
        seed = voice_seed(scenario)
        fields = {
            "Index": start_index + offset,
            "Ad Name": f"Schaden v1 - R61 - {num:02d} - {slug(scenario)} [Schaden & Service]",
            pillar_field: "Schaden & Service",
            "Video Status": "Pending",
            "Caption": seed,
            "Voiceover Script": seed,
            "Voice Tone": voice_tone(category),
            "Campaign ID": CAMPAIGN_ID,
        }
        planned.append({
            "scenario_number": num,
            "scenario": scenario,
            "fields": filter_existing(fields, field_names),
        })
    return planned


def print_sample(label, rows):
    print(f"\nFirst 3 planned {label} rows:")
    for row in rows[:3]:
        print(json.dumps(row["fields"], ensure_ascii=False, indent=2))


def missing_fields(desired, field_names):
    return [field for field in desired if field not in field_names]


def ensure_core_fields(label, core, field_names):
    missing = missing_fields(core, field_names)
    if missing:
        raise RuntimeError(f"{label} missing required fields: {', '.join(missing)}")


def write_manifest(created_r57, planned_r57, created_r61, planned_r61):
    manifest = {
        "campaign_id": CAMPAIGN_ID,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "r57": [
            {
                "record_id": record["id"],
                "index": plan["fields"].get("Index"),
                "scenario": plan["scenario"],
            }
            for record, plan in zip(created_r57, planned_r57)
        ],
        "r61": [
            {
                "record_id": record["id"],
                "index": plan["fields"].get("Index"),
                "scenario": plan["scenario"],
            }
            for record, plan in zip(created_r61, planned_r61)
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage Schaden v1 Airtable rows.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print plan only; no writes.")
    mode.add_argument("--apply", action="store_true", help="Create Airtable rows and manifest.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass duplicate apply protection. Use only after manual review.",
    )
    args = parser.parse_args(argv)
    apply = bool(args.apply)

    if r57_airtable.config.check_credentials():
        raise SystemExit(1)
    missing_r61 = r61_airtable.check_credentials()
    if missing_r61:
        print(f"Missing R61 env vars: {', '.join(missing_r61)}", file=sys.stderr)
        raise SystemExit(1)

    r57_fields = get_field_names(
        r57_airtable.config.AIRTABLE_API_KEY,
        r57_airtable.config.AIRTABLE_BASE_ID,
        r57_airtable.config.AIRTABLE_TABLE_NAME,
    )
    r61_fields = get_field_names(
        r61_airtable.AIRTABLE_API_KEY,
        r61_airtable.AIRTABLE_BASE_ID,
        r61_airtable.TABLE_NAME,
    )

    ensure_core_fields("R57", R57_CORE_FIELDS, r57_fields)
    ensure_core_fields("R61", R61_CORE_FIELDS, r61_fields)

    r57_records = r57_airtable.get_records()
    r61_records = r61_airtable.get_records()
    r57_max = max_index(r57_records)
    r61_max = max_index(r61_records)
    duplicate_check = {
        "existing_r57_rows": count_ad_prefix(r57_records, R57_AD_PREFIX),
        "existing_r61_rows": count_ad_prefix(r61_records, R61_AD_PREFIX),
        "manifest_exists": MANIFEST_PATH.exists(),
    }

    planned_r57 = build_r57_rows(r57_max + 1, r57_fields)
    planned_r61 = build_r61_rows(r61_max + 1, r61_fields)

    r57_missing = missing_fields(R57_FIELDS, r57_fields)
    r61_missing = missing_fields(R61_FIELDS, r61_fields)
    campaign_field_exists = {
        "r57": "Campaign ID" in r57_fields,
        "r61": "Campaign ID" in r61_fields,
    }

    print(f"Mode: {'APPLY' if apply else 'DRY-RUN'}")
    print(f"Campaign ID: {CAMPAIGN_ID}")
    print(f"R57 current max Index: {r57_max}")
    print(f"R61 current max Index: {r61_max}")
    print(f"Planned R57 rows: {len(planned_r57)}")
    print(f"Planned R61 rows: {len(planned_r61)}")
    print("Duplicate check:")
    print(f"  existing staged R57 rows: {duplicate_check['existing_r57_rows']}")
    print(f"  existing staged R61 rows: {duplicate_check['existing_r61_rows']}")
    print(f"  manifest exists: {duplicate_check['manifest_exists']}")
    print(f"R57 optional/desired fields missing: {r57_missing or 'none'}")
    print(f"R61 optional/desired fields missing: {r61_missing or 'none'}")
    print(f"Campaign ID field exists: R57={campaign_field_exists['r57']} R61={campaign_field_exists['r61']}")
    if not campaign_field_exists["r57"] or not campaign_field_exists["r61"]:
        print("WARNING: Campaign ID field missing; generation must use record_ids from staging output.")

    print_sample("R57", planned_r57)
    print_sample("R61", planned_r61)

    if not apply:
        print("\nDry run only - no Airtable records created.")
        return 0

    duplicates_found = (
        duplicate_check["existing_r57_rows"] > 0
        or duplicate_check["existing_r61_rows"] > 0
        or duplicate_check["manifest_exists"]
    )
    if duplicates_found and not args.force:
        print("\nABORT: existing Schaden v1 staging artifacts found.")
        print(f"  existing staged R57 rows: {duplicate_check['existing_r57_rows']}")
        print(f"  existing staged R61 rows: {duplicate_check['existing_r61_rows']}")
        print(f"  manifest exists: {duplicate_check['manifest_exists']}")
        print("No Airtable records were created. Re-run with --force only after manual review.")
        return 2
    if duplicates_found and args.force:
        print("\nWARNING: --force set; duplicate protection is bypassed.")

    created_r57 = r57_airtable.create_records_batch([row["fields"] for row in planned_r57])
    created_r61 = r61_airtable.create_records_batch([row["fields"] for row in planned_r61])
    manifest = write_manifest(created_r57, planned_r57, created_r61, planned_r61)

    print("\nCreated R57 record IDs:")
    print(json.dumps([item["record_id"] for item in manifest["r57"]], indent=2))
    print("Created R61 record IDs:")
    print(json.dumps([item["record_id"] for item in manifest["r61"]], indent=2))
    print(f"Manifest written: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

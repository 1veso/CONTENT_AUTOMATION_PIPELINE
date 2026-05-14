# R2 filename cleanup — v3 generation

**Date:** 2026-05-14
**Pipeline:** R61
**Context:** The `slugify()` function in `R61_video_pipeline/tools/stitch.py` was tightened to strip brackets `[]`, ampersands `&`, and Windows-illegal characters before they hit the filesystem or the R2 key. Existing R2 objects under `r61/final/v3/` still carry the old, unclean filenames.

## Why we're not re-uploading

Per [[SOUL.md]] rule 2 — never delete generated content. The 22 existing v3 finals in R2 are referenced from Airtable's `Final Video` field and from Blotato's scheduled posts; rewriting their keys would either:

- (a) Force a re-upload and a parallel set of objects (wasting bandwidth + R2 storage), or
- (b) Break every Airtable + Blotato pointer.

Neither is acceptable. The clean-slug rule applies from this cut-forward — new v4 generations (or any future render where the operator bumps `R61_VERSION_TAG`) will land in R2 with clean keys.

## Mapping (old key → clean key under future tag)

These mappings are advisory. If a re-render is ever triggered for the same record under a new `R61_VERSION_TAG`, the clean key shown below is what the pipeline will produce.

| idx | Existing v3 key | Future clean key (under e.g. v4) |
|----:|-----------------|----------------------------------|
| 1  | `r61/final/v3/1_Provinzial_-_Day_1_-_Family_at_New_Home_[Sicherheit_im_Allta.mp4` | `r61/final/<tag>/1_Provinzial_-_Day_1_-_Family_at_New_Home_Sicherheit_im_Allta.mp4` |
| 2  | `r61/final/v3/2_Provinzial_-_Day_2_-_Hausrat_vs_Wohngebäude_Explainer_[Produ.mp4` | `r61/final/<tag>/2_Provinzial_-_Day_2_-_Hausrat_vs_Wohngebäude_Explainer_Produ.mp4` |
| 4  | `r61/final/v3/4_Provinzial_-_Day_4_-_Daughter_Moving_Out_[Vorsorge_&_Zukunft.mp4` | `r61/final/<tag>/4_Provinzial_-_Day_4_-_Daughter_Moving_Out_Vorsorge_Zukunft.mp4` |
| 5  | `r61/final/v3/5_Provinzial_-_Day_5_-_Calm_Phone_Call_[Schaden_&_Service].mp4` | `r61/final/<tag>/5_Provinzial_-_Day_5_-_Calm_Phone_Call_Schaden_Service.mp4` |
| 6  | `r61/final/v3/6_Provinzial_-_Day_6_-_Kreisliga_Saturday_[Regional_&_Gemeinsc.mp4` | `r61/final/<tag>/6_Provinzial_-_Day_6_-_Kreisliga_Saturday_Regional_Gemeinsc.mp4` |
| 7  | `r61/final/v3/7_Provinzial_-_Day_7_-_Sunday_Still_Life_[Sicherheit_im_Alltag.mp4` | `r61/final/<tag>/7_Provinzial_-_Day_7_-_Sunday_Still_Life_Sicherheit_im_Alltag.mp4` |
| 8  | `r61/final/v3/8_Provinzial_-_Day_8_-_Child_Seat_in_Wagon_[Sicherheit_im_Allt.mp4` | `r61/final/<tag>/8_Provinzial_-_Day_8_-_Child_Seat_in_Wagon_Sicherheit_im_Allt.mp4` |
| 9  | `r61/final/v3/9_Provinzial_-_Day_9_-_Selbstbehalt_Explainer_[Produktaufkläru.mp4` | `r61/final/<tag>/9_Provinzial_-_Day_9_-_Selbstbehalt_Explainer_Produktaufkläru.mp4` |
| 10 | `r61/final/v3/10_Provinzial_-_Day_10_-_Bäcker_um_die_Ecke_[Regional_&_Gemeins.mp4` | `r61/final/<tag>/10_Provinzial_-_Day_10_-_Bäcker_um_die_Ecke_Regional_Gemeins.mp4` |
| 11 | `r61/final/v3/11_Provinzial_-_Day_11_-_Renovating_Couple_[Vorsorge_&_Zukunft].mp4` | `r61/final/<tag>/11_Provinzial_-_Day_11_-_Renovating_Couple_Vorsorge_Zukunft.mp4` |
| 12 | `r61/final/v3/12_Provinzial_-_Day_12_-_Adjuster_Handshake_[Schaden_&_Service].mp4` | `r61/final/<tag>/12_Provinzial_-_Day_12_-_Adjuster_Handshake_Schaden_Service.mp4` |
| 16 | `r61/final/v3/16_Provinzial_-_Day_16_-_Haftpflicht_Explainer_[Produktaufkläru.mp4` | `r61/final/<tag>/16_Provinzial_-_Day_16_-_Haftpflicht_Explainer_Produktaufkläru.mp4` |
| 19 | `r61/final/v3/19_Provinzial_-_Day_19_-_Schaden_in_2_Minuten_[Schaden_&_Servic.mp4` | `r61/final/<tag>/19_Provinzial_-_Day_19_-_Schaden_in_2_Minuten_Schaden_Servic.mp4` |
| 20 | `r61/final/v3/20_Provinzial_-_Day_20_-_Sunrise_Landstraße_[Regional_&_Gemeins.mp4` | `r61/final/<tag>/20_Provinzial_-_Day_20_-_Sunrise_Landstraße_Regional_Gemeins.mp4` |
| 22 | `r61/final/v3/22_Provinzial_-_Day_22_-_Road_Trip_Packing_[Sicherheit_im_Allta.mp4` | `r61/final/<tag>/22_Provinzial_-_Day_22_-_Road_Trip_Packing_Sicherheit_im_Allta.mp4` |
| 23 | `r61/final/v3/23_Provinzial_-_Day_23_-_BU_Explainer_[Produktaufklärung].mp4` | `r61/final/<tag>/23_Provinzial_-_Day_23_-_BU_Explainer_Produktaufklärung.mp4` |
| 24 | `r61/final/v3/24_Provinzial_-_Day_24_-_Wochenmarkt_Tomaten_[Regional_&_Gemein.mp4` | `r61/final/<tag>/24_Provinzial_-_Day_24_-_Wochenmarkt_Tomaten_Regional_Gemein.mp4` |
| 25 | `r61/final/v3/25_Provinzial_-_Day_25_-_Couple_Walking_Meadow_[Vorsorge_&_Zuku.mp4` | `r61/final/<tag>/25_Provinzial_-_Day_25_-_Couple_Walking_Meadow_Vorsorge_Zuku.mp4` |
| 26 | `r61/final/v3/26_Provinzial_-_Day_26_-_Service_Agent_Portrait_[Schaden_&_Serv.mp4` | `r61/final/<tag>/26_Provinzial_-_Day_26_-_Service_Agent_Portrait_Schaden_Serv.mp4` |
| 27 | `r61/final/v3/27_Provinzial_-_Day_27_-_Stadtpark_Konzert_[Regional_&_Gemeinsc.mp4` | `r61/final/<tag>/27_Provinzial_-_Day_27_-_Stadtpark_Konzert_Regional_Gemeinsc.mp4` |
| 28 | `r61/final/v3/28_Provinzial_-_Day_28_-_Vater_und_Sohn_Werkstatt_[Sicherheit_i.mp4` | `r61/final/<tag>/28_Provinzial_-_Day_28_-_Vater_und_Sohn_Werkstatt_Sicherheit_i.mp4` |
| 30 | `r61/final/v3/30_Provinzial_-_Day_30_-_Welche_Versicherung_[Produktaufklärung.mp4` | `r61/final/<tag>/30_Provinzial_-_Day_30_-_Welche_Versicherung_Produktaufklärung.mp4` |

## How the new keys are produced

`hf_stitch.publish_to_r2_and_airtable()` constructs the R2 key as:

```
r2_key = f"r61/final/{VERSION_TAG}/{key_name}"
```

where `VERSION_TAG = os.environ.get("R61_VERSION_TAG", "v3")` and `key_name` is `f"{index}_{clean_slug(ad_name)}.mp4"`.

`clean_slug` (canonical impl in `R61_video_pipeline/tools/path_utils.py`):
- strips `[]()`, `{}` brackets
- drops `&`
- strips `\\ / : * ? " < > |` (Windows-illegal)
- collapses whitespace to `_`
- preserves German umlauts

To cut a new generation, set `R61_VERSION_TAG=v4` in `R61_video_pipeline/.env` and re-run `hf_stitch`. Local outputs land in `references/outputs/final/v4/`, R2 keys under `r61/final/v4/`. The v3 shelf is untouched per the never-delete rule.

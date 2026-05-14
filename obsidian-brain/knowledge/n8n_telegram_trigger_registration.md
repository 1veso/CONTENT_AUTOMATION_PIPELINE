# n8n telegramTrigger Registration — Manual UI Steps

The n8n public API **cannot** create `n8n-nodes-base.telegramTrigger` nodes. PUTs are rejected by the server (verified during the W01–W05 merge, 2026-05-13). The five trigger placeholders that live as sticky-note TODOs in workflow `SmtkmTgfCTLZPlN4` therefore have to be registered in the UI.

This page documents that exact UI flow so it takes <5 minutes. Once registration is done, ping the primary agent and the downstream wiring (set lux_bot credential, enable callback_query updates, connect to first body node) can be auto-bound via partial diff.

---

## Where to register

5 triggers across 5 pipeline sections. Coordinates are the location of the existing TODO sticky in the canvas — drop the new `telegramTrigger` next to it, slightly to its left (X = sticky.X − 100).

| # | Section | Pipeline | TODO sticky id | Sticky coords (X, Y) | Connect output to (node name) |
|---|---------|----------|----------------|---------------------|-------------------------------|
| 1 | §F | R39 (Split AI Images) | `ff44290c-664c-4d15-aed0-d4e2fb0df631` | `(-848, 6484)` | `[F] Set Bot ID` |
| 2 | §G | n19 (Ultimate Video Ads) | `1907490b-f26b-4317-ba0b-8c812693dc09` | `(-864, 7716)` | `[G] Set Bot ID` |
| 3 | §L1 | n29 (TikTok→Sora) | `f9347a7c-baa1-430c-b84f-f751a5efbcf4` | `(-304, 13796)` | `[L1] Analyze video1` (sticky-note placeholder — see note A) |
| 4 | §L2 §L2a | n29 (YT-long → LinkedIn) | `e3dc9965-f7ed-497e-98e8-85b2f4b39299` | `(-320, 14912)` | `[L2] Analyze video3` (sticky-note placeholder — see note A) |
| 5 | §L2b | n29 (YT-long → Twitter) | `56f6a773-842c-400f-accf-fbb0256c868d` | `(-320, 15104)` | `[L2] Analyze video4` (sticky-note placeholder — see note A) |
| 6 | §L3 | n29 (YT-short → Script) | `63ebf30f-26b4-46ae-8139-8225e7cbc934` | `(-528, 15900)` | `[L3] Analyze video` (sticky-note placeholder — see note A) |

> Note A: §L1/§L2/§L3 also have "Analyze video" sticky-note placeholders. Those need to become real nodes too (a langchain agent or HTTP request — depends on the pipeline). For trigger registration just connect the new trigger to wherever the first real downstream node lives — the trigger's purpose is to receive Telegram messages and pass them into the pipeline, so the chain only needs to be valid from the trigger forward.

Six trigger nodes total (§L2 has two — for LinkedIn and Twitter sub-flows).

---

## Per-trigger UI flow (~30 seconds each)

1. Open the workflow in the n8n UI: <https://ops.getautomata.ai/workflow/SmtkmTgfCTLZPlN4>.
2. Click **+ Add node** (or hit `Tab` while a node is selected).
3. Search: `Telegram Trigger`. Pick the one with the n8n icon (NOT a community node).
4. **Trigger node name:** rename the new node to match the convention. E.g. for §F: `[F] Telegram Trigger`. (Replace the prefix per the table above.)
5. **Credential:** click the credential dropdown → select **`lux_bot`** (id `WoB3AsOoB9cIKUrI`). If `lux_bot` doesn't appear in the dropdown, the credential has been renamed or deleted — re-check `Settings → Credentials`.
6. **Updates:** in the "Updates" multi-select, enable BOTH:
   - `message` (so user-sent text/photos trigger the chain)
   - `callback_query` (so inline-keyboard button taps trigger the chain — required for the R61 gate approval flow)
   Leave the other update types (channel_post, edited_message, etc.) off unless you have a specific need.
7. **Additional fields:** leave at defaults. Specifically, don't set a `chatIds` filter — the bot is already access-gated via `.claude/telegram/access.json`.
8. **Position:** drag the new node to roughly `(sticky.X − 100, sticky.Y)` so it sits left of the TODO sticky. (See coords column above.)
9. **Save the workflow** (Cmd/Ctrl + S).
10. Delete the TODO sticky — it has served its purpose.

Repeat for all 6 triggers.

---

## After registration — ping the primary agent

Reply on Telegram: **"telegram triggers registered"** and list the six node names you created (e.g. `[F] Telegram Trigger`, `[G] Telegram Trigger`, `[L1] Telegram Trigger1`, `[L2] Telegram Trigger2`, `[L2] Telegram Trigger3`, `[L3] Telegram Trigger`).

The agent will then:

1. Fetch the workflow.
2. Confirm each new trigger has the `lux_bot` credential bound (id `WoB3AsOoB9cIKUrI`) and both `message` + `callback_query` updates enabled.
3. Add a `main` connection from each new trigger to the downstream "Set Bot ID" / "Analyze video" node (as listed above) via partial diff. This part IS supported by the API — only the trigger node *creation* is rejected.
4. Optionally re-bind any other Telegram nodes in the workflow to the same `lux_bot` credential id.
5. Export the updated workflow.

---

## Why the public API rejects telegramTrigger PUTs

n8n classifies trigger nodes (especially webhook-style triggers) as needing server-side registration to allocate a webhook path. The public API surface only registers webhooks for `n8n-nodes-base.webhook`; for `telegramTrigger` it expects the UI flow to wire up the `setWebhook` call on the Telegram side. Bypassing via PUT leaves the n8n internal state inconsistent (no path allocated, no Telegram webhook subscribed), and the server rejects rather than persist a half-registered trigger.

This is also why `n8n-nodes-base.webhook` nodes (used in every R57/R61 pipeline webhook chain) work fine via API — they ARE supported. Only `telegramTrigger` is special.

---

## Reference

- Workflow id: `SmtkmTgfCTLZPlN4`
- lux_bot credential id: `WoB3AsOoB9cIKUrI` (Telegram chat 1077552316)
- Webhook merge log: `obsidian-brain/knowledge/webhook_registry.md`
- CLAUDE.md compatibility caps section (where this constraint was first documented)

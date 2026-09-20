---
name: minecraft-keybindings
description: Diagnose and repair conflicting physical controls when the connected client advertises a tested settings capability.
---

Use this skill when a physical key triggers the wrong function, a required binding
is unavailable, or two controls interfere in the same context.

1. Read `mcgame controls-capabilities --json`. If settings are unsupported, report
   that limitation and stop this workflow. Structured actions do not provide a
   physical keyboard namespace. Use only the settings operations and command
   grammar advertised by a capable client; the following names describe those
   operations, not permission to invent unavailable commands.
2. Discover bindings through `mcgame controls list`. Identify each binding's stable
   ID, owning mod, contexts, current physical key, modifiers and protected status.
   Diagnose intended and competing effects with the permitted client feedback.
3. Ask `mcgame controls plan` for a minimal repair using only the backend's tested
   pool. Disjoint known contexts may share a key. Unknown contexts may overlap.
   Never invent a key from a Unicode character or copy numeric codes between
   GLFW, legacy LWJGL and operating-system backends. Preserve essential controls.
4. Apply the planned transaction with its expected revision and keymap digest.
   A revision conflict requires a fresh read and plan. Do not force an old patch.
5. Poll transaction status. Acceptance is not completion. Verify the intended
   effect, competing effects, modifiers and relevant GUI/game/chat contexts,
   release of held keys, essential controls, and persistence through a client
   restart. Keep world continuity through the normal settings transaction.
6. If a check fails, request rollback and confirm the receipt. If the result is
   uncertain or rollback conflicts, stop input and request recovery. Do not blindly
   replay the mutation or overwrite unrelated settings changes.

Keep a short note of a successful repair with the binding IDs and confirmed
physical representation. A later backend or layout change requires rediscovery.

# Quest menu integration audit — September 19, 2026

Status: **source inspection only**. M0.3b.3.2.3c.2.2b is in progress;
ordinary interactions (.c.3) and authentic qualification (.4) remain unimplemented
or unrun. No capability, acceptance result or specification scope changes.

The exact installed FTB artifacts from the [catalog report](2026-09-19-quest-catalog.md)
were inspected with the pinned JDK's `javap -c -p`. Public signatures and bytecode
are retained outside the repository in
`.strata/evidence/2026-09-19-quest-menu-audit-01/`. This did not invoke game code.

## Findings that constrain the adapter

- `TaskButton` passes permission to act separately from its display callback:
  the task must be valid, startable for the current team and incomplete.
  `ItemTask.onButtonClicked` may still open a display when permission is false.
  A non-consuming task with one display item routes to the recipe integration;
  other nonempty item lists open `ValidItemsScreen`. Empty lists show a toast.
- `ValidItemsScreen` exposes public task, item list and control references.
  Its item panel creates `ValidItemButton` widgets and caps its visible height
  at 160 pixels. The public item list includes entries beyond the currently
  visible viewport; membership alone cannot authorize an on-screen click.
  Clicking an item opens its recipe display, rather than selecting it for
  submission.
- Submit's `getWidgetType()` returns disabled unless the captured `canClick`
  flag is true, the task consumes resources, and it is not task-screen-only.
  Its `onClicked` sends `SubmitTaskMessage` and navigates back without repeating
  those checks. Calling that callback directly could therefore bypass the
  disabled control. A future adapter must preserve ordinary enabled/hit/menu
  checks and revalidate the live team/task state before dispatch.
- `RewardButton` obtains permission from current-player `getClaimType().canClaim()`.
  `ChoiceReward.onButtonClicked` opens its selection screen only when permitted.
  That screen creates buttons from the table in list order. A selection closes
  the screen and sends the choice index with the parent reward ID. Table order,
  active screen, parent identity and own-player eligibility must remain bound
  across observation and dispatch; an index alone is insufficient authority.
- The choice screen and choice button keep their parent reward/weighted entry
  private. Their visible widget titles/tooltips are accessible through public
  UI APIs. Do not add private-field reflection or dump the raw reward table to
  manufacture parent binding. A qualified opening action can retain its own
  private context and invalidate it on screen/source changes.
- FTB Library provides `ScreenWrapper.getGui()`, public `Panel.widgets`,
  widget bounds, `shouldDraw`, `isEnabled`, `getWidgetType`, and panel clipping
  accessors. These establish APIs to investigate; they do not prove clipping,
  hover, scroll, modifier or ordinary input parity in the loaded client.

The next implementation should first project a bounded, active supported menu
with explicit unsupported states and private screen identity. Opening,
submission, selection and dismissal then need separate bounded, charged actions
through the existing mutation lane, source/body/menu checks, cancellation and
ambiguous-result handling. No direct server packets, progress writes or automatic
reward selection are authorized by a read operation. Resource/server feedback
and independent UI parity remain required.

## Audit outcome and limitations

The first inspection guessed a nested class name `ValidItemsScreen$ItemButton`
and exited nonzero for that name. The artifact inventory identifies
`ValidItemsScreen$ValidItemButton`; the corrected full inspection succeeded.
Both the attempt and final output are retained. No guessed API was implemented.

This audit changes no code and runs no Minecraft interaction, model call, test
suite, capacity test or study. The [normal tooltip/status candidate](2026-09-19-quest-components.md)
remains built but uninstalled. Windows Security still awaits the existing
operator handoff; broad desktop authorization remains active.

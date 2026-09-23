# Native public game-contract conformance

Operator-only. September 23, 2026. M0.1d.9; F03/F06/F09/F11/F16,
N01/N02/N04/N06; partial T01/T03/T04/T07/T12/T13; G0 1/4/6.
M0/G0 remain incomplete/fail. D14 isolation deferral is unchanged.

The failed D15 pilot guessed game argument shapes because its initial context
lacked public request documentation. The correction from `1e2ec66` now has
actual pinned-native consumer evidence, using synthetic model replies and a
synthetic worker. No Minecraft process, account credential or paid model call
was used. This verifies the public API path, not model reasoning or movement.

The existing native fixture has a `piloting_contract` mode with the actual
`development_piloting` purpose and zero helpers. It uses the same gateway
enrollment and immutable projection that the live pilot uses. Scripted native
code reads `initial/game/contract.json`, retains that document in native code
mode, checks the returned schema for a malformed request without echoing
rejected input, derives the RPC selector/schema from the document, and sends
one valid observation request. Exact broker events and the worker journal
corroborate the read-before-forwarding order. Three fixture requests settle;
the native process exits normally and its budget closes.

Pilot preflight now requires these relevant public-contract checks and the
zero-helper development purpose. It refuses the older helper/canary fixture
as a substitute for this failed interface. The receipt-only conformance route
keeps its existing requirements. Full isolation qualification remains deferred;
no canary failure has been relabeled as a pass.

Executed verification:

- Skills/broker/piloting source selection: 102 pass; the final piloting file
  passes 44 cases after two admission/profile regressions were added. These
  overlap: **104 distinct cases**, not 146.
- Full Ruff and `git diff --check`: pass.
- Native case01: **14/15**, retained. The report read the pre-budget-closure
  runtime snapshot (`UNSETTLED`), although native exit was zero and the final
  closure was `FINALIZED`. The check was corrected to use final closure.
- Changed native case02: **15/15**, three settled scripted requests,
  one valid synthetic worker observation, zero helpers, native exit zero and
  final closure. The real `inspect_preflight(..., piloting=True)` consumer
  accepts its exact source/profile/tool pins through a read-only audit.
- All **38** current original-authority tables are identical before and after
  each case. D12/D15 remain consumed, total exposure remains $0.763280 and the
  original unknown hold remains unchanged.

Both complete long-path inventories pass independent `EvidenceBundle` checks:

| Private bundle under `C:/Users/Darian/.strata/evidence` | Files / bytes | Seal SHA-256 |
|---|---|---|
| `2026-09-23-pilot-contract-native-01` | 3,726 / 73,682,798 | `b782b137423461f4460f7b30ec60351b9e6f8bb4f0a88e129d350d6e56f536b2` |
| `2026-09-23-pilot-contract-native-02` | 3,724 / 73,480,634 | `d50b76e1a696cc13375d0b363ab29ce7ff1c628b0ea74b7c6bcf633eab09eaf8` |

The first case's exact pre-correction report source is preserved against its
original source hash. Neither its failed check nor D15's actual piloting
failure is overwritten by case02. A new live pilot needs a fresh unused
baseline and a distinct authorization; this work grants neither another model
request nor a full G0 pass.

A reviewable second pilot is prepared in private
`2026-09-23-m0-pilot-next-preparation-01`, using a new unused
`C:/Users/Darian/.strata/runtime/m0-pilot-02/instance` restored from the original
baseline. The first pilot's used world remains intact. The worker/PackLock are
unchanged; no installation, worker rebuild, Minecraft process or model request
was performed. Independent checks confirm the 4,118-file inventory, empty
player state/session lock, exact public prompt, zero helpers, source pins,
both launch roles and all 38 unchanged authority tables.

At preparation time, job `validation-2026-09-18:m0-pilot-02` was **not authorized**.
The actual driver refuses `PILOT_INPUTS` before creating output, because current
admission accepts only the consumed first pilot identity. A distinct approved
one-run admission must be installed before this proposed job can execute.
The proposed bounds remain 90 seconds, six requests and $1 maximum within the
original $10, with every old hold/cost retained. That pending question was subsequently answered affirmatively as D16; this
sealed preparation remains the original unapproved version. No new allowance was added.

Preparation seal (14 files):
`b87085b07b156bce24c4b1f30c3a483ba1e7b838c3e82f424e052e2fad3da9ac`.
Plan SHA:
`e99e7a2252cc0850c5d430107769c9e5f3f17112e3ee1393fdcd776727d278a5`.
Preserve this version and reuse its unused instance if approved; any changed
admission/source metadata gets a new input version, not an in-place rewrite.

D16 subsequently approved the exact proposed limits. The changed admission source
passes 87 focused accounting/piloting/OAuth checks and full Ruff. Refreshed native
case03 passes 15/15 with three scripted requests, zero helpers and native exit 0;
all 38 original-authority tables remain unchanged. Its seal (3,720 files) is
`2d8d4edf168e3e334f3b96fcba74693b4b051da08260c9f013ea472962d237eb`.
Approved input version `2026-09-23-m0-pilot-d16-01` reuses the unchanged unused
instance; its seal (six files) is
`47d53d34aa4d24010fa85e51e82dcc07d5e6f3a1b8bf585bb8d089502f56305b`.
The D16 plan SHA is
`247079b4096c332494e7e9204e695c2b19e21a314363cd24c75f53934ae1bb6c`.

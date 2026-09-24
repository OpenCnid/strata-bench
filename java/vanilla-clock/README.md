# Private vanilla clock agent

This is an operator-only observer for the official Minecraft1.19.2 server.
`mcbench.vanilla_clock.prepare_vanilla_clock` builds it offline with the pinned
JDK17 compiler and ASM9.7.1 bytes. Generated JARs, installed game files, private
configuration and journals remain outside the repository and gameplay tools.

The two original class hashes are fixed in `Agent.java`. ASM inserts only
no-argument entry/return callbacks and a UUID callback at the normal return of
`ServerPlayer.doTick`. Unmatched bytes or redefinition halt the owned JVM with
exit126; an ignored transformer exception must not permit unmeasured execution.
The observer neither reads hidden world state nor chooses/dispatches actions.

Mojang's bundler parents its game loader to the platform loader. The agent thus
extracts its byte-bound callback-only JAR to a fresh private output path and
adds that JAR to bootstrap search. Agent/ASM classes stay in their app-loader
package. The private launcher holds the original JAR/configuration, passes DOS/
UNC spellings to Java, and checks the generated callback JAR after owned stop.

The state machine records ordered completed server ticks, actual player-method
returns, per-tick work and monotonic startup/drain exposure. It enforces one
server thread, unique UUIDs per tick and at most64UUIDs. A fault is sticky.
Windows contain actual elapsed time and completed work, including late samples;
the terminal record retains the partial tail. Counts are never inferred from
wall time, saved game time or client physics.

`tools/development_server.py` accepts a `strata/DevelopmentServer/6` envelope with
`base` (an existing vanilla `/2`, `/4` or `/5` plan) and `clock` (exact agent path/
hash, campaign/avatar/epoch and distinct run ID). It records the complete envelope,
changed argument vector and composite launch identity. It does not mutate or
mislabel the original sealed PackLock. The stopped reader checks the complete
series against that scope/module and the JVM identity observed while alive.

The authentic headless case proves server callback production and normal-stop
capture only. Connected avatar mapping, native root/helper cost/time joins,
measurement overhead and capacity/isolation qualification remain separate.
See [verification](../../docs/verification/2026-09-24-vanilla-clocks.md).

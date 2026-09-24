"""Private exact-version vanilla callback instrumentation and stopped reader.

Preparation is offline. A caller must bind the resulting agent, launch scope,
owned JVM identity and stopped journal; a matching text file alone is not proof.
"""

import hashlib
import io
import math
from pathlib import Path
import re
import subprocess
import zipfile

from .inference_transport import strict_json
from .inventory import file_hash
from .storage import canonical, reject_links, require

POLICY = "vanilla1192-method-callback-clock/1"
ROOT = Path(__file__).resolve().parents[2]
ASM_SHA = "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281"
CLASS_PINS = {
    "net/minecraft/server/MinecraftServer": "bb6ab22cbdff49b8f7a76523a21ed54166244b914d63064d1a30f2e1747f802f",
    "agh": "cc6a79060c45ab954bcf80a301b8a21ed48b43fee9eb29ab4a13b28c93b10ad2",
}
MAX_BYTES = 4 * 1024**2


def prepare_vanilla_clock(javac, asm, destination):
    javac, asm, destination = map(Path, (javac, asm, destination))
    for path in (javac, asm, destination):
        require(path.is_absolute(), "UNSAFE_PATH")
        reject_links(path)
    require(not destination.exists() and not destination.is_relative_to(ROOT), "VANILLA_CLOCK_DESTINATION")
    require(file_hash(asm) == ASM_SHA, "VANILLA_CLOCK_ASM_PIN")
    compiler = strict_json((ROOT / "java/build-inputs.json").read_bytes())["compiler"]["javac_sha256"]
    require(file_hash(javac) == compiler, "VANILLA_CLOCK_COMPILER_PIN")
    source = sorted((ROOT / "java/vanilla-clock/src").rglob("*.java"))
    require({p.name for p in source} == {"Agent.java", "Clock.java", "Ticks.java"} and len(source) == 3,
            "VANILLA_CLOCK_SOURCE")
    pins = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in source}
    destination.mkdir(parents=True)
    classes = destination / "classes"
    classes.mkdir()
    result = subprocess.run([str(javac), "--release", "17", "-g:none", "-encoding", "UTF-8",
        "-classpath", str(asm), "-d", str(classes), *(str(p) for p in source)], capture_output=True, timeout=60)
    (destination / "compiler.stdout").write_bytes(result.stdout)
    (destination / "compiler.stderr").write_bytes(result.stderr)
    require(result.returncode == 0, "VANILLA_CLOCK_COMPILE")
    entries = {p.relative_to(classes).as_posix(): p.read_bytes() for p in classes.rglob("*.class")}
    require(entries and all(n.startswith("io/github/opencnid/strata/vanillaclock/") for n in entries),
            "VANILLA_CLOCK_CLASS_INVENTORY")
    callbacks = {n: raw for n, raw in entries.items() if Path(n).name.startswith(("Clock", "Ticks"))}
    entries = {n: raw for n, raw in entries.items() if n not in callbacks}
    callback_bytes = io.BytesIO()
    with zipfile.ZipFile(callback_bytes, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(callbacks.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw)
    entries["strata-clock-callbacks.jar"] = callback_bytes.getvalue()
    # Retain the dependency's exact classes and original manifest in the private
    # generated artifact; repository source does not vendor game or library bytes.
    with zipfile.ZipFile(asm) as archive:
        entries.update({n: archive.read(n) for n in archive.namelist()
                        if n.startswith("org/objectweb/asm/") and n.endswith(".class")})
        entries["META-INF/strata-asm-manifest.mf"] = archive.read("META-INF/MANIFEST.MF")
    entries["META-INF/MANIFEST.MF"] = ("Manifest-Version: 1.0\r\n"
        "Premain-Class: io.github.opencnid.strata.vanillaclock.Agent\r\n"
        "Can-Redefine-Classes: false\r\nCan-Retransform-Classes: false\r\n\r\n").encode()
    jar = destination / "strata-vanilla-clock-0.1.0.jar"
    with zipfile.ZipFile(jar, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw)
    require(file_hash(asm) == ASM_SHA and file_hash(javac) == compiler
            and all(file_hash(ROOT / n) == sha for n, sha in pins.items()), "SOURCE_CHANGED")
    with zipfile.ZipFile(jar) as archive:
        require({n: archive.read(n) for n in archive.namelist()} == entries, "HASH_MISMATCH")
    receipt = {"schema": "strata/VanillaClockAgent/1", "policy": POLICY,
        "jar_sha256": file_hash(jar), "jar_bytes": jar.stat().st_size,
        "asm_sha256": ASM_SHA, "compiler_sha256": compiler, "source_pins": pins, "class_pins": CLASS_PINS,
        "entries": {n: hashlib.sha256(raw).hexdigest() for n, raw in entries.items()},
        "installed": False, "game_conformance_qualified": False, "campaign_admission": False}
    (destination / "receipt.json").write_bytes(canonical(receipt))
    return receipt


def uint(value):
    return type(value) is int and 0 <= value <= 2**53 - 1


def inspect_vanilla_clock(path, *, scope, module_sha256, pid=None, expected_sha256=None):
    path = Path(path)
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES, "VANILLA_CLOCK_QUOTA")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(0 < len(raw) <= MAX_BYTES, "VANILLA_CLOCK_QUOTA")
    sha = hashlib.sha256(raw).hexdigest()
    require(expected_sha256 is None or sha == expected_sha256, "VANILLA_CLOCK_CHANGED")
    lines = raw.splitlines(keepends=True)
    require(3 <= len(lines) <= 2048 and all(line.endswith(b"\n") and len(line) <= 131072 for line in lines),
            "VANILLA_CLOCK_INCOMPLETE")
    require(set(scope) == {"campaign_id", "agent_id", "epoch", "run_id"}, "VANILLA_CLOCK_SCOPE")
    require(all(isinstance(scope[k], str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", scope[k])
                for k in ("campaign_id", "agent_id", "run_id"))
            and uint(scope["epoch"]) and scope["epoch"] > 0
            and isinstance(module_sha256, str) and re.fullmatch("[0-9a-f]{64}", module_sha256)
            and (pid is None or uint(pid) and pid > 0), "VANILLA_CLOCK_SCOPE")
    records = []
    for seq, line in enumerate(lines, 1):
        record = strict_json(line)
        require(set(record) == {"seq", "body"} and type(record["seq"]) is int and record["seq"] == seq
                and isinstance(record["body"], dict), "VANILLA_CLOCK_SEQUENCE")
        records.append(record["body"])
    header = records[0]
    require(set(header) == {"schema", "policy", *scope, "module_sha256", "pid", "origin", "terminal", "period_ns"}
            and header["schema"] == "strata/VanillaClockStart/1" and header["policy"] == POLICY
            and header["module_sha256"] == module_sha256 and header["origin"] == "runServer-entry"
            and header["terminal"] == "stopServer-return" and header["period_ns"] == 1_000_000_000
            and uint(header["pid"]) and header["pid"] > 0 and (pid is None or header["pid"] == pid)
            and all(header[k] == v and type(header[k]) is type(v) for k, v in scope.items()),
            "VANILLA_CLOCK_BINDING")
    bindings, samples, durations, avatars = {}, [], [], {}
    running = terminal = False
    ticks = work = elapsed = 0
    first = last = None
    keys = {"schema", "terminal", "run_elapsed_ns", "window_start_ns", "window_end_ns", "first_tick_ns",
            "last_tick_ns", "completed_server_ticks", "observed_tick_work_ns", "window_ticks", "window_work_ns",
            "tick_work_ns", "avatar_tick_events"}
    for body in records[1:]:
        require(not terminal, "VANILLA_CLOCK_AFTER_TERMINAL")
        schema = body.get("schema")
        if schema == "strata/VanillaClockBinding/1":
            require(set(body) == {"schema", "class", "original_sha256", "transformed_sha256"}
                    and body["class"] in CLASS_PINS and body["class"] not in bindings
                    and body["original_sha256"] == CLASS_PINS[body["class"]]
                    and isinstance(body["transformed_sha256"], str)
                    and re.fullmatch("[0-9a-f]{64}", body["transformed_sha256"]), "VANILLA_CLOCK_CLASS_PIN")
            bindings[body["class"]] = body
            continue
        if schema == "strata/VanillaClockRunning/1":
            require(set(body) == {"schema"} and not running and "net/minecraft/server/MinecraftServer" in bindings,
                    "VANILLA_CLOCK_ORDER")
            running = True
            continue
        require(schema == "strata/VanillaClockSample/1" and running and set(body) == keys,
                "VANILLA_CLOCK_ORDER")
        require(type(body["terminal"]) is bool and all(uint(body[k]) for k in (
            "run_elapsed_ns", "window_start_ns", "window_end_ns", "completed_server_ticks",
            "observed_tick_work_ns", "window_ticks", "window_work_ns")), "VANILLA_CLOCK_COUNTER")
        ended, total, total_work = body["run_elapsed_ns"], body["completed_server_ticks"], body["observed_tick_work_ns"]
        require(body["window_start_ns"] == elapsed <= ended == body["window_end_ns"]
                and total >= ticks and total_work >= work and total_work <= ended
                and body["window_ticks"] == total - ticks and body["window_work_ns"] == total_work - work,
                "VANILLA_CLOCK_CONTINUITY")
        values = body["tick_work_ns"]
        require(isinstance(values, list) and len(values) <= 4096 and all(uint(v) for v in values)
                and len(values) == total - ticks and sum(values) == total_work - work <= ended - elapsed,
                "VANILLA_CLOCK_WORK")
        start_tick, end_tick = body["first_tick_ns"], body["last_tick_ns"]
        require((start_tick is None and end_tick is None and total == 0) or
                (uint(start_tick) and uint(end_tick) and start_tick <= end_tick <= ended and total > 0
                 and total_work <= end_tick - start_tick
                 and (first is None or first == start_tick) and (last is None or last <= end_tick)
                 and (total > ticks or end_tick == last)),
                "VANILLA_CLOCK_TICK_BOUNDS")
        current = body["avatar_tick_events"]
        require(isinstance(current, dict) and len(current) <= 64 and avatars.keys() <= current.keys()
                and (not current or "agh" in bindings), "VANILLA_CLOCK_AVATARS")
        for uuid, count in current.items():
            require(re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", uuid)
                    and uint(count) and 0 < count and avatars.get(uuid, 0) <= count <= total
                    and count - avatars.get(uuid, 0) <= total - ticks, "VANILLA_CLOCK_AVATARS")
        terminal = body["terminal"]
        require(terminal or ended - elapsed >= 1_000_000_000, "VANILLA_CLOCK_PERIOD")
        samples.append(body)
        durations.extend(values)
        require(len(durations) <= 65536, "VANILLA_CLOCK_QUOTA")
        ticks, work, elapsed, first, last, avatars = total, total_work, ended, start_tick, end_tick, current
    require(terminal and running, "VANILLA_CLOCK_INCOMPLETE")
    ordered = sorted(durations)
    with path.open("rb") as stream:
        require(stream.read(MAX_BYTES + 1) == raw, "VANILLA_CLOCK_CHANGED")
    return {"schema": "strata/VanillaClockReport/1", "policy": POLICY, "visibility": "evaluator",
        **scope, "source_sha256": sha, "header": header, "class_bindings": bindings,
        "completed_server_ticks": ticks, "avatar_tick_events": avatars, "observed_tick_work_ns": work,
        "run_elapsed_ns": elapsed, "first_tick_ns": first, "last_tick_ns": last,
        "completed_tick_work_p95_ns": ordered[math.ceil(len(ordered)*.95)-1] if ordered else None,
        "samples": samples, "source_process_bound": pid is not None,
        "active_wall_s": None, "isolation_qualified": False, "capacity_qualified": False,
        "gaps": ["pre_run_and_post_stop_process_intervals", "campaign_active_time_join",
                 "avatar_roster_binding", "telemetry_overhead_control", "rolling_capacity_qualification"]}


class ClockLaunch:
    """Declared development overlay, held through owned stop; not a new PackLock."""

    def __init__(self, value, evidence, game_root, launch):
        from .launch_integrity import FileLease, safe, snapshot
        from .storage import digest
        from .worker_bundle import launch_path
        require(set(value) == {"agent_path", "agent_sha256", "campaign_id", "agent_id", "epoch", "run_id"},
                "VANILLA_CLOCK_LAUNCH")
        self.scope = {k: value[k] for k in ("campaign_id", "agent_id", "epoch", "run_id")}
        require(all(isinstance(value[k], str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value[k])
                    for k in ("campaign_id", "agent_id", "run_id"))
                and type(value["epoch"]) is int and 1 <= value["epoch"] <= 999999999
                and isinstance(value["agent_sha256"], str) and re.fullmatch("[0-9a-f]{64}", value["agent_sha256"]),
                "VANILLA_CLOCK_SCOPE")
        self.agent = safe(value["agent_path"])
        self.evidence = safe(evidence)
        game_root = safe(game_root)
        require(not self.agent.is_relative_to(game_root) and not self.agent.is_relative_to(ROOT)
                and not self.evidence.is_relative_to(game_root) and not game_root.is_relative_to(self.evidence),
                "VANILLA_CLOCK_PATH")
        require(self.agent.stat().st_size <= 1024**2 and file_hash(self.agent) == value["agent_sha256"],
                "VANILLA_CLOCK_AGENT_PIN")
        self.sha = value["agent_sha256"]
        self.identity = None
        with zipfile.ZipFile(self.agent) as jar:
            require(jar.getinfo("strata-clock-callbacks.jar").file_size <= 262144, "VANILLA_CLOCK_QUOTA")
            self.callbacks_sha = hashlib.sha256(jar.read("strata-clock-callbacks.jar")).hexdigest()
        self.output = self.evidence / "vanilla-clock.jsonl"
        self.config = self.evidence / "vanilla-clock.config"
        values = self.scope | {"output": launch_path(self.output)}
        require(not any("\n" in str(v) or "\r" in str(v) for v in values.values()), "VANILLA_CLOCK_CONFIG")
        with self.config.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("".join(f"{k}={v}\n" for k, v in values.items()))
        inventory = snapshot([self.agent, self.config], [])
        self.lease = FileLease(inventory)
        self.executable = Path(launch.executable_path).resolve()
        # The Windows JVM agent loader rejects extended Win32 path spellings.
        # Keep those for custody, pass equivalent DOS/UNC paths to the JVM.
        self.arguments = [f"-javaagent:{launch_path(self.agent)}={launch_path(self.config)}", *launch.arguments]
        self.binding = {"schema": "strata/VanillaClockLaunch/1", "policy": POLICY,
            "base_launch_digest": digest(launch.model_dump()), "agent_sha256": self.sha,
            "callbacks_sha256": self.callbacks_sha, "configuration_sha256": file_hash(self.config),
            "arguments": self.arguments, "inventory": inventory, **self.scope,
            "original_pack_profile_unchanged_claim": False, "campaign_admission": False}
        self.binding["composite_launch_digest"] = digest(self.binding)

    def observe(self, process):
        """Capture image/start identity while alive; the Job retains its handle."""
        if self.identity is not None or not self.output.exists():
            return
        reject_links(self.output)
        with self.output.open("rb") as stream:
            line = stream.readline(131073)
        if not line.endswith(b"\n"):
            require(len(line) <= 131072, "VANILLA_CLOCK_QUOTA")
            return
        header = strict_json(line)["body"]
        pid = header["pid"]
        require(uint(pid) and pid > 0, "VANILLA_CLOCK_PROCESS")
        if pid not in process.job.members:
            return  # It may have started just after this iteration's Job query.
        identity = process.job.member_identity(pid)
        require(Path(identity["executable"]).resolve() == self.executable, "VANILLA_CLOCK_PROCESS")
        self.identity = identity

    def finish(self, process):
        require(self.output.is_file() and self.output.stat().st_size <= MAX_BYTES, "VANILLA_CLOCK_INCOMPLETE")
        with self.output.open("rb") as stream:
            header = strict_json(stream.readline(131073))["body"]
        pid = header["pid"]
        identity = self.identity
        require(identity is not None and identity["pid"] == pid and pid in process.job.members,
                "VANILLA_CLOCK_PROCESS")
        job, held = process.job.accounting(), process.job.member_status()
        require(job["active_processes"] == job["terminated_processes"] == 0
                and job["total_processes"] == held["held_processes"] == held["signaled_processes"],
                "VANILLA_CLOCK_PROCESS")
        require(file_hash(self.evidence / "vanilla-clock-callbacks.jar") == self.callbacks_sha,
                "VANILLA_CLOCK_AGENT_PIN")
        self.lease.recheck()
        report = inspect_vanilla_clock(self.output, scope=self.scope, module_sha256=self.sha, pid=pid)
        return report | {"owned_jvm": identity, "owned_processes": {"job": job, "held": held},
                         "launch_binding": self.binding}

    def close(self):
        self.lease.close()

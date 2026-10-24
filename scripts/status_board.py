#!/usr/bin/env python3
"""Generate the module board from status/modules.json and the component checkouts.

  status_board.py [--run-checks] [--out docs]

For every module the generator records the declared state and tag, whether each
declared path exists in the component checkout ("presence"), and, with
--run-checks, the result of each hosted check command run from the component
root. It writes docs/index.html (self-contained page), docs/STATUS_BOARD.md and
docs/status.json. The declared state is a human judgement taken from the plan;
presence and checks are measured.
"""
import argparse
import datetime as dt
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_ORDER = ["planned", "scaffold", "model", "bounded", "native", "stable"]
TAG_LABEL = {"new": "新增", "upgrade": "升级", "move": "迁移", "shrink": "收缩", "keep": "不变"}
STATE_LABEL = {"planned": "计划", "scaffold": "脚手架", "model": "模型", "bounded": "有界", "native": "原生", "stable": "稳定"}


def git_head(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=12", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "missing"


def run_check(repo: Path, command: str, timeout: int) -> dict:
    try:
        result = subprocess.run(command, shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout)
        ok = result.returncode == 0
        tail = (result.stdout + result.stderr).strip().splitlines()[-1:] or [""]
        return {"command": command, "ok": ok, "detail": tail[0][:200]}
    except subprocess.TimeoutExpired:
        return {"command": command, "ok": False, "detail": f"timeout after {timeout}s"}
    except Exception as error:  # noqa: BLE001
        return {"command": command, "ok": False, "detail": str(error)[:200]}


def measure(spec: dict, run_checks: bool, timeout: int) -> dict:
    heads = {}
    modules = []
    for m in spec["modules"]:
        repo = ROOT / m["repo"] if m["repo"] != "ObfuscationProject" else ROOT
        if m["repo"] not in heads:
            heads[m["repo"]] = git_head(repo)
        present = [p for p in m["paths"] if (repo / p).exists()]
        checks = [run_check(repo, c, timeout) for c in m["checks"]] if run_checks else []
        modules.append({**m, "present": len(present), "declared": len(m["paths"]),
                        "missing": [p for p in m["paths"] if p not in present], "check_results": checks})
    return {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "heads": heads, "checks_run": run_checks, "modules": modules}


def write_markdown(spec: dict, data: dict, out: Path) -> None:
    lines = [f"# {spec['title']}", "",
             f"Generated {data['generated']} from " + ", ".join(f"{k}@{v}" for k, v in data["heads"].items()) + ".",
             "", "State is the declared judgement from the plans; presence counts declared paths found on main; checks are hosted commands"
             + (" (run)." if data["checks_run"] else " (not run in this generation)."), ""]
    counts = {s: 0 for s in STATE_ORDER}
    for m in data["modules"]:
        counts[m["state"]] += 1
    lines += ["| " + " | ".join(STATE_LABEL[s] + f" ({s})" for s in STATE_ORDER) + " |",
              "| " + " | ".join("---" for _ in STATE_ORDER) + " |",
              "| " + " | ".join(str(counts[s]) for s in STATE_ORDER) + " |", ""]
    for layer in spec["layers"]:
        lines += [f"## {layer['title']}" + (f" · {layer['subtitle']}" if layer["subtitle"] else ""), "",
                  "| Module | Tag | State | Presence | Checks | Plan | Summary |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for m in data["modules"]:
            if m["layer"] != layer["id"]:
                continue
            presence = f"{m['present']}/{m['declared']}" if m["declared"] else "—"
            if m["check_results"]:
                passed = sum(1 for c in m["check_results"] if c["ok"])
                checks = f"{passed}/{len(m['check_results'])} pass"
            else:
                checks = f"{len(m['checks'])} declared" if m["checks"] else "—"
            lines.append(f"| {m['title']} | {TAG_LABEL[m['tag']]} | {STATE_LABEL[m['state']]} | {presence} | {checks} | {m['plan'] or '—'} | {m['summary']} |")
        lines.append("")
    out.write_text("\n".join(lines))


HTML_HEAD = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f4f6f9;--surface:#fff;--fg:#18212b;--muted:#5b6773;--line:#d6dde5;--accent:#0e7490;--accent-soft:#ddf0f5;
--k-bg:#e7edf7;--k-line:#8da3c6;--o-bg:#e4f3ec;--o-line:#7db497;--t-bg:#ecedf0;--t-line:#a6abb6;
--s-planned:#6b7280;--s-scaffold:#7c3aed;--s-model:#9ca3af;--s-bounded:#b45309;--s-native:#0e7490;--s-stable:#15803d;--ok:#15803d;--bad:#b42318;
font-family:"IBM Plex Sans","Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e1319;--surface:#151c25;--fg:#e4e9ef;--muted:#98a5b3;--line:#2a3542;--accent:#38bdf8;--accent-soft:#10303f;
--k-bg:#1a2639;--k-line:#4f6b99;--o-bg:#14302a;--o-line:#3f8a69;--t-bg:#20242c;--t-line:#5a606e;--s-planned:#9ca3af;--s-scaffold:#a78bfa;--s-model:#9ca3af;--s-bounded:#f59e0b;--s-native:#38bdf8;--s-stable:#4ade80;--ok:#4ade80;--bad:#f97066;color-scheme:dark}}
:root[data-theme=dark]{--bg:#0e1319;--surface:#151c25;--fg:#e4e9ef;--muted:#98a5b3;--line:#2a3542;--accent:#38bdf8;--accent-soft:#10303f;
--k-bg:#1a2639;--k-line:#4f6b99;--o-bg:#14302a;--o-line:#3f8a69;--t-bg:#20242c;--t-line:#5a606e;--s-planned:#9ca3af;--s-scaffold:#a78bfa;--s-model:#9ca3af;--s-bounded:#f59e0b;--s-native:#38bdf8;--s-stable:#4ade80;--ok:#4ade80;--bad:#f97066;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-size:14px;line-height:1.5;padding:24px max(16px,env(safe-area-inset-right,0px)) 48px max(16px,env(safe-area-inset-left,0px))}
.wrap{max-width:1180px;margin:0 auto}h1{font-size:24px;margin:0 0 4px}.meta{color:var(--muted);font-family:"IBM Plex Mono",monospace;font-size:12px;margin-bottom:16px}
.summary{display:flex;flex-wrap:wrap;gap:8px 18px;margin:0 0 18px;font-size:13px}.summary span b{font-family:"IBM Plex Mono",monospace}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:var(--muted);margin-bottom:18px}
.board{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px;display:grid;gap:8px}
.layer{display:grid;grid-template-columns:128px minmax(0,1fr);gap:10px}.lbl{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);padding-top:7px}
.lbl small{display:block;text-transform:none;letter-spacing:0;font-weight:400;font-size:10.5px}
.boxes{display:flex;flex-wrap:wrap;gap:6px}.box{flex:1 1 180px;min-width:0;border:1px solid var(--k-line);background:var(--k-bg);border-radius:4px;padding:7px 9px;font-size:12.5px;border-left-width:4px}
.box.o{background:var(--o-bg);border-color:var(--o-line)}.box.t{background:var(--t-bg);border-color:var(--t-line)}
.box[data-state=planned]{border-left-color:var(--s-planned)}.box[data-state=scaffold]{border-left-color:var(--s-scaffold)}.box[data-state=model]{border-left-color:var(--s-model)}
.box[data-state=bounded]{border-left-color:var(--s-bounded)}.box[data-state=native]{border-left-color:var(--s-native)}.box[data-state=stable]{border-left-color:var(--s-stable)}
.box b{display:block;font-weight:600}.box small{display:block;color:var(--muted);font-size:11.5px}
.tag{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;padding:0 5px;border-radius:3px;margin-left:6px;vertical-align:1px;color:var(--surface)}
.tag.new{background:var(--accent)}.tag.upgrade{background:var(--s-bounded)}.tag.move{background:var(--o-line)}.tag.shrink,.tag.keep{background:var(--t-line)}
.st{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10.5px;padding:0 6px;border-radius:999px;border:1px solid currentColor;margin-right:6px}
.st.planned{color:var(--s-planned)}.st.scaffold{color:var(--s-scaffold)}.st.model{color:var(--s-model)}.st.bounded{color:var(--s-bounded)}.st.native{color:var(--s-native)}.st.stable{color:var(--s-stable)}
.m{margin-top:4px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--muted)}.m .ok{color:var(--ok)}.m .bad{color:var(--bad)}
.band{grid-column:1/-1;border:1px dashed var(--accent);background:var(--accent-soft);border-radius:4px;padding:8px 12px;font-size:12.5px}
@media (max-width:640px){.layer{grid-template-columns:1fr}}
</style></head><body><div class="wrap">"""


def write_html(spec: dict, data: dict, out: Path) -> None:
    e = html.escape
    counts = {s: 0 for s in STATE_ORDER}
    for m in data["modules"]:
        counts[m["state"]] += 1
    parts = [HTML_HEAD.replace("__TITLE__", e(spec["title"]))]
    parts.append(f"<h1>{e(spec['title'])}</h1>")
    parts.append("<div class='meta'>generated " + e(data["generated"]) + " · " +
                 " · ".join(f"{e(k)}@{e(v)}" for k, v in data["heads"].items()) +
                 (" · checks run" if data["checks_run"] else " · checks not run") + "</div>")
    parts.append("<div class='summary'>" + "".join(
        f"<span><i class='st {s}'>{e(STATE_LABEL[s])}</i><b>{counts[s]}</b></span>" for s in STATE_ORDER) + "</div>")
    parts.append("<div class='legend'>" + " ".join(
        f"<span><i class='st {s}'>{e(STATE_LABEL[s])}</i>{e(spec['states'][s])}</span>" for s in STATE_ORDER) + "</div>")
    parts.append("<div class='board'>")
    for layer in spec["layers"]:
        mods = [m for m in data["modules"] if m["layer"] == layer["id"]]
        if layer["id"] == "sdk":
            m = mods[0]
            parts.append(f"<div class='band'><b>{e(m['title'])}</b> <i class='st {m['state']}'>{e(STATE_LABEL[m['state']])}</i> {e(m['summary'])}</div>")
            continue
        parts.append(f"<div class='layer'><div class='lbl'>{e(layer['title'])}<small>{e(layer['subtitle'])}</small></div><div class='boxes'>")
        for m in mods:
            cls = "o" if m["repo"] == "ObfuscationOS" else ("t" if layer["id"] == "eng" else "")
            presence = f"{m['present']}/{m['declared']} 文件" if m["declared"] else "无声明路径"
            pcls = "ok" if m["declared"] and m["present"] == m["declared"] else ("bad" if m["declared"] else "")
            if m["check_results"]:
                passed = sum(1 for c in m["check_results"] if c["ok"])
                ccls = "ok" if passed == len(m["check_results"]) else "bad"
                checks = f" · <span class='{ccls}'>检查 {passed}/{len(m['check_results'])}</span>"
            else:
                checks = f" · 检查 {len(m['checks'])} 项未跑" if m["checks"] else ""
            plan = f" · {e(m['plan'])}" if m["plan"] else ""
            parts.append(f"<div class='box {cls}' data-state='{m['state']}'><b>{e(m['title'])}<i class='tag {m['tag']}'>{e(TAG_LABEL[m['tag']])}</i></b>"
                         f"<small>{e(m['summary'])}</small><div class='m'><i class='st {m['state']}'>{e(STATE_LABEL[m['state']])}</i>"
                         f"<span class='{pcls}'>{e(presence)}</span>{checks}{plan}</div></div>")
        parts.append("</div></div>")
    parts.append("</div></div></body></html>")
    out.write_text("".join(parts))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-checks", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out", default=str(ROOT / "docs"))
    args = ap.parse_args()
    spec = json.loads((ROOT / "status/modules.json").read_text())
    layer_ids = {l["id"] for l in spec["layers"]}
    for m in spec["modules"]:
        assert m["layer"] in layer_ids and m["state"] in STATE_ORDER and m["tag"] in TAG_LABEL, m["id"]
    data = measure(spec, args.run_checks, args.timeout)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "status.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    write_markdown(spec, data, out / "STATUS_BOARD.md")
    write_html(spec, data, out / "index.html")
    failed = [(m["id"], c) for m in data["modules"] for c in m["check_results"] if not c["ok"]]
    missing = [(m["id"], p) for m in data["modules"] for p in m["missing"]]
    for mid, p in missing:
        print(f"missing path: {mid}: {p}")
    for mid, c in failed:
        print(f"check failed: {mid}: {c['command']}: {c['detail']}")
    print(f"board: {len(data['modules'])} modules, {len(missing)} missing paths, {len(failed)} failed checks -> {out}")
    return 1 if (missing or failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())

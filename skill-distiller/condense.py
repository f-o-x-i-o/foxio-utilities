#!/usr/bin/env python3
"""
condense.py — Comprime transcripts JSONL de Claude Code dejando SOLO la senal
util para destilar aprendizajes de un proceso de desarrollo:
  - lo que el humano pidio / corrigio (user text)
  - lo que se PROBO (tool_use: comandos, edits, etc.)
  - lo que FALLO (tool_result con error / errores de API)
  - decisiones del asistente (assistant text)
Tira la basura: file reads gigantes, tool_results exitosos largos, thinking.

Uso:
  python3 condense.py <dir-o-archivos.jsonl> [--thinking] [--cap N] > out.md

<dir-o-archivos> puede ser:
  - un directorio de ~/.claude/projects/<...>/  (toma todos los *.jsonl)
  - uno o varios archivos .jsonl
"""
import sys, os, json, glob, argparse

NOISE_TAGS = ("<ide_opened_file>", "<local-command-caveat>", "<command-name>",
              "<command-message>", "<command-args>", "<local-command-stdout>",
              "<system-reminder>", "<ide_selection>", "<ide_diagnostics>")

def is_noise(text):
    t = text.strip()
    return any(t.startswith(tag) for tag in NOISE_TAGS)

def short(s, cap):
    s = " ".join(str(s).split())
    return s if len(s) <= cap else s[:cap] + " …[+%d]" % (len(s) - cap)

def tool_use_line(b, cap):
    name = b.get("name", "?")
    inp = b.get("input", {}) or {}
    if name == "Bash":
        return "🔧 $ " + short(inp.get("command", ""), cap)
    if name in ("Edit", "Write", "NotebookEdit"):
        return "🔧 %s %s" % (name, inp.get("file_path", inp.get("notebook_path", "")))
    if name == "Read":
        return "🔧 Read %s" % inp.get("file_path", "")
    if name in ("Grep", "Glob"):
        return "🔧 %s %s" % (name, short(inp.get("pattern", inp.get("query", "")), 80))
    return "🔧 %s(%s)" % (name, short(json.dumps(inp, ensure_ascii=False), cap))

def looks_error(text):
    t = text.lower()
    return any(k in t for k in ("error", "traceback", "exception", "failed",
                                "cannot", "not found", "refused", "fatal",
                                "econnrefused", "panic", "undefined"))

def tool_result_line(b, cap):
    content = b.get("content", "")
    if isinstance(content, list):
        content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    content = str(content)
    is_err = b.get("is_error") or looks_error(content[:400])
    if is_err:
        return "❌ result: " + short(content, cap * 2)
    if len(content) <= 200:
        return "✓ " + short(content, 200)
    return "✓ result (%d chars elided)" % len(content)

def render(path, args, out):
    keep = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        t = o.get("type")
        if t not in ("user", "assistant"):
            continue
        if o.get("isApiErrorMessage"):
            keep.append("⚠️ API ERROR: " + short(json.dumps(o.get("message", {}))[:300], 300))
            continue
        msg = o.get("message", {}) or {}
        content = msg.get("content")
        if isinstance(content, str):
            if content.strip() and not is_noise(content):
                keep.append(("👤 " if t == "user" else "🤖 ") + short(content, args.cap))
            continue
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text":
                txt = b.get("text", "").strip()
                if txt and not is_noise(txt):
                    keep.append(("👤 " if t == "user" else "🤖 ") + short(txt, args.cap))
            elif bt == "thinking" and args.thinking:
                keep.append("💭 " + short(b.get("thinking", ""), args.cap))
            elif bt == "tool_use":
                keep.append(tool_use_line(b, args.cap))
            elif bt == "tool_result":
                keep.append(tool_result_line(b, args.cap))
    if keep:
        out.write("\n\n## SESSION: %s\n\n" % os.path.basename(path))
        out.write("\n".join(keep))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--thinking", action="store_true", help="incluir bloques de razonamiento")
    ap.add_argument("--cap", type=int, default=600, help="max chars por bloque")
    args = ap.parse_args()

    if os.path.isdir(args.target):
        files = sorted(glob.glob(os.path.join(args.target, "*.jsonl")), key=os.path.getmtime)
    else:
        files = sorted(glob.glob(args.target), key=os.path.getmtime)
    if not files:
        sys.exit("No encontre .jsonl en: " + args.target)

    out = sys.stdout
    out.write("# Transcript condensado (%d sesiones)\n" % len(files))
    for f in files:
        render(f, args, out)

if __name__ == "__main__":
    main()

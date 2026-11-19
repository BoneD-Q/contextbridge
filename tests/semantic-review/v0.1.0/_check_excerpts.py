from pathlib import Path
import json

p = Path(__file__).resolve().parents[3] / "examples/technical-proposal/generated-output"
ev = json.loads((p / "evidence/evidence.json").read_text(encoding="utf-8"))["evidence"]
for e in ev:
    loc = e["locator"]
    path = p / loc["path"]
    lines = path.read_text(encoding="utf-8").splitlines()
    s = int(loc["start"])
    en = int(loc["end"] if loc["end"] is not None else loc["start"])
    span = "\n".join(lines[s - 1 : en])
    ex = loc["excerpt"]
    # every non-empty excerpt line must appear in span
    missing = [ln for ln in ex.splitlines() if ln.strip() and ln not in span]
    print(f"{e['evidence_id']}\t{s}-{en}\tmissing={len(missing)}\t{missing[:1]}")

# Agent mistakes (contextbridge)

## Exporter 整仓卡死
- 现象：用户在其它大仓跑 context-exporter → “Taking longer than expected…”，长时间无包。
- 错误：Agent 先通读全部 references/Schema，再递归扫仓库，迟迟不写文件。
- 正确：默认 fast-path（`references/fast-path.md`）；先 `scaffold_package.py`；仅用户点名的 ≤3 文件；禁止未授权整仓扫描。

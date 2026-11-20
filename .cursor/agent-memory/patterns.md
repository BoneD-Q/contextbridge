# Agent patterns (contextbridge)

## Exporter 快速路径
1. 读 `skills/context-exporter/references/fast-path.md`（不要先吞三份长 references）。
2. `python skills/context-exporter/scripts/scaffold_package.py <out> --package-id …`
3. 只复制白名单源文件 → 填 knowledge/evidence → 更新 manifest。
4. `validate_package.py` 出会话报告（包外保存）→ Importer。

## 跨项目发现 Skill
`python scripts/install_skills.py --dest <other-project-root>`  
canonical 仍在 ContextBridge `skills/`，对方项目只建 discovery 链接。

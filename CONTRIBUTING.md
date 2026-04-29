# Contributing to ChemMind Learn

感谢你参与贡献。

## 建议流程

1. Fork 仓库并创建分支。
2. 修改代码后先运行 `python test_all.py`。
3. 保持改动聚焦，尽量避免无关重构。
4. 提交 PR 时说明修改内容、影响范围和验证结果。

## 代码风格

- 优先保持现有项目风格
- 保持对 Windows 的兼容性
- 不要提交真实 API Key 或本地数据文件

## 验证要求

至少保证：

- `python test_all.py` 通过
- CLI 可以启动
- Web 可以启动

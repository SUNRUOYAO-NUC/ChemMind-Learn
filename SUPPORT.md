# Support

如果你在使用 ChemMind Learn 时遇到问题，可以先：

1. 查看 [README.md](README.md)
2. 查看 [docs/USAGE.md](docs/USAGE.md)
3. 运行 `python test_all.py` 检查环境是否正常

## 常见问题

- 如果无法连接模型服务，请确认 `.env` 中的 `LLM_API_KEY` 和 `LLM_BASE_URL` 是否正确。
- 如果 Web 启动失败，请确认端口未被占用。
- 如果没有真实 Key，项目会使用本地兜底逻辑，适合本地演示和测试。

## 反馈建议

提交 issue 时建议附上：

- Python 版本
- 操作系统
- 复现步骤
- 控制台报错信息

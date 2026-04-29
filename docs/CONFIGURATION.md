# 配置说明

ChemMind Learn 使用环境变量进行配置，推荐通过 `.env` 文件管理。

## 变量列表

- `LLM_API_KEY`：大模型 API Key
- `LLM_BASE_URL`：OpenAI 兼容接口地址
- `LLM_MODEL`：聊天模型名称
- `EMBEDDING_MODEL`：向量嵌入模型名称
- `CHROMA_PERSIST_DIR`：ChromaDB 持久化目录
- `WEB_PORT`：Web 服务端口

## 示例

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_data
WEB_PORT=8000
```

## 兼容建议

- 如果你使用兼容 OpenAI 协议的第三方服务，只需要修改 `LLM_BASE_URL`。
- 如果你没有真实 Key，项目会自动使用本地兜底逻辑，适合演示和离线测试。

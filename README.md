# ChemMind Learn

ChemMind Learn 是一个面向化学与理科学习场景的 AI 学习助手，支持费曼式讲解、AI 反向提问、长期记忆追踪，以及 CLI 和 Web 两种使用方式。

## 特性

- 费曼学习法导向的教学提示词
- AI 学生反向提问，用于检验理解程度
- 基于 ChromaDB 的学习记忆与薄弱点检索
- CLI 和 Web 两种入口
- 支持 OpenAI 兼容接口
- 无真实 API Key 时可离线运行，便于本地测试和开源分发

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 配置环境变量

复制 [.env.example](.env.example) 为 `.env`，然后按需修改：

```bash
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_data
WEB_PORT=8000
```

### 3. 启动 CLI

```bash
python app.py
```

### 4. 启动 Web

```bash
python app.py web
```

也可以指定端口：

```bash
python app.py web --port 8080
```

## 使用说明

CLI 模式下，先输入学习主题，再进行自由提问。输入 `/quiz` 进入测验阶段，输入 `/quit` 退出当前会话。

Web 模式下，页面支持同样的交互命令：

- `/quiz`：进入测验
- `/end`：结束本轮学习并生成报告
- `/new`：开启新主题

## 项目结构

- `app.py`：命令行和 Web 的统一入口
- `agents/`：教学、验证、记忆分析相关提示词与基础 Agent
- `memory/`：向量存储与长期记忆系统
- `models/`：Pydantic 数据模型
- `ui/`：CLI 和 Web 交互界面
- `utils/`：LLM 和 embedding 访问封装
- `test_all.py`：项目自检脚本

## 运行测试

```bash
python test_all.py
```

## 兼容性说明

- 支持 Windows、Linux、macOS
- 支持 Python 3.12+
- 支持 OpenAI 兼容服务端点
- 在没有真实 API Key 的情况下，也可以启动离线兜底逻辑进行本地演示和测试

## 开源说明

本项目面向 GitHub 开源发布，建议保留 `.env.example` 作为环境配置模板，不要提交真实密钥。

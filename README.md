# ChemMind Learn

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-Compatible-111827)](docs/CONFIGURATION.md)

ChemMind Learn 是一个面向化学与理科学习场景的 AI 学习助手。它结合了费曼学习法、AI 反向提问和长期记忆追踪，提供 CLI 和 Web 两种入口，适合个人学习、教学演示和开源扩展。

## 目录

- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [使用方式](#使用方式)
- [项目结构](#项目结构)
- [运行测试](#运行测试)
- [兼容性说明](#兼容性说明)
- [开源说明](#开源说明)
- [相关文档](#相关文档)

## 核心特性

- 费曼学习法导向的教学提示词，帮助用户用更自然的方式理解概念
- AI 学生反向提问，用于检验理解深度，而不是只做被动问答
- 基于 ChromaDB 的学习记忆与薄弱点检索
- CLI 和 Web 两种使用方式，适配不同场景
- 支持 OpenAI 兼容接口，方便接入第三方模型服务
- 无真实 API Key 时可离线运行，便于本地测试、演示和开源分发

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 配置环境变量

复制 [.env.example](.env.example) 为 `.env`，然后按需修改：

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_data
WEB_PORT=8000
```

### 3. 启动程序

CLI 模式：

```bash
python app.py
```

Web 模式：

```bash
python app.py web
```

指定端口：

```bash
python app.py web --port 8080
```

## 使用方式

CLI 模式下，先输入学习主题，再进行自由提问。常用命令如下：

- `/quiz`：进入测验阶段
- `/quit`：退出当前会话

Web 模式下支持相同的学习流程，并额外提供以下命令：

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
- `docs/`：配置、架构、使用指南等说明文档
- `test_all.py`：项目自检脚本

## 运行测试

```bash
python test_all.py
```

## 兼容性说明

- 支持 Windows、Linux、macOS
- 支持 Python 3.12+
- 支持 OpenAI 兼容服务端点
- 没有真实 API Key 时，仍可运行本地兜底逻辑完成演示和测试

## 开源说明

本项目面向 GitHub 开源发布，建议保留 [.env.example](.env.example) 作为环境配置模板，不要提交真实密钥或本地生成的数据文件。

## 相关文档

- [配置说明](docs/CONFIGURATION.md)
- [项目架构](docs/ARCHITECTURE.md)
- [使用指南](docs/USAGE.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [支持与反馈](SUPPORT.md)

# 项目架构

ChemMind Learn 由四个核心部分组成：对话入口、教学与测验 Agent、长期记忆系统、前端/CLI 交互层。

## 核心流程

1. 用户输入学习主题。
2. `teacher` Agent 基于费曼学习法进行讲解。
3. `validator` Agent 以学生身份反向提问。
4. `memory` 系统总结学习内容并存入 ChromaDB。
5. 下次进入时根据历史记录提醒复习。

## 主要模块

- `app.py`：程序入口
- `agents/`：提示词构建与 Agent 基类
- `memory/`：记忆分析与向量检索
- `models/`：数据结构定义
- `ui/`：CLI 和 Web 界面
- `utils/llm_client.py`：LLM 和 embedding 调用封装

## 设计目标

- 兼容 OpenAI 生态
- 支持本地离线兜底
- 便于 GitHub 开源发布
- 保持代码结构简单清晰，方便后续扩展

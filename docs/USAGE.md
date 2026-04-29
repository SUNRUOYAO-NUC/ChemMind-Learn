# 使用指南

## CLI 模式

```bash
python app.py
```

常用命令：

- `/quiz`：进入测验阶段
- `/quit`：退出当前会话

## Web 模式

```bash
python app.py web
```

如需指定端口：

```bash
python app.py web --port 8080
```

Web 页面常用命令：

- `/quiz`：开始反向提问
- `/end`：结束本轮学习并生成报告
- `/new`：重新开始一个主题

## 测试

```bash
python test_all.py
```

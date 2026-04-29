"""
ChemMind Learn 完整测试脚本
覆盖：配置、数据模型、Agent提示词构建、向量存储、记忆系统
运行方式：python test_all.py
"""
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch

# ── 0. 临时覆盖 ChromaDB 路径，避免污染本地数据 ──
tmpdir = tempfile.mkdtemp()
os.environ["CHROMA_PERSIST_DIR"] = tmpdir
os.environ["LLM_API_KEY"] = "sk-test-placeholder"
os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"
os.environ["LLM_MODEL"] = "gpt-4o"
os.environ["EMBEDDING_MODEL"] = "text-embedding-3-small"

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}  FAILED")

# ── 1. 配置模块 ──
print("\n[TEST] 测试: 配置模块")
from config import Config
cfg = Config()
check("LLM_API_KEY 读取环境变量", cfg.LLM_API_KEY == "sk-test-placeholder")
check("CHROMA_PERSIST_DIR 读取环境变量", cfg.CHROMA_PERSIST_DIR == tmpdir)
check("WEB_PORT 默认值", cfg.WEB_PORT == 8000)

# ── 2. 数据模型 ──
print("\n[TEST] 测试: 数据模型")
from models.schemas import LearningRecord, QuizQuestion, SessionState, ChatRequest, ChatResponse

record = LearningRecord(
    id="r1", topic="牛顿力学", user_understanding="基础", weak_points=["惯性概念"]
)
check("LearningRecord 创建", record.id == "r1" and len(record.weak_points) == 1)
check("LearningRecord 自动生成时间戳", bool(record.timestamp))

quiz = QuizQuestion(question="什么是力？", expected_concepts=["力", "加速度"], difficulty="easy")
check("QuizQuestion 创建", quiz.difficulty == "easy" and len(quiz.expected_concepts) == 2)

session = SessionState(topic="量子力学", phase="teaching")
check("SessionState 默认值", session.phase == "teaching" and session.understanding_level == "beginner")

req = ChatRequest(session_id=None, topic="化学", message="什么是原子？")
check("ChatRequest 创建", req.topic == "化学")

resp = ChatResponse(session_id="s1", phase="teaching", content="原子是...", weak_points=["电子排布"])
check("ChatResponse 创建", resp.phase == "teaching" and len(resp.weak_points) == 1)

# ── 3. Agent 提示词构建 ──
print("\n[TEST] 测试: Agent 提示词构建")
from agents.teacher import build_teacher_prompt
from agents.validator import build_validator_prompt
from agents.memory_agent import build_memory_analysis_prompt, build_review_reminder_prompt

teacher_prompt = build_teacher_prompt("牛顿力学", "惯性概念, 作用力与反作用力")
check("teacher prompt 含主题", "牛顿力学" in teacher_prompt)
check("teacher prompt 含薄弱点", "惯性概念" in teacher_prompt)
check("teacher prompt 含费曼指引", "费曼学习法" in teacher_prompt or "类比" in teacher_prompt)

teacher_empty = build_teacher_prompt("新主题", "")
check("teacher prompt 无历史薄弱点时使用默认文本", "第一次" in teacher_empty)

validator_prompt = build_validator_prompt("牛顿力学", "讲解了三大定律", "惯性, F=ma")
check("validator prompt 含主题", "牛顿力学" in validator_prompt)
check("validator prompt 含教学摘要", "三大定律" in validator_prompt)
check("validator prompt 含检验要点", "惯性" in validator_prompt)

memory_prompt = build_memory_analysis_prompt("化学", "用户: 什么是原子？\n助手: 原子是...")
check("memory prompt 含主题", "化学" in memory_prompt)
check("memory prompt 含对话", "什么是原子" in memory_prompt)
check("memory prompt 要求JSON格式", "JSON" in memory_prompt)

reminder_prompt = build_review_reminder_prompt("- 惯性概念\n- 电子排布", "2026-04-28")
check("reminder prompt 含薄弱记录", "惯性概念" in reminder_prompt)
check("reminder prompt 含时间", "2026-04-28" in reminder_prompt)

# ── 4. BaseAgent 类 ──
print("\n[TEST] 测试: BaseAgent")
from agents.base import BaseAgent
from utils.llm_client import get_client

with patch("agents.base.chat", return_value="Mocked LLM response") as mock_chat:
    agent = BaseAgent("You are a test agent.")
    check("BaseAgent 初始化（无对话）", len(agent.conversation) == 0)

    resp = agent._call_llm("Hello")
    check("BaseAgent._call_llm 返回模拟结果", resp == "Mocked LLM response")
    check("BaseAgent 记录对话", len(agent.conversation) == 2)
    check("BaseAgent conversation[0] user", agent.conversation[0]["role"] == "user")
    check("BaseAgent conversation[1] assistant", agent.conversation[1]["role"] == "assistant")

    agent.reset()
    check("BaseAgent.reset 清空对话", len(agent.conversation) == 0)

# ── 5. ChromaDB 向量存储 ──
print("\n[TEST] 测试: ChromaDB VectorStore")
from memory.vector_store import VectorStore

# 虚拟嵌入函数：不做 API 调用，返回随机向量
class FakeEmbeddingFn:
    def name(self):
        return "fake_embedding"
    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return [[0.1 * (i + j % 10) for j in range(384)] for i in range(len(input))]
    def embed_query(self, input):
        if isinstance(input, str):
            input = [input]
        return [[0.1 * (i + j % 10) for j in range(384)] for i in range(len(input))]

store = VectorStore(embedding_function=FakeEmbeddingFn())
check("VectorStore 初始化", store.collection is not None)
check("VectorStore 集合名称", store.collection.name == "learning_records")
check("VectorStore 初始为0条", store.count() == 0)

rid = store.add_record({
    "topic": "牛顿力学",
    "weak_points": ["惯性概念", "参考系"],
    "strengths": ["F=ma公式"],
    "summary": "用户基本理解三大定律，但惯性概念仍有混淆",
    "review_priority": ["惯性概念"],
    "understanding_level": "intermediate",
    "timestamp": "2026-04-29T10:00:00",
})
check("add_record 返回有效ID", bool(rid) and len(rid) > 0)
check("Store 变为1条", store.count() == 1)

# 搜索
results = store.search_similar("惯性", n_results=3)
check("search_similar 返回结果", len(results) >= 1)
check("搜索结果含ID", results[0]["id"] == rid)
check("搜索结果含metadata", "topic" in results[0]["metadata"])
check("搜索结果含distance", "distance" in results[0])

# 薄弱点检索
weak_points = store.get_weak_points_for_topic("牛顿力学")
check("get_weak_points_for_topic 返回惯性", "惯性概念" in weak_points)

weak_points_empty = store.get_weak_points_for_topic("不存在主题")
check("不存在主题返回列表（假嵌入可能匹配到已有记录）", isinstance(weak_points_empty, list))

# 全部薄弱点
all_weak = store.get_all_weak_points(5)
check("get_all_weak_points 返回列表", isinstance(all_weak, list))
check("get_all_weak_points 含牛顿力学", any(r["topic"] == "牛顿力学" for r in all_weak))

# 最近记录
recent = store.get_recent_records(5)
check("get_recent_records 返回1条", len(recent) == 1)

# 再添加一条
store.add_record({
    "topic": "量子力学",
    "weak_points": ["波函数坍缩"],
    "strengths": [],
    "summary": "波函数概念需要加强",
    "review_priority": ["波函数坍缩"],
    "understanding_level": "beginner",
})
check("Store 变为2条", store.count() == 2)
check("get_recent_records 返回2条", len(store.get_recent_records(5)) == 2)

# 默认离线兼容路径
print("\n[TEST] 测试: 离线兼容路径")
default_store = VectorStore()
check("默认VectorStore可初始化", default_store.collection is not None)

from utils.llm_client import chat as direct_chat
from memory.embeddings import MemorySystem

with patch("utils.llm_client.get_client", side_effect=RuntimeError("offline")):
    offline_reply = direct_chat([
        {"role": "system", "content": "你是一位精通费曼学习法的导师。"},
        {"role": "user", "content": "请解释原子"},
    ])
    check("LLM 无网络时返回本地兜底", bool(offline_reply))

    offline_ms = MemorySystem()
    offline_result = offline_ms.analyze_and_store("化学", "用户: 不太明白原子\n助手: 原子是物质的基本单位。")
    check("MemorySystem 离线可分析", bool(offline_result.get("summary")))

# ── 6. MemorySystem ──
print("\n[TEST] 测试: MemorySystem")

# 模拟 LLM 分析返回
mock_analysis = json.dumps({
    "weak_points": ["惯性概念"],
    "strengths": ["F=ma", "作用力反作用力"],
    "summary": "学习了牛顿三大定律",
    "review_priority": ["惯性概念"],
    "understanding_level": "intermediate",
})

with patch("memory.embeddings.chat", return_value=mock_analysis) as mock_mem_chat:
    ms = MemorySystem(embedding_function=FakeEmbeddingFn())

    # analyze_and_store
    conv = "用户: 什么是牛顿第一定律？\n助手: 牛顿第一定律也称为惯性定律..."
    result = ms.analyze_and_store("牛顿力学", conv)
    check("analyze_and_store 返回weak_points", "惯性概念" in result["weak_points"])
    check("analyze_and_store 返回strengths", "F=ma" in result["strengths"])
    check("analyze_and_store 返回summary", result["summary"] == "学习了牛顿三大定律")
    check("analyze_and_store 返回understanding_level", result["understanding_level"] == "intermediate")
    check("analyze_and_store 返回id", "id" in result)

    # get_context_for_topic
    ctx = ms.get_context_for_topic("牛顿力学")
    check("get_context_for_topic 含薄弱点", "薄弱知识点" in ctx)
    check("get_context_for_topic 含惯性概念", "惯性概念" in ctx)

    # generate_welcome_back
    mock_greeting = "欢迎回来！上次你学习了牛顿力学，惯性概念可以再复习一下哦~"
    with patch("memory.embeddings.chat", return_value=mock_greeting):
        welcome = ms.generate_welcome_back()
        check("generate_welcome_back 返回非空", bool(welcome))
        check("generate_welcome_back 含欢迎内容", "欢迎" in welcome)

    # search_history
    results = ms.search_history("惯性", n=3)
    check("search_history 返回列表", isinstance(results, list))
    check("search_history 结果非空", len(results) > 0)

# ── 7. 边界情况 ──
print("\n[TEST] 测试: 边界情况")

# JSON 解析失败时的容错
with patch("memory.embeddings.chat", return_value="Not valid JSON {{broken}}"):
    ms2 = MemorySystem(embedding_function=FakeEmbeddingFn())
    fallback_result = ms2.analyze_and_store("测试", "对话内容")
    check("JSON解析失败时默认weak_points为空列表", fallback_result["weak_points"] == [])
    check("JSON解析失败时summary为'分析失败'", fallback_result["summary"] == "分析失败")
    check("JSON解析失败时默认level为beginner", fallback_result["understanding_level"] == "beginner")

# markdown code block 去除
with patch("memory.embeddings.chat", return_value='```json\n{"weak_points":["w1"],"strengths":[],"summary":"s","review_priority":[],"understanding_level":"beginner"}\n```'):
    ms3 = MemorySystem(embedding_function=FakeEmbeddingFn())
    clean_result = ms3.analyze_and_store("测试", "对话")
    check("能解析```json包裹的JSON", clean_result["weak_points"] == ["w1"])

# SessionState 边界
default_session = SessionState(topic="", phase="teaching")
check("空主题SessionState可创建", default_session.topic == "")
check("SessionState history默认空", default_session.history == [])
check("SessionState weak_points默认空", default_session.weak_points == [])

# ChatRequest 空字段
empty_req = ChatRequest(topic="", message="")
check("空ChatRequest可创建", empty_req.topic == "" and empty_req.message == "")

# ── 8. 清理 ──
print("\n[CLEANUP] 清理临时 ChromaDB 数据...")
shutil.rmtree(tmpdir, ignore_errors=True)

# ── 结果 ──
total = passed + failed
print(f"\n{'='*50}")
print(f"测试结果: {passed}/{total} 通过", end="")
if failed > 0:
    print(f"，{failed} 个失败")
    sys.exit(1)
else:
    print(" [OK] 全部通过！")
    sys.exit(0)
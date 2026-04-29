from __future__ import annotations

import uuid
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from agents.teacher import build_teacher_prompt
from agents.validator import build_validator_prompt
from agents.base import BaseAgent
from memory.embeddings import MemorySystem
from models.schemas import SessionState

console = Console()


class ChemMindCLI:
    def __init__(self):
        self.memory = MemorySystem()
        self.session: SessionState | None = None
        self.teacher_agent: BaseAgent | None = None
        self.validator_agent: BaseAgent | None = None

    def run(self):
        self._show_welcome()
        while True:
            try:
                if self.session is None:
                    self._start_new_session()
                elif self.session.phase == "teaching":
                    self._teaching_phase()
                elif self.session.phase == "quizzing":
                    self._quizzing_phase()
                elif self.session.phase == "review":
                    self._review_phase()
                    self.session = None
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold yellow]再见！记得常回来复习哦！[/]")
                break

    def _show_welcome(self):
        console.print(Panel.fit(
            "[bold cyan]🧪 ChemMind Learn[/] —— 自我进化 AI 学习平台\n\n"
            "[dim]采用费曼学习法 | AI反向提问 | 长期记忆追踪[/]",
            border_style="cyan",
        ))
        greeting = self.memory.generate_welcome_back()
        if greeting:
            console.print(Panel(greeting, title="📮 学习提醒", border_style="green"))
            console.print("")

    def _start_new_session(self):
        topic = Prompt.ask("\n[bold]请输入你想学习的主题[/]")
        console.print(f"\n[dim]正在准备 {topic} 的学习资料...[/]\n")

        weak_context = self.memory.get_context_for_topic(topic)

        teacher_prompt = build_teacher_prompt(topic, weak_context)
        self.teacher_agent = BaseAgent(teacher_prompt)

        self.session = SessionState(topic=topic, phase="teaching")
        self.session.history.append({"role": "system", "content": f"开始学习: {topic}"})

    def _teaching_phase(self):
        user_input = Prompt.ask(
            "\n[bold green]💬 你的问题或输入[/] (输入 [yellow]/quiz[/] 进入测验, [yellow]/quit[/] 退出)"
        )

        if user_input.lower() == "/quit":
            self._end_session()
            return
        if user_input.lower() == "/quiz":
            self._start_quiz()
            return

        with console.status("[cyan]AI导师正在思考..."):
            response = self.teacher_agent._call_llm(user_input)

        self.session.history.append({"role": "user", "content": user_input})
        self.session.history.append({"role": "assistant", "content": response})

        console.print("")
        console.print(Panel(Markdown(response), title="👨‍🏫 费曼导师", border_style="blue"))

    def _start_quiz(self):
        self.session.phase = "quizzing"
        teaching_text = "\n".join(
            f"{h['role']}: {h['content']}" for h in self.session.history
        )
        validator_prompt = build_validator_prompt(
            self.session.topic, teaching_text, ""
        )
        self.validator_agent = BaseAgent(validator_prompt)

        console.print("\n[bold magenta]🎓 现在进入测验阶段！AI将扮演学生来提问检验你的理解。[/]\n")

        with console.status("[cyan]学生正在想问题..."):
            first_question = self.validator_agent._call_llm("请开始提问吧。")
        console.print(Panel(first_question, title="🤔 学生提问", border_style="magenta"))

    def _quizzing_phase(self):
        user_answer = Prompt.ask("\n[bold cyan]💡 你的回答[/] (输入 [yellow]/end[/] 结束测验)")

        if user_answer.lower() == "/end":
            self._end_session()
            return

        with console.status("[magenta]学生在思考你的回答..."):
            follow_up = self.validator_agent._call_llm(
                f"我的回答是：{user_answer}\n\n请根据我的回答：如果回答有漏洞就追问引导我发现，如果回答正确就换一个角度提问或确认理解。"
            )

        self.session.history.append({"role": "user", "content": f"[测验回答] {user_answer}"})
        self.session.history.append({"role": "assistant", "content": f"[测验追问] {follow_up}"})

        console.print("")
        console.print(Panel(follow_up, title="🤔 学生追问", border_style="magenta"))

    def _end_session(self):
        self.session.phase = "review"
        self._review_phase()
        self.session = None

    def _review_phase(self):
        console.print("\n[bold yellow]📊 正在生成本次学习报告...[/]\n")

        conversation_text = "\n".join(
            f"{h['role']}: {h['content']}" for h in self.session.history
        )
        analysis = self.memory.analyze_and_store(self.session.topic, conversation_text)

        weak_text = "\n".join(f"  • {w}" for w in analysis.get("weak_points", []))
        strength_text = "\n".join(f"  • {s}" for s in analysis.get("strengths", []))

        report = f"""
## 📋 学习报告

**主题**: {self.session.topic}
**理解水平**: {analysis.get('understanding_level', 'N/A')}

### ✅ 已掌握
{strength_text or '  (暂无记录)'}

### ⚠️ 薄弱点
{weak_text or '  (暂无记录)'}

### 📝 学习摘要
{analysis.get('summary', 'N/A')}

---
💾 已存入长期记忆，下次学习时会自动提醒复习。
"""
        console.print(Panel(Markdown(report), border_style="yellow"))


def main():
    cli = ChemMindCLI()
    cli.run()


if __name__ == "__main__":
    main()
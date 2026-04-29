from __future__ import annotations

import uuid
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agents.teacher import build_teacher_prompt
from agents.validator import build_validator_prompt
from agents.base import BaseAgent
from memory.embeddings import MemorySystem
from models.schemas import SessionState

app = FastAPI(title="ChemMind Learn API", version="1.0.0")

memory = MemorySystem()
sessions: dict[str, SessionState] = {}
teacher_agents: dict[str, BaseAgent] = {}
validator_agents: dict[str, BaseAgent] = {}


class ChatIn(BaseModel):
    session_id: str = ""
    topic: str = ""
    message: str = ""


class ChatOut(BaseModel):
    session_id: str
    phase: str
    content: str
    weak_points: list[str] = Field(default_factory=list)


@app.get("/")
def root():
    return HTMLResponse(HTML_PAGE)


@app.get("/api/welcome")
def welcome():
    greeting = memory.generate_welcome_back()
    return {"greeting": greeting}


@app.post("/api/chat")
def chat_api(chat_in: ChatIn):
    sid = chat_in.session_id
    if not sid or sid not in sessions:
        sid = str(uuid.uuid4())
        topic = chat_in.topic or chat_in.message
        weak_context = memory.get_context_for_topic(topic)
        teacher_prompt = build_teacher_prompt(topic, weak_context)
        teacher_agents[sid] = BaseAgent(teacher_prompt)
        sessions[sid] = SessionState(topic=topic, phase="teaching")
        sessions[sid].history.append({"role": "system", "content": f"开始学习: {topic}"})

    session = sessions[sid]
    response_content = ""

    if session.phase == "teaching":
        if chat_in.message.lower() == "/quiz":
            session.phase = "quizzing"
            teaching_text = "\n".join(
                f"{h['role']}: {h['content']}" for h in session.history
            )
            validator_prompt = build_validator_prompt(
                session.topic, teaching_text, ""
            )
            validator_agents[sid] = BaseAgent(validator_prompt)
            response_content = validator_agents[sid]._call_llm("请开始提问吧。")
            session.history.append({"role": "assistant", "content": f"[测验] {response_content}"})
        elif chat_in.message.lower() == "/end":
            return _end_session(sid)
        else:
            response_content = teacher_agents[sid]._call_llm(chat_in.message)
            session.history.append({"role": "user", "content": chat_in.message})
            session.history.append({"role": "assistant", "content": response_content})

    elif session.phase == "quizzing":
        if chat_in.message.lower() == "/end":
            return _end_session(sid)
        agent = validator_agents[sid]
        response_content = agent._call_llm(
            f"我的回答是：{chat_in.message}\n\n请根据我的回答："
            "如果回答有漏洞就追问引导我发现，如果回答正确就换一个角度提问或确认理解。"
        )
        session.history.append({"role": "user", "content": f"[测验回答] {chat_in.message}"})
        session.history.append({"role": "assistant", "content": f"[测验追问] {response_content}"})

    return ChatOut(
        session_id=sid,
        phase=session.phase,
        content=response_content,
    )


@app.post("/api/end")
def end_session(sid: str = Query(...)):
    return _end_session(sid)


def _end_session(sid: str) -> ChatOut:
    if sid not in sessions:
        raise HTTPException(404, "Session not found")
    session = sessions[sid]

    conversation_text = "\n".join(
        f"{h['role']}: {h['content']}" for h in session.history
    )
    analysis = memory.analyze_and_store(session.topic, conversation_text)

    report_lines = [
        f"## 学习报告: {session.topic}",
        f"**理解水平**: {analysis.get('understanding_level', 'N/A')}",
        "",
        "### ✅ 已掌握",
        *[f"- {s}" for s in analysis.get("strengths", [])],
        "",
        "### ⚠️ 薄弱点",
        *[f"- {w}" for w in analysis.get("weak_points", [])],
        "",
        f"### 📝 摘要: {analysis.get('summary', '')}",
    ]
    content = "\n".join(report_lines)

    result = ChatOut(
        session_id=sid,
        phase="review",
        content=content,
        weak_points=analysis.get("weak_points", []),
    )

    sessions.pop(sid, None)
    teacher_agents.pop(sid, None)
    validator_agents.pop(sid, None)
    return result


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChemMind Learn</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#0c0e14 0%,#1a1e2e 50%,#0f1119 100%);color:#e0e0e0;min-height:100vh;display:flex;flex-direction:column;}
header{background:rgba(20,22,30,0.95);padding:16px 24px;border-bottom:1px solid #2a2d3a;display:flex;align-items:center;gap:12px;backdrop-filter:blur(10px);}
header h1{font-size:1.4em;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
header span.tag{font-size:0.75em;background:#2a2d3a;padding:4px 10px;border-radius:12px;color:#9ca3af;}
#greeting{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.25);margin:16px 24px;padding:14px 18px;border-radius:12px;color:#4ade80;font-size:0.95em;display:none;}
main{flex:1;max-width:900px;width:100%;margin:0 auto;padding:8px 24px 24px;display:flex;flex-direction:column;}
#chatbox{flex:1;background:rgba(20,22,30,0.7);border:1px solid #2a2d3a;border-radius:16px;padding:20px;overflow-y:auto;margin-bottom:16px;min-height:400px;max-height:60vh;}
.msg{margin-bottom:18px;animation:fadeIn .3s;}
.msg.teacher .bubble{background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.3);border-radius:4px 16px 16px 16px;padding:12px 16px;}
.msg.student .bubble{background:rgba(168,85,247,0.12);border:1px solid rgba(168,85,247,0.3);border-radius:16px 4px 16px 16px;padding:12px 16px;}
.msg.user .bubble{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.25);border-radius:16px 16px 4px 16px;padding:12px 16px;}
.msg .label{font-size:0.75em;margin-bottom:4px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;}
.bubble h2,.bubble h3{color:#93c5fd;margin:6px 0;}
.bubble ul,.bubble ol{padding-left:20px;margin:6px 0;}
.bubble li{margin:3px 0;}
.bubble code{background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;font-size:0.9em;}
.bubble p{margin:4px 0;line-height:1.6;}
.report{border:2px solid #eab308 !important;background:rgba(234,179,8,0.08) !important;}
#input-area{display:flex;gap:10px;}
#topic{background:#1a1e2e;border:1px solid #2a2d3a;color:#e0e0e0;padding:12px 16px;border-radius:10px;font-size:1em;width:200px;outline:none;}
#topic:focus{border-color:#60a5fa;}
#input{flex:1;background:#1a1e2e;border:1px solid #2a2d3a;color:#e0e0e0;padding:12px 16px;border-radius:10px;font-size:1em;outline:none;resize:none;}
#input:focus{border-color:#60a5fa;}
button{background:linear-gradient(135deg,#3b82f6,#8b5cf6);border:none;color:white;padding:12px 20px;border-radius:10px;cursor:pointer;font-size:0.95em;transition:opacity 0.2s;white-space:nowrap;}
button:hover{opacity:0.85;}
button.secondary{background:#2a2d3a;}
.helper{font-size:0.78em;color:#6b7280;padding:6px 0;}
.helper code{color:#a78bfa;background:rgba(167,139,250,0.1);padding:2px 6px;border-radius:4px;}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}
</style>
</head>
<body>
<header>
<h1>🧪 ChemMind Learn</h1>
<span class="tag">费曼学习法</span>
<span class="tag">AI 反向提问</span>
<span class="tag">长期记忆</span>
</header>
<div id="greeting"></div>
<main>
<div id="chatbox"><div style="color:#6b7280;text-align:center;padding-top:60px;">👋 在上方输入学习主题开始吧</div></div>
<div class="helper">命令: <code>/quiz</code> 进入测验 <code>/end</code> 结束学习 <code>/new</code> 开启新主题</div>
<div id="input-area">
<input id="topic" placeholder="学习主题...">
<textarea id="input" rows="1" placeholder="输入你的问题或回复..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
<button onclick="send()">发送</button>
<button class="secondary" onclick="endSession()">结束</button>
</div>
</main>
<script>
let sessionId='',phase='';
function escapeHtml(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function simpleMd(t){
  t=escapeHtml(t);
  t=t.replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>');
  t=t.replace(/^- (.+)$/gm,'<li>$1</li>').replace(/(<li>.*<\/li>)/s,function(m){return '<ul>'+m+'</ul>';});
  t=t.replace(/^(\d+)\. (.+)$/gm,'<li>$2</li>');
  t=t.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
  t=t.replace(/\*(.+?)\*/g,'<i>$1</i>');
  t=t.replace(/`(.+?)`/g,'<code>$1</code>');
  t=t.replace(/✅/g,'<span style="color:#4ade80">✅</span>');
  t=t.replace(/⚠️/g,'<span style="color:#fbbf24">⚠️</span>');
  return t.replace(/\n/g,'<br>');
}
function addMsg(role,label,text,extraClass=''){
  var d=document.createElement('div');d.className='msg '+role+(extraClass?' '+extraClass:'');
  var html='<div class="label">'+label+'</div><div class="bubble">'+simpleMd(text)+'</div>';
  d.innerHTML=html;document.getElementById('chatbox').appendChild(d);
  var box=document.getElementById('chatbox');box.scrollTop=box.scrollHeight;
}
function send(){
  var topic=document.getElementById('topic').value.trim();
  var msg=document.getElementById('input').value.trim();
  if(!msg)return;
  if(!sessionId&&!topic){alert('请先输入学习主题');return;}
  if(msg==='/quiz'&&phase==='quizzing'){addMsg('system','系统','已在测验阶段');return;}
  if(msg==='/new'){sessionId='';phase='';document.getElementById('chatbox').innerHTML='';document.getElementById('greeting').style.display='none';document.getElementById('input').value='';return;}
  addMsg('user','你',msg);
  document.getElementById('input').value='';
  fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,topic:topic,message:msg})})
  .then(r=>r.json()).then(d=>{
    sessionId=d.session_id;phase=d.phase;
    if(phase==='teaching')addMsg('teacher','费曼导师',d.content);
    else if(phase==='quizzing')addMsg('student','AI学生提问',d.content);
    else if(phase==='review')addMsg('teacher','学习报告',d.content,'report');
  });
}
function endSession(){
  if(!sessionId)return;
  fetch('/api/end?sid='+sessionId,{method:'POST'}).then(r=>r.json()).then(d=>{
    addMsg('teacher','学习报告',d.content,'report');
    sessionId='';phase='';
  });
}
fetch('/api/welcome').then(r=>r.json()).then(d=>{
  if(d.greeting){var g=document.getElementById('greeting');g.textContent='📮 '+d.greeting;g.style.display='block';}
});
</script>
</body>
</html>"""


def main():
    import uvicorn
    from config import config
    uvicorn.run(app, host="0.0.0.0", port=config.WEB_PORT)


if __name__ == "__main__":
    main()
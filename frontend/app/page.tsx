"use client";
import {FormEvent,useEffect,useRef,useState} from "react";
import {Bot,Cpu,Plus,Send,Settings2,Sparkles,Wifi,WifiOff} from "lucide-react";
type Message={role:"user"|"assistant";content:string};
type Model={name:string;size:number};
export default function Home(){
 const [messages,setMessages]=useState<Message[]>([]),[input,setInput]=useState("");
 const [models,setModels]=useState<Model[]>([]),[model,setModel]=useState("qwen2.5:3b");
 const [busy,setBusy]=useState(false),[connected,setConnected]=useState(false);
 const bottom=useRef<HTMLDivElement>(null);
 async function refresh(){try{const r=await fetch("/api/models");if(!r.ok)throw Error();const d=await r.json();setModels(d.models||[]);setModel(v=>v||d.default);setConnected(true);}catch{setConnected(false);setModels([]);}}
 useEffect(()=>{refresh();},[]);useEffect(()=>{bottom.current?.scrollIntoView({behavior:"smooth"});},[messages]);
 async function send(e:FormEvent){e.preventDefault();const prompt=input.trim();if(!prompt||busy)return;
  const prior=[...messages,{role:"user" as const,content:prompt}];setMessages([...prior,{role:"assistant",content:""}]);setInput("");setBusy(true);
  try{const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model,messages:prior,temperature:0.7})});
   if(!r.ok||!r.body)throw Error("AI backend request failed");const reader=r.body.getReader(),decoder=new TextDecoder();let buffer="",answer="";
   while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});const parts=buffer.split("\n\n");buffer=parts.pop()||"";
    for(const part of parts){const line=part.split("\n").find(v=>v.startsWith("data: "));if(!line)continue;const d=JSON.parse(line.slice(6));if(d.error)throw Error(d.error);if(d.token){answer+=d.token;setMessages([...prior,{role:"assistant",content:answer}]);}}
   }
  }catch(err){setMessages([...prior,{role:"assistant",content:"Connection error: "+(err instanceof Error?err.message:"Unknown error")}]);refresh();}
  finally{setBusy(false);}
 }
 return <main className="shell"><aside className="sidebar"><div className="brand"><span className="brand-icon"><Sparkles size={19}/></span>Universe<span className="accent">AI</span></div>
 <button className="new" onClick={()=>setMessages([])}><Plus size={16}/> New chat</button><div className="section-label">WORKSPACE</div>
 <div className="nav active"><Bot size={17}/> AI Chat</div><div className="nav muted"><Cpu size={17}/> Model library <small>SOON</small></div><div className="nav muted"><Settings2 size={17}/> Settings <small>SOON</small></div>
 <div className="side-bottom"><div className="connection"><i className={connected?"dot online":"dot"}/>{connected?"Ollama connected":"Ollama disconnected"}</div><small>UNIVERSEAI · PREVIEW 0.1.0</small></div></aside>
 <section className="main"><header className="topbar"><b>AI Chat <small>PREVIEW</small></b><div className="status">{connected?<Wifi size={14}/>:<WifiOff size={14}/>} {connected?"Local engine online":"Engine offline"}</div></header>
 <div className="chat">{messages.length===0?<div className="welcome"><div className="hero-icon"><Sparkles size={25}/></div><div className="eyebrow">YOUR OPEN-SOURCE AI WORKSPACE</div>
 <h1>What can I help<br/><span>you build today?</span></h1><p>Chat with your own AI model. Your prompts stay on the machine running Ollama.</p>
 <div className="suggestions">{["Explain how AI models work","Help me write a Python script","Plan a website project","Summarize a technical concept"].map(s=><button key={s} onClick={()=>setInput(s)}>{s}<span>↗</span></button>)}</div></div>
 :<div className="messages">{messages.map((m,i)=><article className="message" key={i}><div className="avatar">{m.role==="assistant"?<Sparkles size={15}/>:"Y"}</div><div className="body"><b>{m.role==="assistant"?"UniverseAI":"You"}</b><p>{m.content||(busy&&i===messages.length-1?"Thinking…":"")}</p></div></article>)}<div ref={bottom}/></div>}</div>
 <div className="composer-wrap"><form className="composer" onSubmit={send}><textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();(e.currentTarget.form as HTMLFormElement)?.requestSubmit();}}} placeholder="Message UniverseAI…" rows={1}/>
 <div className="composer-bottom"><label><Cpu size={14}/><select value={model} onChange={e=>setModel(e.target.value)}>{models.length===0&&<option value={model}>{model} · not detected</option>}{models.map(m=><option key={m.name} value={m.name}>{m.name}</option>)}</select></label>
 <button className="send" disabled={busy||!input.trim()} aria-label="Send">{busy?"…":<Send size={16}/>}</button></div></form><p className="footnote">AI can make mistakes. Check important information. Your model runs locally through Ollama.</p></div>
 </section></main>;
}

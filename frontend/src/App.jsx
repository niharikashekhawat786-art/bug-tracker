import React, { useEffect, useMemo, useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { DndContext, useDraggable, useDroppable } from '@dnd-kit/core';
import { Bug, CheckCircle2, Circle, ClipboardList, LogOut, Plus, Search, KanbanSquare } from 'lucide-react';
import api from './api';

const statuses = ['backlog', 'todo', 'in_progress', 'review', 'done'];
const label = s => ({ in_progress: 'In progress', todo: 'To do' }[s] || s.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase()));

function Login({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  async function submit(e) {
    e.preventDefault(); setError('');
    try {
      if (mode === 'register') await api.post('/api/auth/register', { name, email, password });
      const body = new URLSearchParams({ username: email, password });
      const { data } = await api.post('/api/auth/login', body, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
      localStorage.setItem('token', data.access_token);
      onLogin();
    } catch (err) { setError(err.response?.data?.detail || 'Unable to sign in'); }
  }
  return <div className="auth-shell"><form className="auth-card" onSubmit={submit}>
    <div className="brand"><Bug /> IssueDesk</div><h1>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
    <p className="muted">Manage projects, bugs and team work in one place.</p>
    {mode === 'register' && <input required placeholder="Full name" value={name} onChange={e=>setName(e.target.value)} />}
    <input required type="email" placeholder="Email address" value={email} onChange={e=>setEmail(e.target.value)} />
    <input required minLength="8" type="password" placeholder="Password (8+ characters)" value={password} onChange={e=>setPassword(e.target.value)} />
    {error && <p className="error">{error}</p>}
    <button className="primary full">{mode === 'login' ? 'Sign in' : 'Create account'}</button>
    <button type="button" className="link-btn" onClick={()=>setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'New here? Create an account' : 'Already registered? Sign in'}</button>
  </form></div>;
}

function DraggableIssue({ issue, onClick }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: String(issue.id) });
  const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` } : undefined;
  return <article ref={setNodeRef} style={style} className={`issue-card ${isDragging ? 'dragging' : ''}`} {...listeners} {...attributes} onClick={()=>onClick(issue)}>
    <div className="issue-top"><span className="issue-key">ISSUE-{issue.id}</span><span className={`priority ${issue.priority}`}>{issue.priority}</span></div>
    <strong>{issue.title}</strong><div className="issue-bottom"><span>{issue.issue_type}</span><span>{issue.assignee_id ? `User #${issue.assignee_id}` : 'Unassigned'}</span></div>
  </article>;
}
function Column({ status, issues, onIssue }) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  return <div ref={setNodeRef} className={`kanban-column ${isOver ? 'over' : ''}`}><div className="column-heading"><span>{label(status)}</span><span className="count">{issues.length}</span></div>
    {issues.map(issue=><DraggableIssue key={issue.id} issue={issue} onClick={onIssue} />)}
    {!issues.length && <div className="empty-column">Drop an issue here</div>}
  </div>;
}

function IssueModal({ issue, projectId, onClose, onSaved }) {
  const [form, setForm] = useState(issue || { title:'', description:'', issue_type:'bug', priority:'medium', status:'backlog', project_id:projectId });
  const [comment, setComment] = useState('');
  const [comments, setComments] = useState([]);
  const [error, setError] = useState('');
  useEffect(()=>{ if(issue) api.get(`/api/issues/${issue.id}/comments`).then(r=>setComments(r.data)).catch(()=>{}); },[issue]);
  const change = e => setForm({...form, [e.target.name]:e.target.value});
  async function save(e) {
    e.preventDefault(); setError('');
    try {
      if (issue) await api.patch(`/api/issues/${issue.id}`, form);
      else await api.post('/api/issues', {...form, project_id: projectId});
      onSaved();
    } catch(err) { setError(err.response?.data?.detail || 'Could not save issue'); }
  }
  async function addComment(e) { e.preventDefault(); await api.post(`/api/issues/${issue.id}/comments`, {body:comment}); setComment(''); const r=await api.get(`/api/issues/${issue.id}/comments`); setComments(r.data); }
  return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal" onMouseDown={e=>e.stopPropagation()}>
    <div className="modal-head"><h2>{issue ? `Issue #${issue.id}` : 'Create issue'}</h2><button className="icon-btn" onClick={onClose}>×</button></div>
    <form onSubmit={save} className="form-grid">
      <label className="wide">Title<input name="title" required minLength="3" value={form.title} onChange={change}/></label>
      <label className="wide">Description<textarea name="description" rows="3" value={form.description || ''} onChange={change}/></label>
      <label>Type<select name="issue_type" value={form.issue_type} onChange={change}><option value="bug">Bug</option><option value="task">Task</option><option value="feature">Feature</option></select></label>
      <label>Priority<select name="priority" value={form.priority} onChange={change}><option>low</option><option>medium</option><option>high</option><option>critical</option></select></label>
      <label>Status<select name="status" value={form.status} onChange={change}>{statuses.map(s=><option key={s} value={s}>{label(s)}</option>)}</select></label>
      {error && <p className="error wide">{error}</p>}
      <div className="wide"><button className="primary">{issue ? 'Save changes' : 'Create issue'}</button></div>
    </form>
    {issue && <section className="comments"><h3>Comments</h3>{comments.map(c=><div className="comment" key={c.id}>{c.body}<small> · User #{c.author_id}</small></div>)}<form onSubmit={addComment} className="comment-form"><input placeholder="Write a comment..." value={comment} onChange={e=>setComment(e.target.value)} required/><button className="primary">Send</button></form></section>}
  </div></div>;
}

function Dashboard({ user, onLogout }) {
  const [projects,setProjects]=useState([]), [projectId,setProjectId]=useState('');
  const [issues,setIssues]=useState([]), [query,setQuery]=useState('');
  const [modal,setModal]=useState(null), [newProject,setNewProject]=useState(false), [projectForm,setProjectForm]=useState({name:'',key:'',description:''});
  const [view,setView]=useState('board'), [error,setError]=useState('');
  const loadProjects = async()=>{ try { const r=await api.get('/api/projects'); setProjects(r.data); if(!projectId && r.data.length) setProjectId(String(r.data[0].id)); } catch(e){setError('Unable to load projects');} };
  const loadIssues = async()=>{ if(!projectId) return; try { const r=await api.get('/api/issues',{params:{project_id:projectId,q:query||undefined}}); setIssues(r.data); } catch(e){setError(e.response?.data?.detail || 'Unable to load issues');} };
  useEffect(()=>{loadProjects();},[]);
  useEffect(()=>{loadIssues();},[projectId,query]);
  async function createProject(e){e.preventDefault();try{const r=await api.post('/api/projects',projectForm);setNewProject(false);setProjectForm({name:'',key:'',description:''});await loadProjects();setProjectId(String(r.data.id));}catch(e){setError(e.response?.data?.detail||'Could not create project');}}
  async function moveIssue(event){const {active,over}=event;if(!over)return;const id=Number(active.id), status=String(over.id);if(!statuses.includes(status))return;const old=issues.find(i=>i.id===id);if(!old||old.status===status)return;setIssues(prev=>prev.map(i=>i.id===id?{...i,status}:i));try{await api.patch(`/api/issues/${id}`,{status});}catch(e){loadIssues();setError(e.response?.data?.detail||'Status update failed');}}
  const selected=projects.find(p=>String(p.id)===String(projectId));
  const counts=useMemo(()=>({total:issues.length,open:issues.filter(i=>i.status!=='done').length,done:issues.filter(i=>i.status==='done').length,bugs:issues.filter(i=>i.issue_type==='bug').length}),[issues]);
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><Bug/> IssueDesk</div><div className="side-label">WORKSPACE</div><button className="nav-item active"><KanbanSquare/> Board</button><button className="nav-item" onClick={()=>setView('list')}><ClipboardList/> All issues</button><div className="side-label projects-label">PROJECTS <button onClick={()=>setNewProject(true)}>＋</button></div>
      {projects.map(p=><button key={p.id} className={`project-link ${String(p.id)===String(projectId)?'chosen':''}`} onClick={()=>setProjectId(String(p.id))}><span className="project-dot">{p.key.slice(0,1)}</span>{p.name}</button>)}
      <div className="sidebar-user"><div className="avatar">{user.name?.[0]?.toUpperCase()}</div><div><b>{user.name}</b><small>{user.email}</small></div><button title="Sign out" onClick={onLogout}><LogOut size={17}/></button></div>
    </aside>
    <main className="main"><header className="topbar"><div><span className="crumb">Workspace / Projects / </span><b>{selected?.name || 'Select a project'}</b></div><div className="top-actions"><div className="search"><Search size={16}/><input placeholder="Search issues..." value={query} onChange={e=>setQuery(e.target.value)}/></div><button className="primary" disabled={!projectId} onClick={()=>setModal({})}><Plus size={16}/> Create issue</button></div></header>
      <div className="content"><div className="page-title"><div><h1>{selected?.name || 'Your workspace'}</h1><p className="muted">{selected?.description || 'Track work and keep your team aligned.'}</p></div><div className="view-switch"><button className={view==='board'?'selected':''} onClick={()=>setView('board')}>Board</button><button className={view==='list'?'selected':''} onClick={()=>setView('list')}>List</button></div></div>
        {error && <p className="error">{error}</p>}
        <div className="stats"><div className="stat"><span>Total issues</span><b>{counts.total}</b><ClipboardList/></div><div className="stat"><span>Open</span><b>{counts.open}</b><Circle/></div><div className="stat"><span>Completed</span><b>{counts.done}</b><CheckCircle2/></div><div className="stat"><span>Bugs</span><b>{counts.bugs}</b><Bug/></div></div>
        {!projects.length ? <div className="welcome"><h2>Start your first project</h2><p>Create a project to start tracking bugs, tasks and features.</p><button className="primary" onClick={()=>setNewProject(true)}>Create project</button></div> :
        view==='board' ? <DndContext onDragEnd={moveIssue}><div className="kanban">{statuses.map(s=><Column key={s} status={s} issues={issues.filter(i=>i.status===s)} onIssue={setModal}/>)}</div></DndContext> :
        <div className="table-wrap"><table><thead><tr><th>Issue</th><th>Type</th><th>Status</th><th>Priority</th><th>Assignee</th></tr></thead><tbody>{issues.map(i=><tr key={i.id} onClick={()=>setModal(i)}><td><b>ISSUE-{i.id}</b> {i.title}</td><td>{i.issue_type}</td><td>{label(i.status)}</td><td><span className={`priority ${i.priority}`}>{i.priority}</span></td><td>{i.assignee_id||'Unassigned'}</td></tr>)}</tbody></table></div>}
      </div>
    </main>
    {modal && <IssueModal issue={modal.id?modal:null} projectId={Number(projectId)} onClose={()=>setModal(null)} onSaved={()=>{setModal(null);loadIssues();}}/>}
    {newProject && <div className="modal-backdrop" onMouseDown={()=>setNewProject(false)}><form className="modal small-modal" onSubmit={createProject} onMouseDown={e=>e.stopPropagation()}><div className="modal-head"><h2>New project</h2><button type="button" className="icon-btn" onClick={()=>setNewProject(false)}>×</button></div><label>Project name<input required value={projectForm.name} onChange={e=>setProjectForm({...projectForm,name:e.target.value})}/></label><label>Project key<input required maxLength="12" placeholder="e.g. WEB" value={projectForm.key} onChange={e=>setProjectForm({...projectForm,key:e.target.value.toUpperCase()})}/></label><label>Description<textarea value={projectForm.description} onChange={e=>setProjectForm({...projectForm,description:e.target.value})}/></label><button className="primary">Create project</button></form></div>}
  </div>;
}

export default function App(){
  const [user,setUser]=useState(null),[checking,setChecking]=useState(true);
  const loadUser=async()=>{try{const r=await api.get('/api/auth/me');setUser(r.data);}catch{localStorage.removeItem('token');setUser(null);}finally{setChecking(false);}};
  useEffect(()=>{if(localStorage.getItem('token'))loadUser();else setChecking(false);},[]);
  if(checking)return <div className="loading">Loading IssueDesk…</div>;
  return user?<Dashboard user={user} onLogout={()=>{localStorage.removeItem('token');setUser(null);}}/>:<Login onLogin={loadUser}/>;
}

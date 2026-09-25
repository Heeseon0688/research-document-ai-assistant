import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, CircleHelp,
  FileText, FlaskConical, Layers3, LoaderCircle, MessageSquare, Plus, Search,
  Send, ShieldCheck, Sparkles, UploadCloud, X } from 'lucide-react';
import { askQuestion, getDocuments, getHealth, uploadDocuments } from './api';

const suggestions = [
  { label: '발효 공정', question: '발효 공정 보고서에서 가장 높은 생산량을 기록한 배치는 무엇인가요?', icon: FlaskConical },
  { label: '단백질 발현', question: '단백질 발현 보고서에서 P-02의 수율과 순도는 얼마인가요?', icon: Layers3 },
  { label: '제조 품질', question: '제조 품질 보고서에서 Q-03이 보류된 이유는 무엇인가요?', icon: ShieldCheck },
];

function Sources({ sources }) {
  return <div className="sources">
    <div className="sources-heading"><BookOpen size={14} /> Sources <span>{sources.length}</span></div>
    <div className="source-grid">{sources.map((source, i) => <details className="source" key={`${source.chunk_id}-${i}`}>
      <summary><span className="source-number">{i + 1}</span><span className="source-name">{source.file_name}<small>페이지 {source.page} · 원문 확인</small></span><ChevronDown size={15} /></summary>
      <blockquote>{source.quote}</blockquote>
      <p className="source-excerpt">{source.excerpt}</p>
    </details>)}</div>
  </div>;
}

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [help, setHelp] = useState(false);
  const [filter, setFilter] = useState('');
  const fileInput = useRef(null);
  const questionInput = useRef(null);
  const bottom = useRef(null);
  const busyUpload = useRef(false);
  const busyAsk = useRef(false);

  async function refresh() {
    setLoading(true);
    try {
      const [status, docs] = await Promise.all([getHealth(), getDocuments()]);
      setHealth(status); setDocuments(docs); setError('');
    } catch (err) { setHealth(null); setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, []);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages, asking]);

  async function upload(fileList) {
    if (busyUpload.current) return;
    const files = Array.from(fileList || []);
    if (!files.length) return;
    if (files.some(file => !file.name.toLowerCase().endsWith('.pdf'))) {
      setError('PDF 파일을 선택해주세요.'); return;
    }
    busyUpload.current = true; setUploading(true); setError(''); setUploadResults([]);
    try {
      const results = await uploadDocuments(files);
      setUploadResults(results);
      setDocuments(await getDocuments());
    } catch (err) { setError(err.message); }
    finally { busyUpload.current = false; setUploading(false); if (fileInput.current) fileInput.current.value = ''; }
  }

  async function submit(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busyAsk.current || !documents.length || uploading) return;
    busyAsk.current = true; setAsking(true); setError(''); setQuestion('');
    setMessages(previous => [...previous, { role: 'user', text }]);
    try {
      const result = await askQuestion(text, topK);
      setMessages(previous => [...previous, { role: 'assistant', ...result }]);
    } catch (err) {
      setMessages(previous => [...previous, { role: 'error', text: err.message }]);
      setQuestion(text);
    } finally { busyAsk.current = false; setAsking(false); }
  }

  const filteredDocuments = documents.filter(doc => doc.file_name.toLowerCase().includes(filter.toLowerCase()));
  const totalPages = documents.reduce((sum, doc) => sum + doc.page_count, 0);

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="./"><span className="brand-mark"><Layers3 size={24} /></span><span>Research<span className="brand-sub">RAG ASSISTANT</span></span></a>
      <div className="workspace-label">WORKSPACE <span>01</span></div>
      <div className="nav-current"><MessageSquare size={17} /> 연구 어시스턴트 <span className="nav-dot" /></div>
      <div className="library-heading"><span>문서 라이브러리 <b>{documents.length}</b></span><button className="icon-button" aria-label="PDF 추가" onClick={() => fileInput.current?.click()} disabled={uploading}><Plus size={17} /></button></div>
      <input ref={fileInput} type="file" accept=".pdf,application/pdf" multiple hidden onChange={event => upload(event.target.files)} />
      <button className={`upload-zone ${dragging ? 'dragging' : ''}`} disabled={uploading}
        onClick={() => fileInput.current?.click()}
        onDragOver={event => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={event => { event.preventDefault(); setDragging(false); upload(event.dataTransfer.files); }}>
        <span className="upload-icon">{uploading ? <LoaderCircle className="spin" size={22} /> : <UploadCloud size={23} />}</span>
        <strong>{uploading ? '문서를 분석하고 있어요' : '연구 PDF 업로드'}</strong>
        <span>{uploading ? '최초 실행 시 모델 다운로드로 시간이 걸릴 수 있어요' : '파일을 끌어 놓거나 클릭해 선택하세요'}</span>
        <small>{uploading ? '텍스트 추출 → 분할 → 검색 인덱스 생성' : '여러 PDF를 한 번에 추가할 수 있어요'}</small>
      </button>
      {uploadResults.length > 0 && <div className="upload-results" aria-live="polite">{uploadResults.map((result, i) =>
        <div className={result.status === 'error' ? 'upload-error' : ''} key={i}>
          {result.status === 'error' ? <X size={13} /> : <Check size={13} />}<span>{result.file_name}<small>{result.error || (result.status === 'duplicate' ? '이미 등록된 문서입니다' : '검색 준비 완료')}</small></span>
        </div>)}</div>}
      {documents.length > 0 && <label className="document-search"><Search size={14} /><input aria-label="문서 이름 검색" placeholder="문서 이름 검색" value={filter} onChange={event => setFilter(event.target.value)} /></label>}
      <div className="document-list">
        {loading ? <p className="library-empty">라이브러리를 불러오는 중…</p> : filteredDocuments.map(doc => <div className="document-item" key={doc.document_id} title={doc.file_name}>
          <span className="pdf-icon"><FileText size={18} /><small>PDF</small></span><span className="document-name">{doc.file_name}<small>{doc.page_count} pages <span>·</span> {doc.chunk_count} chunks</small></span><Check className="doc-check" size={14} />
        </div>)}
        {!loading && !documents.length && <div className="library-empty"><FileText size={25} /><p>아직 등록된 문서가 없어요</p><small>첫 PDF를 업로드해 연구를 시작하세요.</small></div>}
        {documents.length > 0 && !filteredDocuments.length && <p className="library-empty">일치하는 문서가 없습니다.</p>}
      </div>
      <div className="sidebar-bottom"><div className="private-note"><ShieldCheck size={17} /><div>문서에 근거한 답변<small>파일명과 페이지로 출처를 확인하세요</small></div></div><button className="help-button" onClick={() => setHelp(true)}><CircleHelp size={17} /> 사용 가이드 <ArrowUpRight size={14} /></button></div>
    </aside>

    <main>
      <header className="topbar"><div><span className="breadcrumb">Workspace</span><span className="slash">/</span><strong>연구 어시스턴트</strong></div><div className="connection"><span className={health ? 'status-dot online' : 'status-dot'} />{loading ? '연결 중' : health ? 'API 연결됨' : 'API 연결 안 됨'}{!health && !loading && <button onClick={refresh}>재연결</button>}</div></header>
      <div className="workspace-top"><div><span className="eyebrow"><span /> YOUR RESEARCH, CONNECTED</span><h1>문서에서 근거를, 연구에서 인사이트를.</h1><p>흩어진 연구문서에 질문하고, 출처가 있는 답변을 만나보세요.</p></div><span className="workspace-badge"><FlaskConical size={15} /> Research workspace</span></div>
      {error && <div className="error-banner" role="alert"><span>{error}</span><button aria-label="오류 메시지 닫기" onClick={() => setError('')}><X size={16} /></button></div>}
      <div className="stats-row"><div><span className="stat-icon"><FileText size={18} /></span><span><strong>{documents.length}</strong><small>등록된 문서</small></span></div><div><span className="stat-icon"><BookOpen size={18} /></span><span><strong>{totalPages}</strong><small>검색 가능한 페이지*</small></span></div><div><span className="stat-icon"><Search size={18} /></span><span><strong>Top {topK}</strong><small>질문별 검색 범위</small></span></div><span className="stat-note">*등록된 PDF의 전체 페이지 수</span></div>

      <section className="chat-panel" aria-label="연구문서 질의응답">
        <div className="panel-heading"><span><span className="assistant-icon"><Sparkles size={17} /></span><strong>Research Assistant</strong><span className="beta-badge">RAG</span></span><button disabled={asking || !messages.length} onClick={() => { setMessages([]); setQuestion(''); }}><Plus size={15} /> 새 대화</button></div>
        <div className="conversation">
          {messages.length === 0 ? <div className="welcome">
            <div className="welcome-symbol"><Layers3 size={30} /><span className="little-star">✦</span></div>
            <span className="welcome-eyebrow">LESS SEARCHING. MORE DISCOVERY.</span>
            <h2>어떤 연구가 궁금하신가요?</h2><p>업로드한 PDF에서 관련 내용을 찾아<br />근거와 함께 답변해드릴게요.</p>
            <div className="suggestion-grid">{suggestions.map(({ label, question: prompt, icon: Icon }) => <button key={label} onClick={() => { setQuestion(prompt); questionInput.current?.focus(); }}><span><Icon size={17} /> {label}<ArrowUpRight size={14} /></span><p>{prompt}</p></button>)}</div>
            <div className="sample-note"><FlaskConical size={14} /><span>샘플 질문은 <code>sample_data/</code>의 가상 연구 PDF 업로드 후 사용할 수 있어요.</span></div>
          </div> : <div className="message-list">{messages.map((message, i) => <article key={i} className={`message ${message.role}`}>
            <div className="message-label">{message.role === 'user' ? <><span className="user-avatar">나</span> 질문</> : <><span className="assistant-icon"><Sparkles size={15} /></span> Research Assistant</>}</div>
            {message.role === 'assistant' ? <><p className="answer-text">{message.answer}</p>{message.sources.length > 0 && <Sources sources={message.sources} />}{!message.grounded && <p className="no-evidence-note">질문을 구체적으로 바꾸거나 관련 PDF를 추가해주세요.</p>}</> : <p className="answer-text" role={message.role === 'error' ? 'alert' : undefined}>{message.text}</p>}
          </article>)}{asking && <div className="thinking" role="status"><LoaderCircle className="spin" size={17} /><span>문서에서 근거를 찾고 답변을 작성하고 있어요…</span></div>}<div ref={bottom} /></div>}
        </div>
        <div className="composer-wrap"><form onSubmit={submit} className="composer"><label className="sr-only" htmlFor="question">연구문서에 질문하기</label><textarea ref={questionInput} id="question" value={question} maxLength={2000} rows={2} onChange={event => setQuestion(event.target.value)} placeholder={documents.length ? '연구문서에 대해 질문해보세요…' : '먼저 왼쪽에서 PDF를 업로드해주세요…'} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); if (!asking) event.currentTarget.form.requestSubmit(); } }} /><div className="composer-bottom"><span><span className="context-dot" /> {documents.length ? `${documents.length}개 문서를 바탕으로 답변` : '문서 업로드 후 질문할 수 있어요'}</span><div><label className="top-k">검색 수<select aria-label="검색할 chunk 수" value={topK} onChange={event => setTopK(Number(event.target.value))}>{[3, 5, 8, 10].map(value => <option key={value} value={value}>Top {value}</option>)}</select></label><button className="send-button" type="submit" aria-label="질문 보내기" disabled={!question.trim() || asking || uploading || !documents.length}>{asking ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}</button></div></div></form><p className="composer-caption"><ShieldCheck size={12} /> 답변의 정확성은 Sources의 원문과 함께 확인해주세요.<span>Enter 전송 · Shift + Enter 줄바꿈</span></p></div>
      </section>
      <footer><span>내 연구문서 탐색을 돕는 AI Assistant <span className="footer-dot">·</span> Portfolio project</span><span>문서를 연결하고, 연구를 이어가세요 <ArrowRight size={12} /></span></footer>
    </main>

    {help && <div className="modal-backdrop" onClick={() => setHelp(false)}><section className="help-modal" role="dialog" aria-modal="true" aria-labelledby="help-title" onClick={event => event.stopPropagation()} onKeyDown={event => { if (event.key === 'Escape') setHelp(false); }}><button autoFocus className="close-modal icon-button" aria-label="사용 가이드 닫기" onClick={() => setHelp(false)}><X size={20} /></button><span className="eyebrow">QUICK START</span><h2 id="help-title">첫 번째 연구 질문까지</h2><ol><li><strong>연구 PDF를 업로드하세요.</strong><p>텍스트가 있는 PDF를 사용하세요. 스캔 이미지의 OCR은 지원하지 않습니다.</p></li><li><strong>궁금한 내용을 질문하세요.</strong><p>한국어와 영어 질문을 지원합니다. 각 질문은 독립적으로 처리됩니다.</p></li><li><strong>Sources에서 근거를 확인하세요.</strong><p>파일명, 실제 PDF 페이지 번호, 인용문과 검색된 원문을 확인할 수 있어요.</p></li></ol><div className="guide-note">샘플 PDF는 모두 가상의 데이터입니다. OpenAI 사용 시 질문과 검색된 문서 일부가 해당 API로 전송됩니다. Ollama 사용 시 설정한 Ollama 서버로 전송됩니다.</div><a href="/api/docs" target="_blank" rel="noreferrer">API 문서 열기 <ArrowUpRight size={15} /></a></section></div>}
  </div>;
}

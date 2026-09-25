# 내 연구문서 탐색을 돕는 AI Assistant

Research Document Explorer · Evidence-grounded RAG Assistant

연구자가 PDF를 올리고 자연어로 질문하면, 페이지를 보존한 텍스트 chunk를 다국어 임베딩으로 바꾸고 ChromaDB에서 의미적으로 가까운 근거를 검색한 뒤 LLM이 답하는 포트폴리오용 RAG 웹서비스입니다. 모든 답변은 검증된 PDF 파일명과 페이지를 함께 보여주며, 근거가 없으면 `제공된 문서에서 근거를 찾을 수 없습니다`를 반환합니다.

## Architecture

```text
PDF upload → PyMuPDF pages → token chunks + overlap → multilingual-e5-small
                                                        ↓
Question → query embedding → Chroma cosine search (top_k=5) → OpenAI/Ollama → verified citations
```

페이지 경계에서 chunk를 나누는 이유는 출처 페이지를 정확히 유지하기 위해서입니다. overlap은 경계에서 끊긴 문장이 검색되지 않는 문제를 줄입니다. E5는 문서에 `passage:`와 질문에 `query:` 접두사를 사용합니다. LLM은 검색된 context만 받고 JSON 형식으로 답하며, 서버가 citation의 chunk ID와 실제 quote를 다시 검증합니다.

## Stack

Python/FastAPI, React/Vite, PyMuPDF, ChromaDB, `intfloat/multilingual-e5-small`, OpenAI Responses API 또는 Ollama. OpenAI 구조화 출력은 공식 문서의 JSON Schema 방식을 사용하고, Chroma는 cosine 공간의 query 결과를 사용합니다.

## Run

먼저 Node.js 20 이상이 설치되어 있어야 합니다. `node --version`과 `npm --version`이 동작하지 않으면 Node.js를 설치한 뒤 아래 명령을 실행하세요. 프론트엔드와 백엔드는 서로 다른 터미널에서 실행하며, 각 터미널은 서버가 실행 중인 동안 닫지 않습니다.

터미널 1 — 백엔드:

```bash
cp .env.example .env
python3 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements-dev.txt
python scripts/generate_sample_pdfs.py
uvicorn app.main:app --app-dir backend --reload
```

터미널 2 — 프론트엔드:

```bash
cd frontend
npm install
npm run dev
```

터미널에 `Local: http://localhost:5173/`가 표시된 뒤 브라우저에서 http://localhost:5173 을 엽니다. 화면이 비어 있으면 터미널의 Vite 오류와 브라우저 개발자 도구 Console 오류를 먼저 확인하세요. 기본 provider는 Ollama입니다. `ollama serve`와 `ollama pull qwen2.5:3b`를 실행하거나 `.env`에서 `LLM_PROVIDER=openai`, `OPENAI_API_KEY=...`로 바꿉니다. `DEMO_FALLBACK=true`이면 provider가 준비되지 않은 상태에서도 검색된 문장만 인용하는 오프라인 fallback이 동작합니다. 이는 LLM 생성이 아닌 안전한 데모 모드이며, 실제 답변 생성에는 Ollama 또는 OpenAI를 사용하세요. 최초 PDF 업로드 때 임베딩 모델이 다운로드됩니다.

Docker: `cp .env.example .env && docker compose up --build`.

## API

`GET /health` 서버 상태, `POST /documents/upload` 여러 PDF 업로드(multipart `files`), `GET /documents` 문서 목록, `POST /chat` `{ "question": "...", "top_k": 5 }`를 제공합니다. `/chat` 응답에는 `answer`, `grounded`, `retrieved_count`, 그리고 `sources[{file_name,page,quote,excerpt,similarity}]`가 포함됩니다.

## Tests

`cd backend && pytest -m 'not integration'`은 PDF 추출과 chunking을 실행합니다. `pytest`는 실제 embedding 모델을 다운로드하는 retrieval 통합 테스트도 포함합니다.

## Sample data (local demo only)

`sample_data/`의 PDF는 `scripts/generate_sample_pdfs.py`가 만드는 로컬 데모용 가상 연구문서입니다. 각 문서 첫 페이지에 `SYNTHETIC SAMPLE DATA FOR RAG DEMO`를 표시했으며 실제 연구자료나 제조 의사결정의 근거가 아닙니다. 예시 PDF와 로컬 ChromaDB 데이터는 GitHub에 올리지 않습니다.

## Portfolio screenshot

<!-- Add a screenshot or short screen recording here after running the frontend. -->

![Application screenshot placeholder](docs/screenshot-placeholder.png)

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === 'string' ? detail : `요청에 실패했습니다 (${response.status}). 서버 연결과 입력을 확인해주세요.`);
  }
  if (body === null) throw new Error('API 응답을 읽을 수 없습니다. 백엔드가 실행 중인지 확인해주세요.');
  return body;
}

export const getHealth = () => request('/health');
export const getDocuments = () => request('/documents');
export function uploadDocuments(files) {
  const body = new FormData();
  files.forEach(file => body.append('files', file));
  return request('/documents/upload', { method: 'POST', body });
}
export const askQuestion = (question, top_k) => request('/chat', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question, top_k }),
});

export const BACKEND_URL = 'http://localhost:8000';
export const API_URL = `${BACKEND_URL}/api/auth`;

function getCookie(name: string) {
  if (typeof document === 'undefined') return undefined;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    let csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
      await fetch(`${API_URL}/csrf/`, { credentials: 'include' });
      csrfToken = getCookie('csrftoken');
    }
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  const contentType = response.headers.get('content-type');
  let data = null;
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    console.error('API Error:', {
      url,
      method,
      status: response.status,
      statusText: response.statusText,
      body: data
    })
    if (typeof data === 'object') {
      const errorMsg = data.detail || data.non_field_errors?.[0] || Object.values(data as Record<string, any>)[0]?.[0] || 'An error occurred';
      throw new Error(`HTTP ${response.status}: ${errorMsg}`, { cause: data });
    }
    throw new Error(`HTTP ${response.status}: ${data}`);
  }

  return data;
}

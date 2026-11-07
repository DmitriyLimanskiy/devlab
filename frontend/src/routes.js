export const pages = { catalog: '/catalog', git: '/git-course' }
export const api = { catalog: '/api/v1/catalog', git: '/api/v1/git-course' }

// Сформировать HTTP-адрес текущего снимка практической сессии
export const practiceApi = id => `/api/v1/practice-sessions/${encodeURIComponent(id)}/snapshot`
// Сформировать адрес WebSocket-событий графа сессии
export const practiceEvents = id => `/ws/practice-sessions/${encodeURIComponent(id)}`

// Сформировать HTTP-адрес ограниченной страницы истории графа
export const practiceHistory = (id, after, through) => `/api/v1/practice-sessions/${encodeURIComponent(id)}/snapshots?after_id=${after}&through_id=${through}`

// Сформировать HTTP-адрес оперативного состояния файлов сессии
export const worktreeApi = id => `/api/v1/practice-sessions/${encodeURIComponent(id)}/worktree`
// Сформировать адрес WebSocket-обновлений файлов сессии
export const worktreeEvents = id => `/ws/practice-sessions/${encodeURIComponent(id)}/worktree`

// Сформировать адрес страницы выбранного Git-курса
export const gitCoursePage = slug => `${pages.git}?course=${encodeURIComponent(slug)}`

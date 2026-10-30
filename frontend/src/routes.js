export const pages = { catalog: '/catalog', git: '/git-course' }
export const api = { catalog: '/api/v1/catalog', git: '/api/v1/git-course' }

export const practiceApi = id => `/api/v1/practice-sessions/${encodeURIComponent(id)}/snapshot`
export const practiceEvents = id => `/ws/practice-sessions/${encodeURIComponent(id)}`

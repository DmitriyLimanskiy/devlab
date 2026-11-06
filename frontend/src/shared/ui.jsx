export function IconButton({ label, children, ...props }) {
  return <button className="icon-button" type="button" aria-label={label} title={label} {...props}>{children}</button>
}

export function Badge({ children }) {
  return <span className="badge">{children}</span>
}

export function Status({ children, active = false }) {
  return <span className={`status ${active ? 'status-active' : ''}`} role="status"><span className="status-dot" aria-hidden="true" />{children}</span>
}

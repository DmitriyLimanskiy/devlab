export function IconButton({ label, children, ...props }) {
  return <button className="icon-button" type="button" aria-label={label} title={label} {...props}>{children}</button>
}

export function Badge({ children }) {
  return <span className="badge">{children}</span>
}

export function Status({ children }) {
  return <span className="status"><span className="status-dot" aria-hidden="true" />{children}</span>
}

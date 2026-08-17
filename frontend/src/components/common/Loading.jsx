const Loading = ({ text = 'Chargement...' }) => (
  <div className="loading-container">
    <div className="loading-spinner" />
    <p className="text-muted" style={{ marginTop: '12px' }}>{text}</p>
  </div>
)

export default Loading
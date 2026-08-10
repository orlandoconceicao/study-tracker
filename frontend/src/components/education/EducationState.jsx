import React from "react";

export default function EducationState({ loading, error, loadingText, onRetry, children }) {
  if (loading) return <p className="education-status muted">{loadingText}</p>;
  if (error) return <div className="education-status card"><p>{error}</p>{onRetry && <button type="button" onClick={onRetry}>Tentar novamente</button>}</div>;
  return children;
}

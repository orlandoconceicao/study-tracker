import React from "react";

export default function ProgressBar({ value, label = "Progresso" }) {
  if (value === null || value === undefined || value === "") return null;
  const percentage = Math.max(0, Math.min(100, Number(value)));
  return <div className="education-progress"><div className="progress-label"><span>{label}</span><strong>{Math.round(percentage)}%</strong></div><div className="progress-track" role="progressbar" aria-label={label} aria-valuemin="0" aria-valuemax="100" aria-valuenow={percentage}><span style={{ width: `${percentage}%` }} /></div></div>;
}

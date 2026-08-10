import React from "react";
import { Link } from "react-router-dom";

export default function EducationCard({ title, description, detail, to, state, action }) {
  return <article className="education-card card"><div><h2>{title}</h2>{description && <p>{description}</p>}{detail && <small>{detail}</small>}</div><Link className="button" to={to} state={state}>{action}</Link></article>;
}

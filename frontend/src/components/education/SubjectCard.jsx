import React from "react";
import { Link } from "react-router-dom";
import ProgressBar from "./ProgressBar";

export default function SubjectCard({ link, grade, progress }) {
  const subject = link.subject;
  return <article className="education-card card subject-card"><div className="subject-icon" aria-hidden="true">{subject.icon || subject.name.slice(0, 1)}</div><div className="subject-card-copy"><h2>{subject.name}</h2>{subject.description && <p>{subject.description}</p>}<p className="muted">{link.content_count || 0} conteúdos disponíveis</p><ProgressBar value={progress} /></div><Link className="button" to={`/learn/subject/${link.id}`} state={{ gradeSubject: link, grade }}>Ver conteúdos →</Link></article>;
}

import React from "react";
import TopicItem from "./TopicItem";

export default function UnitSection({ unit, topics, progressByTopic, context }) {
  return <section className="unit-section card"><span className="eyebrow">UNIDADE {unit.order || ""}</span><h2>{unit.title}</h2>{unit.description && <p>{unit.description}</p>}{topics.length ? <ol className="topic-list">{topics.map((topic) => <TopicItem key={topic.id} topic={topic} progress={progressByTopic[topic.id]} context={context} />)}</ol> : <p className="empty-inline">Nenhum conteúdo cadastrado nesta unidade.</p>}</section>;
}

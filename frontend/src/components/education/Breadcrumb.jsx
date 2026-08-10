import React from "react";
import { Link } from "react-router-dom";

export default function Breadcrumb({ items }) {
  return <nav className="education-breadcrumb" aria-label="Navegação estrutural"><Link to="/learn">Aprender</Link>{items.filter((item) => item?.label).map((item, index) => <React.Fragment key={`${item.label}-${index}`}><span aria-hidden="true">›</span>{item.to ? <Link to={item.to} state={item.state}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}</React.Fragment>)}</nav>;
}

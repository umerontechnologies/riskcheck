import React from "react";
import { Link, NavLink } from "react-router-dom";

export default function Header({ theme, setTheme }) {
  return (
    <header className="rc-header">
      <div className="rc-container rc-header-inner">
        <Link to="/" className="rc-brand" aria-label="RiskCheck home">
          <img src="/logo.svg" alt="" className="rc-logo" />
          <span className="rc-logo-text">RiskCheck</span>
        </Link>

        <nav className="rc-nav">
          <NavLink to="/" end className={({ isActive }) => "rc-navlink" + (isActive ? " active" : "")}>Check</NavLink>
          <NavLink to="/how-it-works" className={({ isActive }) => "rc-navlink" + (isActive ? " active" : "")}>How it works</NavLink>
          <NavLink to="/report" className={({ isActive }) => "rc-navlink" + (isActive ? " active" : "")}>Report scam</NavLink>
          <NavLink to="/contact" className={({ isActive }) => "rc-navlink" + (isActive ? " active" : "")}>Contact</NavLink>

          <button
            className="rc-navbtn"
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            type="button"
            aria-label="Toggle theme"
          >
            {theme === "light" ? "🌙" : "☀️"} {theme}
          </button>

          <a className="rc-navlink rc-navlink-ghost" href="https://umerontechnologies.com" target="_blank" rel="noreferrer">
            UMERON Technologies
          </a>
        </nav>
      </div>
    </header>
  );
}

import React from "react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="rc-footer">
      <div className="rc-container">
        <div className="rc-footerPro">
          <div>
            <div className="rc-footerBrand">RiskCheck</div>
            <div className="rc-footerText">
              A risk assessment tool by{" "}
              <a href="https://umerontechnologies.com" target="_blank" rel="noreferrer">
                UMERON Technologies
              </a>
              . We show signals + uncertainty — we don’t label anyone a scammer.
            </div>
          </div>

          <div className="rc-footerLinks">
            <Link to="/how-it-works">How it works</Link>
            <span className="sep">•</span>
            <Link to="/report">Report scam</Link>
            <span className="sep">•</span>
            <Link to="/terms">Terms</Link>
            <span className="sep">•</span>
            <Link to="/privacy">Privacy</Link>
            <span className="sep">•</span>
            <Link to="/contact">Contact</Link>
          </div>
        </div>

        <div style={{ marginTop: 10, color: "var(--muted)", fontSize: 12, display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
          <span>© {new Date().getFullYear()} UMERON Technologies. All rights reserved.</span>
          <span>Made for safer online transactions (Pakistan → worldwide).</span>
        </div>
      </div>
    </footer>
  );
}

import React from "react";

export default function Contact() {
  return (
    <div className="rc-page">
      <div className="hero">
        <h1>Contact</h1>
        <p>For partnerships, feedback, or data removal requests.</p>
      </div>

      <div className="card">
        <h2 className="cardTitle">UMERON Technologies</h2>
        <p className="muted">
          Website: <a href="https://umerontechnologies.com" target="_blank" rel="noreferrer">umerontechnologies.com</a>
          <br />
          Email: <a href="mailto:umerontechnologies@gmail.com">umerontechnologies@gmail.com</a>
        </p>

        <div className="divider" />

        <h3 className="subhead">Notes</h3>
        <ul className="bullets">
          <li>We may ask for additional proof before approving any community report.</li>
          <li>If you believe a report is incorrect, contact us with evidence so we can review and remove if needed.</li>
        </ul>
      </div>
    </div>
  );
}

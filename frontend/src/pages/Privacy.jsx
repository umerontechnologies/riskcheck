import React from "react";

export default function Privacy() {
  return (
    <div className="rc-page">
      <div className="hero">
        <h1>Privacy</h1>
        <p>Last updated: {new Date().toLocaleDateString()}</p>
      </div>

      <div className="card">
        <h2 className="cardTitle">What we collect</h2>
        <ul className="bullets">
          <li>Identifiers you enter (links, handles, phone numbers, emails, websites).</li>
          <li>Optional evidence checklist answers.</li>
          <li>Optional screenshot/evidence images you upload.</li>
        </ul>

        <h2 className="cardTitle">How we use it</h2>
        <p>
          We use this data to generate a risk report and to identify reused content (e.g., the same screenshot used across different listings). Community reports may be counted after admin review.
        </p>

        <h2 className="cardTitle">What we do NOT do</h2>
        <ul className="bullets">
          <li>We do not sell your data.</li>
          <li>We do not access private Facebook/Instagram/WhatsApp chats or private groups.</li>
          <li>We do not magically verify identity without official platform permissions.</li>
        </ul>

        <h2 className="cardTitle">Your choices</h2>
        <p>
          Don’t upload sensitive personal documents. If you need data removal, contact us and share the report ID.
        </p>
      </div>
    </div>
  );
}

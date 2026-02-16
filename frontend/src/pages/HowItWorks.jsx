import React from "react";

export default function HowItWorks() {
  return (
    <div className="rc-page">
      <div className="hero">
        <h1>How RiskCheck works</h1>
        <p>
          RiskCheck combines <b>public internet signals</b> (Google search results), <b>community reports</b>, and optional
          evidence checks to estimate <b>risk & uncertainty</b> before you pay.
        </p>
      </div>

      <div className="card">
        <h2 className="cardTitle">Signals we use</h2>
        <ul className="list">
          <li>
            <b>Public footprint (Google results)</b> — We search for the provided number / email / link on the public web. If a seller is
            real, you often find business listings, posts, directories, or consistent mentions.
          </li>
          <li>
            <b>Negative mentions</b> — If the same number / link appears with words like “scam”, “fraud”, “complaint”, etc, we raise risk.
          </li>
          <li>
            <b>Reachability & security</b> — For website/ad links we check if the URL is reachable and whether HTTPS exists.
          </li>
          <li>
            <b>Domain age (when available)</b> — New domains can be higher risk. We try to estimate domain age using public RDAP.
          </li>
          <li>
            <b>Community reports</b> — Reports submitted by users are stored. Only <b>approved</b> reports affect risk. Pending reports are not treated as truth.
          </li>
          <li>
            <b>Screenshot matching</b> — We can detect if the same screenshot/ad image is reused across multiple reports (a common scam pattern).
          </li>
        </ul>

        <h2 className="cardTitle" style={{ marginTop: 16 }}>Limitations (important)</h2>
        <ul className="list">
          <li>We cannot reliably read private Facebook groups, private Instagram profiles, or content behind logins.</li>
          <li>“Many results” does not prove someone is safe; it only improves verifiability and confidence.</li>
          <li>RiskCheck does <b>not</b> label anyone a scammer. It helps you decide what precautions to take.</li>
        </ul>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h2 className="cardTitle">Tips to stay safe (Pakistan + worldwide)</h2>
        <ul className="list">
          <li>Prefer COD, escrow, or platform-protected payments. Avoid advance payment to unknown sellers.</li>
          <li>Ask for proof: invoice, CNIC (with privacy), live video, and consistent business details.</li>
          <li>Cross-check name, phone, and bank account title. If they refuse basic verification, treat as high risk.</li>
        </ul>
      </div>
    </div>
  );
}

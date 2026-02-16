import React from "react";

export default function Terms() {
  return (
    <div className="rc-page">
      <div className="hero">
        <h1>Terms</h1>
        <p>Last updated: {new Date().toLocaleDateString()}</p>
      </div>

      <div className="card">
        <h2 className="cardTitle">Important</h2>
        <ul className="bullets">
          <li>
            RiskCheck provides <b>risk & uncertainty indicators</b> based on public web signals and community reports. It does not declare anyone a scammer.
          </li>
          <li>
            Do not share sensitive personal data in reports (CNIC/passport, home address, bank statements, private chats containing third‑party information).
          </li>
          <li>
            Community reports are stored as <b>pending</b> and may be reviewed/approved/rejected by admins.
          </li>
          <li>
            Use the tool as one input. Always verify independently (COD/escrow, invoices, live video, meet in a safe place).
          </li>
        </ul>

        <h2 className="cardTitle">Acceptable use</h2>
        <p>
          You agree not to use RiskCheck for harassment, stalking, doxxing, defamation, or any illegal activity.
        </p>

        <h2 className="cardTitle">No warranty</h2>
        <p>
          RiskCheck is provided “as is”. We don’t guarantee completeness, accuracy, or availability of third‑party data sources.
        </p>
      </div>
    </div>
  );
}

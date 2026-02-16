import React, { useMemo, useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { submitCommunityReport, uploadFile } from "../api.js";

const PLATFORMS = [
  { key: "facebook", name: "Facebook", accent: "#1877F2" },
  { key: "instagram", name: "Instagram", accent: "#C13584" },
  { key: "whatsapp", name: "WhatsApp", accent: "#25D366" },
  { key: "telegram", name: "Telegram", accent: "#229ED9" },
  { key: "olx", name: "OLX", accent: "#2F80ED" },
  { key: "pakwheels", name: "PakWheels", accent: "#1E3A8A" },
  { key: "daraz", name: "Daraz", accent: "#F85606" },
  { key: "amazon", name: "Amazon", accent: "#FF9900" },
  { key: "aliexpress", name: "AliExpress", accent: "#FF4747" },
  { key: "website", name: "Website", accent: "#2563EB" },
  { key: "other", name: "Other", accent: "#334155" }
];

function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

function Field({ label, hint, error, required, ok, children }) {
  return (
    <div className="rc-field">
      <div className="rc-fieldTop">
        <div className="rc-label">
          {label} {required ? <span className="rc-required">*</span> : null}
          {ok && !error ? <span className="rc-okDot" title="Looks good" /> : null}
        </div>
        {hint ? <div className="rc-hint">{hint}</div> : null}
      </div>

      <div className={cx("rc-control", error && "rc-controlError", ok && !error && "rc-controlOk")}>{children}</div>
      {error ? <div className="rc-error">{error}</div> : null}
    </div>
  );
}

export default function ReportScam() {
  const [params] = useSearchParams();

  const initialType = params.get("entity_type") || params.get("type") || "facebook";
  const initialVal = params.get("entity_value") || params.get("value") || "";

  const [platform, setPlatform] = useState(initialType);
  const accent = useMemo(() => PLATFORMS.find((p) => p.key === platform)?.accent || "#2563EB", [platform]);

  useEffect(() => {
    document.documentElement.style.setProperty("--accent", accent);
  }, [accent]);

  const [entityValue, setEntityValue] = useState(initialVal);

  const [category, setCategory] = useState("advance_payment_fraud");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [evidenceUrl, setEvidenceUrl] = useState("");
  const [reporterContact, setReporterContact] = useState("");

  const [file, setFile] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const canSubmit = useMemo(() => description.trim().length >= 12 && (entityValue || "").trim().length >= 3, [description, entityValue]);

  function validate() {
    const e = {};
    if ((entityValue || "").trim().length < 3) e.entityValue = "Required: provide a valid link / number / identifier.";
    if ((description || "").trim().length < 12) e.description = "Required: explain what happened (at least 12 characters).";
    setFieldErrors(e);
    return Object.keys(e).length === 0;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!validate()) {
      setError("Please fix the required fields.");
      return;
    }

    setSubmitting(true);
    try {
      let uploaded = null;
      if (file) uploaded = await uploadFile(file);

      const out = await submitCommunityReport({
        entity_type: platform,
        entity_value: (entityValue || "").trim(),
        category,
        description: description.trim(),
        amount: amount ? Number(amount) : null,
        evidence_url: evidenceUrl.trim() || null,
        reporter_contact: reporterContact.trim() || null,
        attachment_sha256s: uploaded ? [uploaded.sha256] : null,
        linked_accounts: null
      });

      setSuccess(`Submitted. Report ID #${out.id} (status: ${out.status}). It will affect checks after admin approval.`);
      setDescription("");
      setAmount("");
      setEvidenceUrl("");
      setReporterContact("");
      setFile(null);
    } catch (err) {
      setError(err.message || "Failed to submit report");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rc-shell">
      <div className="rc-bgGlow" aria-hidden="true" />
      <div className="rc-wrap">
        <header className="rc-hero">
          <div className="rc-heroTop">
            <div className="rc-heroBadge">Community Report</div>
            <div className="rc-heroTitle">Report a scam / incident</div>
            <div className="rc-heroSub">
              Reports start as <b>pending</b>. Only approved reports affect results. Please stay factual and avoid sensitive personal data.
            </div>
          </div>

          <div className="rc-heroStrip">
            <div className="rc-stripItem">
              <div className="rc-stripK">Tip</div>
              <div className="rc-stripV">Add a screenshot if possible</div>
            </div>
            <div className="rc-stripItem">
              <div className="rc-stripK">Safety</div>
              <div className="rc-stripV">Don’t share CNIC, OTPs, passwords</div>
            </div>
            <div className="rc-stripItem">
              <div className="rc-stripK">Review</div>
              <div className="rc-stripV">Approval required before public impact</div>
            </div>
          </div>
        </header>

        <div className="rc-grid2">
          <section className="rc-card rc-cardLift">
            <div className="rc-cardHead">
              <div>
                <div className="rc-cardTitle">Incident report</div>
                <div className="rc-cardDesc">Help others by reporting what happened (truthfully).</div>
              </div>
              <div className="rc-accentSwatch" title="Platform accent" />
            </div>

            <form className="rc-form" onSubmit={onSubmit} noValidate>
              <Field label="Platform" hint="Where did this happen?" required>
                <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                  {PLATFORMS.map((p) => (
                    <option key={p.key} value={p.key}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                label="Seller / Listing identifier"
                hint="Required — link, phone number, username, store URL, etc."
                required
                error={fieldErrors.entityValue}
                ok={(entityValue || "").trim().length >= 3}
              >
                <input value={entityValue} onChange={(e) => setEntityValue(e.target.value)} placeholder="Paste link / number" />
              </Field>

              <Field label="Category" hint="Select what type of incident happened" required>
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="advance_payment_fraud">Advance payment fraud</option>
                  <option value="non_delivery">Non-delivery</option>
                  <option value="counterfeit">Counterfeit / fake product</option>
                  <option value="impersonation">Impersonation</option>
                  <option value="phishing">Phishing</option>
                  <option value="other">Other</option>
                </select>
              </Field>

              <Field
                label="What happened?"
                hint="Required — write step-by-step. Include dates, platform chats, payment method."
                required
                error={fieldErrors.description}
                ok={description.trim().length >= 12}
              >
                <textarea
                  rows={6}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Example: Seller asked advance payment via Easypaisa, then blocked me..."
                />
              </Field>

              <div className="rc-row2">
                <Field label="Amount lost (PKR)" hint="Optional">
                  <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g., 25000" inputMode="numeric" />
                </Field>
                <Field label="Evidence link" hint="Optional (Drive link, post link, etc.)">
                  <input value={evidenceUrl} onChange={(e) => setEvidenceUrl(e.target.value)} placeholder="https://..." />
                </Field>
              </div>

              <Field label="Upload screenshot" hint="Optional (strongly recommended)">
                <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                {file ? <div className="rc-fileNote">Selected: <b>{file.name}</b></div> : null}
              </Field>

              <Field label="Your contact" hint="Optional (email or WhatsApp — only for follow-up)">
                <input value={reporterContact} onChange={(e) => setReporterContact(e.target.value)} placeholder="Optional" />
              </Field>

              {error ? <div className="rc-alert rc-alertError">⚠️ {error}</div> : null}
              {success ? <div className="rc-alert rc-alertOk">✅ {success}</div> : null}

              <button className="rc-primaryBtn" disabled={!canSubmit || submitting} type="submit">
                {submitting ? "Submitting..." : "Submit report"}
              </button>

              <div className="rc-actionsInline">
                <Link className="rc-linkBtn" to="/">← Back to Check</Link>
                <Link className="rc-linkBtn" to="/how-it-works">How it works</Link>
              </div>

              <div className="rc-finePrint">
                <b>Note:</b> False reports may be rejected. RiskCheck is a risk assessment tool; it does not make legal judgments.
              </div>
            </form>
          </section>

          <section className="rc-card rc-cardLift">
            <div className="rc-cardHead">
              <div>
                <div className="rc-cardTitle">Before you submit</div>
                <div className="rc-cardDesc">This increases approval chances and helps others.</div>
              </div>
            </div>

            <div className="rc-checklist">
              <div className="rc-checkItem">
                <div className="rc-checkDot">✅</div>
                <div>
                  <div className="rc-checkT">Include exact identifier</div>
                  <div className="rc-checkD">Phone number, page URL, store URL, ad link — whatever uniquely identifies the seller.</div>
                </div>
              </div>

              <div className="rc-checkItem">
                <div className="rc-checkDot">✅</div>
                <div>
                  <div className="rc-checkT">Add screenshot evidence</div>
                  <div className="rc-checkD">Chat, payment proof, listing screenshot — helps verification.</div>
                </div>
              </div>

              <div className="rc-checkItem">
                <div className="rc-checkDot">✅</div>
                <div>
                  <div className="rc-checkT">Avoid sensitive data</div>
                  <div className="rc-checkD">No CNIC, OTP, passwords, bank PIN. Blur them before uploading.</div>
                </div>
              </div>

              <div className="rc-checkItem">
                <div className="rc-checkDot">✅</div>
                <div>
                  <div className="rc-checkT">Be factual</div>
                  <div className="rc-checkD">Write what happened. Don’t add assumptions or insults.</div>
                </div>
              </div>
            </div>

            <div className="rc-disclaimer">
              Reports affect RiskCheck results only after admin review.
            </div>
          </section>
        </div>

        <footer className="rc-footer">
          <div className="rc-footerInner">
            <div className="rc-footerBrand">
              <div className="rc-footerLogo">🛡️</div>
              <div>
                <div className="rc-footerName">RiskCheck</div>
                <div className="rc-footerSmall">Community-powered risk assessment for safer buying.</div>
              </div>
            </div>
            <div className="rc-footerLinks">
              <Link to="/" className="rc-footerLink">Check</Link>
              <Link to="/how-it-works" className="rc-footerLink">How it works</Link>
              <a className="rc-footerLink" href="https://umerontechnologies.com" target="_blank" rel="noreferrer">UMERON Technologies</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

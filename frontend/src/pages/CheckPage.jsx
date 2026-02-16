import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createCheck, uploadFile, reportPdfUrl } from "../api.js";

const PLATFORMS = [
  { key: "facebook", name: "Facebook", accent: "#1877F2" },
  { key: "instagram", name: "Instagram", accent: "#C13584" },
  { key: "whatsapp", name: "WhatsApp", accent: "#25D366" },
  { key: "telegram", name: "Telegram", accent: "#229ED9" },
  { key: "tiktok", name: "TikTok", accent: "#111827" },
  { key: "olx", name: "OLX / Marketplace Ad", accent: "#2F80ED" },
  { key: "daraz", name: "Daraz", accent: "#F85606" },
  { key: "amazon", name: "Amazon", accent: "#FF9900" },
  { key: "aliexpress", name: "AliExpress", accent: "#FF4747" },
  { key: "ebay", name: "eBay", accent: "#0064D2" },
  { key: "craigslist", name: "Craigslist", accent: "#6B21A8" },
  { key: "gumtree", name: "Gumtree", accent: "#00A650" },
  { key: "carousell", name: "Carousell", accent: "#FF5A5F" },
  { key: "pakwheels", name: "PakWheels", accent: "#1E3A8A" },
  { key: "autotrader", name: "AutoTrader", accent: "#DC2626" },
  { key: "website", name: "Website / Link", accent: "#2563EB" },
  { key: "other", name: "Other", accent: "#334155" }
];

const PLATFORM_FAST_TIPS = {
  facebook: [
    "Avoid ‘shipping only’ deals for local Marketplace items. Meet in a public place and inspect before paying.",
    "Never pay via gift cards/crypto/wire for Marketplace purchases. Use platform protections, COD, or escrow.",
    "Urgency is a red flag (‘many buyers’, ‘deposit now’). Slow down and verify identity + item proof."
  ],
  instagram: [
    "Be careful with ‘DM to buy’ shops without business details. Ask for invoice, address, and verifiable phone.",
    "Fake shops often reuse images—request a live video showing the item + today’s date.",
    "Avoid direct bank transfer/crypto to unknown sellers. Prefer safer checkout/buyer protection methods."
  ],
  whatsapp: [
    "Never share OTP/verification codes. This is a common account takeover method.",
    "Advance payment pressure is a red flag—prefer COD/escrow or pay after verifiable proof.",
    "Cross-check the number on Google and match the same identity across links they share."
  ],
  telegram: [
    "Telegram scams often push urgency (‘limited stock’). Avoid advance payment to unknown sellers.",
    "Use escrow/COD where possible. Off-platform transfers are risky and hard to reverse.",
    "Ask for consistent proof: live call, invoice, and matching details across platforms."
  ],
  tiktok: [
    "Be cautious of ‘too cheap’ deals in comments/DMs. Scammers quickly move you off-platform.",
    "Ask for ownership proof (live video + timestamp) before sending any money.",
    "Avoid wire/crypto/gift cards. Prefer buyer-protected payment methods."
  ],
  olx: [
    "Don’t pay deposits before inspection. Meet safely and verify the product physically.",
    "Beware courier/rider stories (‘someone will collect payment’). Confirm inside the platform and use safe methods.",
    "Check seller history; brand-new accounts + urgent discounts are higher risk."
  ],
  pakwheels: [
    "Verify documents + chassis/engine numbers. Meet in daylight in a safe location.",
    "Avoid advance payments before inspection/test drive. Use verified escrow/bank procedure for big deals.",
    "If price is far below market + seller pushes urgency, treat as high risk."
  ],
  daraz: [
    "Pay only through Daraz checkout. Avoid WhatsApp or external links asking direct transfer.",
    "Check store rating + recent reviews. New stores with extreme discounts can be risky.",
    "Keep chat/orders inside Daraz for dispute support and buyer protection."
  ],
  amazon: [
    "Keep payment and communication on Amazon. Avoid external links and direct transfers.",
    "Check seller rating and return policy. Off-platform payment requests are major red flags.",
    "Be careful with unusually cheap listings for high-value items."
  ],
  aliexpress: [
    "Pay only through AliExpress checkout. Off-platform payment requests are risky.",
    "Check store age, rating, and review photos. New stores with huge discounts can be suspicious.",
    "Use tracked shipping and record unboxing for disputes."
  ],
  ebay: [
    "Avoid off-platform payments. Use eBay-supported methods for protection.",
    "Check seller feedback and history; brand-new sellers for expensive items are higher risk.",
    "Decline rushed ‘deal outside eBay’ offers."
  ],
  website: [
    "Check HTTPS, real contact details, and return policy. Missing basics increases risk.",
    "Search the site/brand + phone/email on Google; scam sites often have complaint footprints.",
    "If they accept only wire/crypto/gift cards, treat it as high risk."
  ],
  other: [
    "Avoid off-platform payments (wire, crypto, gift cards) unless fully verified.",
    "Ask for verifiable proof: invoice, live video, address, and matching identity across accounts.",
    "If the seller pressures urgency, pause and verify more."
  ]
};

const RISK_META = {
  High: { icon: "🚨", label: "High Risk", tone: "high" },
  Medium: { icon: "⚠️", label: "Warning", tone: "medium" },
  Unknown: { icon: "❓", label: "Unverified", tone: "unknown" },
  Low: { icon: "✅", label: "Lower Risk", tone: "low" }
};

const SIGNAL_ICON = { High: "🚨", Medium: "⚠️", Low: "✅", Unknown: "❓" };

function triToBool(v) {
  if (v === "yes") return true;
  if (v === "no") return false;
  return null;
}

function normalizeUrlInput(v) {
  const s = (v || "").trim();
  if (!s) return "";
  if (/^https?:\/\//i.test(s)) return s;
  if (s.includes(".") || s.includes("/")) return "https://" + s;
  return s;
}

function hexToRgb(hex) {
  const h = (hex || "").replace("#", "").trim();
  if (h.length === 3) {
    return {
      r: parseInt(h[0] + h[0], 16),
      g: parseInt(h[1] + h[1], 16),
      b: parseInt(h[2] + h[2], 16)
    };
  }
  if (h.length === 6) {
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16)
    };
  }
  return { r: 37, g: 99, b: 235 };
}

function rgba(hex, a) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function Field({ label, hint, error, required, ok, children }) {
  return (
    <div className="rc-field">
      <div className="rc-fieldTop">
        <div className="rc-label">
          {label} {required ? <span className="rc-req">*</span> : null}
        </div>
        {hint ? <div className="rc-hint">{hint}</div> : null}
      </div>

      <div className={["rc-control", error ? "rc-controlError" : "", ok ? "rc-controlOk" : ""].join(" ")}>
        {children}
      </div>

      {error ? <div className="rc-errorMsg">{error}</div> : null}
    </div>
  );
}

function TriSelect({ label, value, onChange, hint }) {
  return (
    <Field label={label} hint={hint}>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="unknown">Not sure</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </Field>
  );
}

function platformPrimaryLabel(platform) {
  if (platform === "whatsapp" || platform === "telegram") return "Seller phone number";
  if (platform === "instagram") return "Instagram handle or URL";
  if (platform === "tiktok") return "TikTok handle or URL";
  if (platform === "website") return "Website URL";
  if (["olx", "pakwheels", "autotrader", "craigslist", "gumtree", "carousell"].includes(platform)) return "Ad / Listing URL";
  if (["daraz", "amazon", "aliexpress", "ebay"].includes(platform)) return "Product or Store URL";
  if (platform === "facebook") return "Facebook Page/Profile/Group URL";
  return "Link / Identifier";
}

function platformPrimaryPlaceholder(platform) {
  if (platform === "whatsapp" || platform === "telegram") return "+92XXXXXXXXXX or 03XXXXXXXXX";
  if (platform === "instagram") return "@handle or https://instagram.com/handle";
  if (platform === "tiktok") return "@handle or https://tiktok.com/@handle";
  return "Paste the link here…";
}

export default function CheckPage() {
  const [platform, setPlatform] = useState(() => localStorage.getItem("rc_platform") || "facebook");
  const accent = useMemo(
    () => PLATFORMS.find((p) => p.key === platform)?.accent || "#2563EB",
    [platform]
  );

  const fastTips = useMemo(
    () => PLATFORM_FAST_TIPS[platform] || PLATFORM_FAST_TIPS.other,
    [platform]
  );

  useEffect(() => {
    document.documentElement.style.setProperty("--accent", accent);
    document.documentElement.style.setProperty("--accentSoft", rgba(accent, 0.12));
    document.documentElement.style.setProperty("--accentGlow", rgba(accent, 0.35));
    localStorage.setItem("rc_platform", platform);
    localStorage.setItem("rc_accent", accent);
  }, [platform, accent]);

  // Main inputs
  const [entityValue, setEntityValue] = useState("");
  const [intent, setIntent] = useState("");
  const [priceRange, setPriceRange] = useState("");

  // Seller contacts (affect scoring)
  const [sellerPhone, setSellerPhone] = useState("");
  const [sellerEmail, setSellerEmail] = useState("");
  const [sellerWebsite, setSellerWebsite] = useState("");

  // User contact (not scoring)
  const [userContact, setUserContact] = useState("");

  // Upload
  const [checkFile, setCheckFile] = useState(null);
  const [checkUpload, setCheckUpload] = useState(null);

  // Cross platform
  const [linked, setLinked] = useState([]);

  // Evidence fields (tri-state)
  const [hasAbout, setHasAbout] = useState("unknown");
  const [hasReviews, setHasReviews] = useState("unknown");
  const [hasAddress, setHasAddress] = useState("unknown");
  const [hasPhone, setHasPhone] = useState("unknown");
  const [hasWebsite, setHasWebsite] = useState("unknown");
  const [hasOldPosts, setHasOldPosts] = useState("unknown");
  const [hasRecentPosts, setHasRecentPosts] = useState("unknown");

  // Chat commerce
  const [askedAdvance, setAskedAdvance] = useState("unknown");
  const [paymentMethod, setPaymentMethod] = useState("");

  // Marketplace
  const [locationProvided, setLocationProvided] = useState("unknown");
  const [sellerAgeVisible, setSellerAgeVisible] = useState("unknown");

  // Website/ecom
  const [httpsPresent, setHttpsPresent] = useState("unknown");
  const [returnPolicyVisible, setReturnPolicyVisible] = useState("unknown");

  // Result state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [formErrors, setFormErrors] = useState({});
  const [touched, setTouched] = useState({}); // { field: true }

  function touch(name) {
    setTouched((p) => ({ ...p, [name]: true }));
  }

  function addLinked() {
    setLinked((prev) => [...prev, { platform: "instagram", value: "" }]);
  }
  function updateLinked(i, patch) {
    setLinked((prev) => {
      const next = prev.slice();
      next[i] = { ...next[i], ...patch };
      return next;
    });
  }
  function removeLinked(i) {
    setLinked((prev) => {
      const next = prev.slice();
      next.splice(i, 1);
      return next;
    });
  }

  function buildEvidence() {
    const e = {
      has_about: triToBool(hasAbout),
      has_reviews: triToBool(hasReviews),
      has_address: triToBool(hasAddress),
      has_phone_or_email: triToBool(hasPhone),
      has_website: triToBool(hasWebsite),
      has_posts_older_than_6_months: triToBool(hasOldPosts),
      has_recent_posts_last_30_days: triToBool(hasRecentPosts),

      asked_advance_payment: triToBool(askedAdvance),
      payment_method: paymentMethod.trim() || null,

      location_provided: triToBool(locationProvided),
      seller_age_visible: triToBool(sellerAgeVisible),

      https_present: triToBool(httpsPresent),
      return_policy_visible: triToBool(returnPolicyVisible)
    };

    Object.keys(e).forEach((k) => {
      if (e[k] === null) delete e[k];
    });
    return e;
  }

  function validate() {
    const errs = {};
    if ((entityValue || "").trim().length < 3) errs.entityValue = "Required: add a valid link / handle / number.";
    return errs;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);

    touch("entityValue");

    const errs = validate();
    setFormErrors(errs);
    if (Object.keys(errs).length) {
      setError("Please fix the highlighted fields and try again.");
      return;
    }

    setLoading(true);

    try {
      let uploaded = null;
      if (checkFile) {
        uploaded = await uploadFile(checkFile);
        setCheckUpload(uploaded);
      } else {
        setCheckUpload(null);
      }

      const payload = {
        entity_type: platform,
        entity_value: normalizeUrlInput(entityValue),
        intent: intent.trim() || null,
        price_range: priceRange.trim() || null,

        seller_phone: sellerPhone.trim() || null,
        seller_email: sellerEmail.trim() || null,
        seller_website: normalizeUrlInput(sellerWebsite) || null,
        user_contact: userContact.trim() || null,

        evidence: buildEvidence(),
        attachment_sha256s: uploaded ? [uploaded.sha256] : null,
        linked_accounts: linked
          .map((x) => ({ platform: x.platform, value: x.value.trim() }))
          .filter((x) => x.value.length >= 3)
      };

      const data = await createCheck(payload);
      setResult(data);
    } catch (err) {
      setError(err?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const riskMeta = result ? RISK_META[result.risk_level] || RISK_META.Unknown : null;

  const showSocialEvidence = platform === "facebook" || platform === "instagram" || platform === "tiktok";
  const showChatEvidence = platform === "whatsapp" || platform === "telegram";
  const showMarketplaceEvidence = ["olx", "craigslist", "gumtree", "carousell", "pakwheels", "autotrader"].includes(platform);
  const showEcomEvidence = ["daraz", "amazon", "aliexpress", "ebay"].includes(platform);
  const showWebsiteEvidence = platform === "website";

  const entityOk = touched.entityValue && !formErrors.entityValue && (entityValue || "").trim().length >= 3;

  return (
    <div className="rc-check">
      <div className="rc-checkBg" />

      <div className="rc-wrap">
        <header className="rc-hero">
          <div className="rc-heroLeft">
            <div className="rc-heroBadge">
              <span className="dot" />
              RiskCheck • Public footprint + evidence checks
            </div>

            <h1 className="rc-heroTitle">Check before you pay</h1>

            <p className="rc-heroSub">
              We verify <b>public data</b> (Google results), platform signals, community reports, and optional screenshot matching.
              This is a risk assessment — <b>not</b> a verdict.
            </p>

            {/* ✅ Platform-based tips */}
            <div className="rc-heroQuick">
              {fastTips.slice(0, 3).map((t, idx) => (
                <div key={idx} className="qCard">
                  <div className="qIcon">{idx === 0 ? "🛡️" : idx === 1 ? "💳" : "⏳"}</div>
                  <div>
                    <div className="qTitle">Fast tip #{idx + 1}</div>
                    <div className="qText">{t}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rc-heroRight">
            <div className="rc-heroPanel">
              <div className="rc-heroPanelTop">
                <div className="rc-heroPanelTitle">Platform</div>
                <div
                  className="rc-chip"
                  style={{ background: rgba(accent, 0.18), borderColor: rgba(accent, 0.35) }}
                >
                  {PLATFORMS.find((p) => p.key === platform)?.name}
                </div>
              </div>

              <div className="rc-heroPanelBody">
                Tip quality improves if you add seller <b>phone/email/website</b> — confidence increases only when we can verify public signals.
              </div>
            </div>
          </div>
        </header>

        <div className="rc-grid">
          {/* LEFT: FORM */}
          <section className="rc-card rc-cardForm">
            <div className="rc-cardHead">
              <h2>Run a check</h2>
              <div className="rc-cardHint">Fields with <span className="rc-req">*</span> are required.</div>
            </div>

            <form onSubmit={onSubmit} className="rc-form" noValidate>
              <Field label="Platform" hint="Where did you find the seller/listing?">
                <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                  {PLATFORMS.map((p) => (
                    <option key={p.key} value={p.key}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </Field>

              <Field
                label={platformPrimaryLabel(platform)}
                hint="Main identifier for this platform"
                required
                error={touched.entityValue ? formErrors.entityValue : ""}
                ok={entityOk}
              >
                <input
                  value={entityValue}
                  onBlur={() => touch("entityValue")}
                  onChange={(e) => setEntityValue(e.target.value)}
                  placeholder={platformPrimaryPlaceholder(platform)}
                  required
                />
              </Field>

              <div className="rc-row2">
                <Field label="What are you buying?" hint="Optional (helps context)">
                  <input value={intent} onChange={(e) => setIntent(e.target.value)} placeholder="e.g., phone, car, shoes" />
                </Field>
                <Field label="Price / Amount" hint="Optional">
                  <input value={priceRange} onChange={(e) => setPriceRange(e.target.value)} placeholder="e.g., 25000" />
                </Field>
              </div>

              <div className="rc-divider" />

              <div className="rc-sectionTitle">
                <h3>Seller contact details</h3>
                <p>These improve accuracy because we can search public footprint for each.</p>
              </div>

              <div className="rc-row2">
                <Field label="Seller phone (WhatsApp)" hint="Optional (recommended)">
                  <input value={sellerPhone} onChange={(e) => setSellerPhone(e.target.value)} placeholder="+92... or 03..." />
                </Field>
                <Field label="Seller email" hint="Optional (recommended)">
                  <input value={sellerEmail} onChange={(e) => setSellerEmail(e.target.value)} placeholder="name@example.com" />
                </Field>
              </div>

              <Field label="Seller website" hint="Optional">
                <input value={sellerWebsite} onChange={(e) => setSellerWebsite(e.target.value)} placeholder="https://example.com" />
              </Field>

              <Field label="Your contact" hint="Optional (not used for scoring)">
                <input value={userContact} onChange={(e) => setUserContact(e.target.value)} placeholder="Email or WhatsApp" />
              </Field>

              <Field
                label="Upload screenshot / ad image"
                hint="Optional. Confidence only increases when we can match it with past reports (hash/near-duplicate)."
              >
                <input
                  className="rc-file"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setCheckFile(e.target.files?.[0] || null)}
                />
                {checkFile && (
                  <div className="rc-fileNote">
                    Selected: <b>{checkFile.name}</b>
                  </div>
                )}
                {checkUpload?.url && (
                  <div className="rc-fileNote">
                    Uploaded • Hash: <span className="rc-mono">{checkUpload.sha256.slice(0, 18)}…</span>
                  </div>
                )}
              </Field>

              <div className="rc-divider" />

              <div className="rc-sectionTitle">
                <h3>Cross-platform accounts</h3>
                <p>Add Instagram/Website/WhatsApp etc. We check public footprint for each.</p>
              </div>

              <div className="rc-linked">
                {linked.map((item, i) => (
                  <div key={i} className="rc-linkedRow">
                    <select value={item.platform} onChange={(e) => updateLinked(i, { platform: e.target.value })}>
                      {PLATFORMS.map((p) => (
                        <option key={p.key} value={p.key}>
                          {p.name}
                        </option>
                      ))}
                    </select>

                    <input
                      value={item.value}
                      onChange={(e) => updateLinked(i, { value: e.target.value })}
                      placeholder="Paste link / number / handle"
                    />

                    <button type="button" className="rc-miniBtn" onClick={() => removeLinked(i)}>
                      Remove
                    </button>
                  </div>
                ))}

                <button type="button" className="rc-btn rc-btnSecondary" onClick={addLinked}>
                  + Add related account
                </button>
              </div>

              <div className="rc-divider" />

              {showSocialEvidence && (
                <>
                  <div className="rc-sectionTitle">
                    <h3>Evidence checks (Social)</h3>
                    <p>Answer what you can. “Not sure” is okay.</p>
                  </div>
                  <div className="rc-evidenceGrid">
                    <TriSelect label="About section present?" value={hasAbout} onChange={setHasAbout} hint="Transparency" />
                    <TriSelect label="Reviews visible?" value={hasReviews} onChange={setHasReviews} hint="Accountability" />
                    <TriSelect label="Address/location shown?" value={hasAddress} onChange={setHasAddress} hint="Verification" />
                    <TriSelect label="Phone or email shown?" value={hasPhone} onChange={setHasPhone} hint="Traceability" />
                    <TriSelect label="Website link present?" value={hasWebsite} onChange={setHasWebsite} hint="External footprint" />
                    <TriSelect label="Posts older than 6 months?" value={hasOldPosts} onChange={setHasOldPosts} hint="History" />
                    <TriSelect label="Recent posts (last 30 days)?" value={hasRecentPosts} onChange={setHasRecentPosts} hint="Activity" />
                  </div>
                </>
              )}

              {showChatEvidence && (
                <>
                  <div className="rc-sectionTitle">
                    <h3>Evidence checks (Chat)</h3>
                    <p>Advance payment requests are a common scam signal.</p>
                  </div>
                  <div className="rc-evidenceGrid">
                    <TriSelect
                      label="Did they ask advance payment?"
                      value={askedAdvance}
                      onChange={setAskedAdvance}
                      hint="High risk signal"
                    />
                    <Field label="Payment method" hint="Optional (bank transfer / easypaisa / jazzcash etc.)">
                      <input value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} placeholder="Optional" />
                    </Field>
                  </div>
                </>
              )}

              {showMarketplaceEvidence && (
                <>
                  <div className="rc-sectionTitle">
                    <h3>Evidence checks (Marketplace)</h3>
                    <p>More transparency usually means less risk.</p>
                  </div>
                  <div className="rc-evidenceGrid">
                    <TriSelect label="Location provided?" value={locationProvided} onChange={setLocationProvided} hint="Transparency" />
                    <TriSelect label="Seller age visible?" value={sellerAgeVisible} onChange={setSellerAgeVisible} hint="Context" />
                  </div>
                </>
              )}

              {showEcomEvidence && (
                <>
                  <div className="rc-sectionTitle">
                    <h3>Evidence checks (E-commerce)</h3>
                    <p>Return policy visibility helps reduce risk.</p>
                  </div>
                  <div className="rc-evidenceGrid">
                    <TriSelect label="Return policy visible?" value={returnPolicyVisible} onChange={setReturnPolicyVisible} hint="Buyer protection" />
                  </div>
                </>
              )}

              {showWebsiteEvidence && (
                <>
                  <div className="rc-sectionTitle">
                    <h3>Evidence checks (Website)</h3>
                    <p>HTTPS is a basic trust signal (not a guarantee).</p>
                  </div>
                  <div className="rc-evidenceGrid">
                    <TriSelect label="HTTPS present?" value={httpsPresent} onChange={setHttpsPresent} hint="Basic security" />
                  </div>
                </>
              )}

              <button disabled={loading} className="rc-btn rc-btnPrimary">
                {loading ? "Checking…" : "Generate Risk Report"}
              </button>

              {error && <div className="rc-alert rc-alertError">⚠️ {error}</div>}

              <div className="rc-note">
                <b>Reminder:</b> “Unverified” means not enough verified public data. Prefer COD / escrow / platform-protected payments.
              </div>
            </form>
          </section>

          {/* RIGHT: RESULT */}
          <section className="rc-card rc-cardResult">
            <div className="rc-cardHead">
              <h2>Result</h2>
              <div className="rc-cardHint">Your report will appear here.</div>
            </div>

            {!result ? (
              <div className="rc-empty">
                <div className="rc-emptyIcon">🧾</div>
                <div className="rc-emptyTitle">No report yet</div>
                <div className="rc-emptyText">Fill required fields and generate a report to see risk signals.</div>

                <div className="rc-skeleton">
                  <div className="skLine" />
                  <div className="skLine" />
                  <div className="skLine short" />
                </div>
              </div>
            ) : (
              <div className="rc-result">
                <div className="rc-summary">
                  <span className={`rc-badge rc-badge-${riskMeta.tone}`}>
                    {riskMeta.icon} {riskMeta.label}
                  </span>
                  <span className="rc-pill">Confidence: <b>{result.confidence}%</b></span>
                  <span className="rc-pill">Grade: <b>{result.grade}</b></span>
                </div>

                <div className="rc-box">
                  <div className="rc-boxLabel">Entity</div>
                  <div className="rc-mono">
                    {result.entity_type} — {result.entity_value}
                  </div>
                </div>

                <div className="rc-box">
                  <div className="rc-boxLabel">Community reports</div>
                  <div className="rc-muted">
                    Approved: <b>{result.community?.approved_count ?? 0}</b> &nbsp;|&nbsp; Pending: <b>{result.community?.pending_count ?? 0}</b>
                  </div>
                  <div className="rc-muted rc-small">
                    Only <b>approved</b> reports affect risk level. Pending reports are not treated as truth.
                  </div>
                </div>

                <div className="rc-box">
                  <div className="rc-boxLabel">Signals</div>
                  <div className="rc-signals">
                    {result.signals.map((s, idx) => (
                      <div key={idx} className={`rc-signal rc-signal-${(s.status || "Unknown").toLowerCase()}`}>
                        <div className="rc-signalTop">
                          <div className="rc-signalLeft">
                            <div className="rc-signalIcon">{SIGNAL_ICON[s.status] || "❓"}</div>
                            <div className="rc-signalName">{s.name}</div>
                          </div>
                          <div className="rc-signalStatus">{s.status}</div>
                        </div>
                        <div className="rc-signalNote">{s.note}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rc-box">
                  <div className="rc-boxLabel">Recommendation</div>
                  <div className="rc-reco">{(result.rationale || "").replace(/\*\*/g, "")}</div>
                </div>

                <div className="rc-actions">
                  <a className="rc-btn rc-btnSecondary" href={reportPdfUrl(result.id)} target="_blank" rel="noreferrer">
                    Download PDF
                  </a>

                  <Link
                    className="rc-btn rc-btnDanger"
                    to={`/report?entity_type=${encodeURIComponent(result.entity_type)}&entity_value=${encodeURIComponent(result.entity_value)}`}
                  >
                    Report incident
                  </Link>
                </div>

                <div className="rc-disclaimer">
                  Confidence reflects how much public data we could verify (not “safety”). Always use buyer protections.
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

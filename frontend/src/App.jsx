import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Header from "./components/Header.jsx";
import Footer from "./components/Footer.jsx";

import CheckPage from "./pages/CheckPage.jsx";
import HowItWorks from "./pages/HowItWorks.jsx";
import ReportScam from "./pages/ReportScam.jsx";
import Terms from "./pages/Terms.jsx";
import Privacy from "./pages/Privacy.jsx";
import Contact from "./pages/Contact.jsx";

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("rc_theme") || "light");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("rc_theme", theme);
  }, [theme]);

  return (
    <BrowserRouter>
      <div className="rc-shell">
        <Header theme={theme} setTheme={setTheme} />
        <main className="rc-main">
          <div className="rc-container">
            <Routes>
              <Route path="/" element={<CheckPage />} />
              <Route path="/how-it-works" element={<HowItWorks />} />
              <Route path="/report" element={<ReportScam />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/contact" element={<Contact />} />
            </Routes>
          </div>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

import { useState } from "react";
import PageHeader from "../components/PageHeader";
import Footer from "../components/Footer";
import { usePageMeta } from "../hooks/usePageMeta";
import { submitContact } from "../api";

export default function ContactPage() {
  usePageMeta(
    "Contact HomeIQ.ie",
    "Get in touch with the HomeIQ team. Questions about our property price data, content permission requests, feedback, or automated price updates for your area.",
    [{ name: "Contact", url: "/contact" }],
  );

  const [form, setForm] = useState({ message: "", price_updates: false, name: "", email: "" });
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  const set = (k: "message" | "name" | "email") =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");
    try {
      await submitContact(form);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="static-page">
      <PageHeader title="Contact Us" />
      <main className="static-content">
        <section className="about-section">
          <p className="about-lead">
            Have a question about our property price data, want to request permission to reuse our
            content, or spotted something that needs fixing? Send us a message and we'll get back to you.
          </p>
        </section>

        <section className="about-section">
          {status === "done" ? (
            <div className="modal-success">
              <p>Thanks — we'll be in touch!</p>
            </div>
          ) : (
            <form className="modal-form" onSubmit={handleSubmit}>
              <label>
                Your message
                <textarea rows={5} value={form.message} onChange={set("message")} required />
              </label>
              <label className="modal-checkbox">
                <input
                  type="checkbox"
                  checked={form.price_updates}
                  onChange={e => setForm(f => ({ ...f, price_updates: e.target.checked }))}
                />
                I would be interested in automated price updates for my area
              </label>
              <div className="modal-row">
                <label>
                  Your name
                  <input type="text" value={form.name} onChange={set("name")} autoComplete="name" required />
                </label>
                <label>
                  Your email
                  <input type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
                </label>
              </div>
              {status === "error" && (
                <p className="modal-error">Something went wrong — please try again.</p>
              )}
              <div className="modal-actions">
                <button type="submit" className="modal-btn" disabled={status === "sending"}>
                  {status === "sending" ? "Sending…" : "Send Message"}
                </button>
              </div>
            </form>
          )}
        </section>
      </main>
      <Footer />
    </div>
  );
}

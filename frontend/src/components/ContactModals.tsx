import { useEffect, useRef, useState } from "react";
import { submitFeedback, submitContact } from "../api";

type ModalType = "feedback" | "contact" | null;

function Modal({ title, onClose, children }: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="modal-overlay"
      ref={overlayRef}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className="modal-box" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function FeedbackModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ datasets: "", comments: "", name: "", email: "" });
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");
    try {
      await submitFeedback(form);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  };

  return (
    <Modal title="Send Feedback" onClose={onClose}>
      {status === "done" ? (
        <div className="modal-success">
          <p>Thanks for your feedback!</p>
          <button className="modal-btn" onClick={onClose}>Close</button>
        </div>
      ) : (
        <form className="modal-form" onSubmit={handleSubmit}>
          <label>
            What data sets or analytics would you like to see?
            <textarea rows={3} value={form.datasets} onChange={set("datasets")} />
          </label>
          <label>
            Any other comments
            <textarea rows={3} value={form.comments} onChange={set("comments")} />
          </label>
          <div className="modal-row">
            <label>
              Your name
              <input type="text" value={form.name} onChange={set("name")} autoComplete="name" />
            </label>
            <label>
              Your email
              <input type="email" value={form.email} onChange={set("email")} autoComplete="email" />
            </label>
          </div>
          {status === "error" && <p className="modal-error">Something went wrong — please try again.</p>}
          <div className="modal-actions">
            <button type="button" className="modal-btn modal-btn--secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="modal-btn" disabled={status === "sending"}>
              {status === "sending" ? "Sending…" : "Send Feedback"}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function ContactModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ message: "", price_updates: false, name: "", email: "" });
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");

  const set = (k: "message" | "name" | "email") => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
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
    <Modal title="Contact Us" onClose={onClose}>
      {status === "done" ? (
        <div className="modal-success">
          <p>Thanks — we'll be in touch!</p>
          <button className="modal-btn" onClick={onClose}>Close</button>
        </div>
      ) : (
        <form className="modal-form" onSubmit={handleSubmit}>
          <label>
            Your message
            <textarea rows={4} value={form.message} onChange={set("message")} />
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
              <input type="text" value={form.name} onChange={set("name")} autoComplete="name" />
            </label>
            <label>
              Your email
              <input type="email" value={form.email} onChange={set("email")} autoComplete="email" />
            </label>
          </div>
          {status === "error" && <p className="modal-error">Something went wrong — please try again.</p>}
          <div className="modal-actions">
            <button type="button" className="modal-btn modal-btn--secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="modal-btn" disabled={status === "sending"}>
              {status === "sending" ? "Sending…" : "Send Message"}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}

export default function ContactSidebar() {
  const [open, setOpen] = useState<ModalType>(null);

  return (
    <>
      <div className="contact-sidebar">
        <button className="contact-sidebar-btn" onClick={() => setOpen("feedback")}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Feedback
        </button>
        <button className="contact-sidebar-btn" onClick={() => setOpen("contact")}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
          </svg>
          Contact
        </button>
      </div>

      {open === "feedback" && <FeedbackModal onClose={() => setOpen(null)} />}
      {open === "contact" && <ContactModal onClose={() => setOpen(null)} />}
    </>
  );
}

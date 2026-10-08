"use client";

import { useState } from "react";

function EyeIcon({ open }: { open: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M2 12s3.8-7 10-7 10 7 10 7-3.8 7-10 7-10-7-10-7Z" />
      {open ? (
        <circle cx="12" cy="12" r="3" />
      ) : (
        <path d="M4 4l16 16" strokeLinecap="round" />
      )}
    </svg>
  );
}

export default function PasswordField({
  id,
  label,
  value,
  onChange,
  required,
  minLength,
  autoComplete,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  minLength?: number;
  autoComplete?: string;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="field">
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          minLength={minLength}
          autoComplete={autoComplete}
          className="input-rule pr-8"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
          className="absolute -right-1.5 top-1/2 -translate-y-1/2 p-2 text-ink/40 hover:text-ink"
        >
          <EyeIcon open={visible} />
        </button>
      </div>
    </div>
  );
}

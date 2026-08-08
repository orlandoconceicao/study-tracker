import React, { useState } from "react";

export default function AuthInput({ label, type = "text", error, ...props }) {
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";
  return (
    <label className="auth-field">
      <span className="auth-label">{label}</span>
      <div className="auth-password-wrapper">
        <input
          className="auth-input"
          type={isPassword && visible ? "text" : type}
          aria-invalid={Boolean(error)}
          {...props}
        />
        {isPassword && (
          <button
            className="auth-password-toggle"
            type="button"
            onClick={() => setVisible(!visible)}
          >
            {visible ? "Ocultar" : "Mostrar"}
          </button>
        )}
      </div>
      {error && <small>{error}</small>}
    </label>
  );
}

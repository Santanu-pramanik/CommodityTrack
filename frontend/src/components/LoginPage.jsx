import React from "react";
import { loginWithGoogle } from "../services/auth";

export default function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-logo">
          ↗
        </div>

        <h1>CommodityTrack</h1>

        <p className="login-subtitle">
          Gold & Silver Market Intelligence
        </p>

        <button
          className="google-login-button"
          onClick={loginWithGoogle}
        >
          <span className="google-icon">G</span>
          Continue with Google
        </button>

        <p className="login-note">
          Sign in to access your market dashboard,
          alerts and AI-powered insights.
        </p>

      </div>
    </div>
  );
}
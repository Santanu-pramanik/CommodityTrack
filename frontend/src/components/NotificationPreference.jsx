import React, { useState } from "react";

const API_BASE =
  "https://commoditytrack-production-5160.up.railway.app";

export default function NotificationPreference({
  userId,
  onComplete,
}) {
  const [channels, setChannels] = useState({
    email: true,
    sms: false,
    whatsapp: false,
    telegram: false,
  });

  const [phone, setPhone] = useState("");
  const [telegram, setTelegram] = useState("");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const toggleChannel = (channel) => {
    setChannels((prev) => ({
      ...prev,
      [channel]: !prev[channel],
    }));
  };

  const handleContinue = async () => {
    setError("");

    if (
      !channels.email &&
      !channels.sms &&
      !channels.whatsapp &&
      !channels.telegram
    ) {
      setError("Please select at least one notification method.");
      return;
    }

    if ((channels.sms || channels.whatsapp) && !phone.trim()) {
      setError("Please enter your phone number.");
      return;
    }

    if (channels.telegram && !telegram.trim()) {
      setError("Please enter your Telegram username.");
      return;
    }

    try {
      setSaving(true);

      const response = await fetch(
        `${API_BASE}/api/auth/notification-preferences`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: Number(userId),

            email_enabled: channels.email,
            sms_enabled: channels.sms,
            whatsapp_enabled: channels.whatsapp,
            telegram_enabled: channels.telegram,

            phone_number: phone.trim() || null,
            telegram_username: telegram.trim() || null,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to save notification preferences."
        );
      }

      onComplete();

    } catch (err) {
      setError(err.message);

    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="notification-page">
      <div className="notification-card">

        <div className="notification-icon">
          🔔
        </div>

        <h1>Stay Updated</h1>

        <p className="notification-subtitle">
          Where should we send your CommodityTrack alerts?
        </p>

        <div className="notification-options">

          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.email}
              onChange={() => toggleChannel("email")}
            />

            <div>
              <strong>📧 Email</strong>
              <span>
                Market alerts and important events
              </span>
            </div>
          </label>

          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.sms}
              onChange={() => toggleChannel("sms")}
            />

            <div>
              <strong>📱 SMS</strong>
              <span>
                Important market alerts via SMS
              </span>
            </div>
          </label>

          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.whatsapp}
              onChange={() => toggleChannel("whatsapp")}
            />

            <div>
              <strong>💬 WhatsApp</strong>
              <span>
                Receive alerts on WhatsApp
              </span>
            </div>
          </label>

          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.telegram}
              onChange={() => toggleChannel("telegram")}
            />

            <div>
              <strong>✈️ Telegram</strong>
              <span>
                Receive alerts on Telegram
              </span>
            </div>
          </label>

        </div>

        {(channels.sms || channels.whatsapp) && (
          <div className="notification-input">
            <label>Phone Number</label>

            <input
              type="tel"
              placeholder="+91 XXXXX XXXXX"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
        )}

        {channels.telegram && (
          <div className="notification-input">
            <label>Telegram Username</label>

            <input
              type="text"
              placeholder="@yourusername"
              value={telegram}
              onChange={(e) => setTelegram(e.target.value)}
            />
          </div>
        )}

        {error && (
          <div className="notification-error">
            {error}
          </div>
        )}

        <button
          className="continue-button"
          onClick={handleContinue}
          disabled={saving}
        >
          {saving ? "Saving..." : "Continue →"}
        </button>

        <small className="notification-skip">
          You can change these preferences later in Settings.
        </small>

      </div>
    </div>
  );
}
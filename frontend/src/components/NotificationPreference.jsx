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

  const [consent, setConsent] = useState({
    email: true,
    sms: false,
    whatsapp: false,
    telegram: false,
  });

  const [phone, setPhone] = useState("");
  const [telegramUsername, setTelegramUsername] = useState("");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const toggleChannel = (channel) => {
    const newValue = !channels[channel];

    setChannels((prev) => ({
      ...prev,
      [channel]: newValue,
    }));

    // If channel is disabled, remove its consent
    if (!newValue) {
      setConsent((prev) => ({
        ...prev,
        [channel]: false,
      }));
    }
  };

  const toggleConsent = (channel) => {
    setConsent((prev) => ({
      ...prev,
      [channel]: !prev[channel],
    }));
  };

  const handleContinue = async () => {
    setError("");

    // At least one notification channel
    const hasChannel =
      channels.email ||
      channels.sms ||
      channels.whatsapp ||
      channels.telegram;

    if (!hasChannel) {
      setError(
        "Please select at least one notification method."
      );
      return;
    }

    // Email consent
    if (channels.email && !consent.email) {
      setError(
        "Please allow email alerts to continue."
      );
      return;
    }

    // SMS consent
    if (channels.sms && !consent.sms) {
      setError(
        "Please allow SMS alerts to continue."
      );
      return;
    }

    // WhatsApp consent
    if (channels.whatsapp && !consent.whatsapp) {
      setError(
        "Please allow WhatsApp alerts to continue."
      );
      return;
    }

    // Telegram consent
    if (channels.telegram && !consent.telegram) {
      setError(
        "Please allow Telegram alerts to continue."
      );
      return;
    }

    // Phone number required for SMS / WhatsApp
    if (
      (channels.sms || channels.whatsapp) &&
      !phone.trim()
    ) {
      setError(
        "Please enter your phone number for SMS or WhatsApp alerts."
      );
      return;
    }

    // Telegram username required
    if (
      channels.telegram &&
      !telegramUsername.trim()
    ) {
      setError(
        "Please enter your Telegram username."
      );
      return;
    }

    try {
      setSaving(true);

      const payload = {
        user_id: Number(userId),

        email_enabled: channels.email,
        sms_enabled: channels.sms,
        whatsapp_enabled: channels.whatsapp,
        telegram_enabled: channels.telegram,

        phone_number: phone.trim()
          ? phone.trim()
          : null,

        telegram_username: telegramUsername.trim()
          ? telegramUsername.trim()
          : null,

        email_consent:
          channels.email && consent.email,

        sms_consent:
          channels.sms && consent.sms,

        whatsapp_consent:
          channels.whatsapp && consent.whatsapp,

        telegram_consent:
          channels.telegram && consent.telegram,
      };

      const response = await fetch(
        `${API_BASE}/api/auth/notification-preferences`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response
        .json()
        .catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to save notification preferences."
        );
      }

      onComplete();
    } catch (err) {
      setError(
        err.message ||
          "Something went wrong while saving preferences."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="notification-overlay">
      <div className="notification-modal">

        <div className="notification-icon">
          🔔
        </div>

        <h1>Stay Updated</h1>

        <p className="notification-subtitle">
          Choose how you would like to receive your
          CommodityTrack alerts.
        </p>

        <div className="notification-options">

          {/* EMAIL */}
          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.email}
              onChange={() =>
                toggleChannel("email")
              }
            />

            <div>
              <strong>📧 Email</strong>
              <span>
                Market alerts and important events
              </span>
            </div>
          </label>

          {channels.email && (
            <label className="notification-consent">
              <input
                type="checkbox"
                checked={consent.email}
                onChange={() =>
                  toggleConsent("email")
                }
              />

              <span>
                I agree to receive CommodityTrack
                alerts by email.
              </span>
            </label>
          )}

          {/* SMS */}
          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.sms}
              onChange={() =>
                toggleChannel("sms")
              }
            />

            <div>
              <strong>📱 SMS</strong>
              <span>
                Important market alerts via SMS
              </span>
            </div>
          </label>

          {channels.sms && (
            <label className="notification-consent">
              <input
                type="checkbox"
                checked={consent.sms}
                onChange={() =>
                  toggleConsent("sms")
                }
              />

              <span>
                I agree to receive CommodityTrack
                alerts by SMS.
              </span>
            </label>
          )}

          {/* WHATSAPP */}
          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.whatsapp}
              onChange={() =>
                toggleChannel("whatsapp")
              }
            />

            <div>
              <strong>💬 WhatsApp</strong>
              <span>
                Receive alerts on WhatsApp
              </span>
            </div>
          </label>

          {channels.whatsapp && (
            <label className="notification-consent">
              <input
                type="checkbox"
                checked={consent.whatsapp}
                onChange={() =>
                  toggleConsent("whatsapp")
                }
              />

              <span>
                I agree to receive CommodityTrack
                alerts on WhatsApp.
              </span>
            </label>
          )}

          {/* PHONE NUMBER */}
          {(channels.sms || channels.whatsapp) && (
            <div className="notification-input">
              <label>Phone Number</label>

              <input
                type="tel"
                placeholder="+91 XXXXX XXXXX"
                value={phone}
                onChange={(e) =>
                  setPhone(e.target.value)
                }
              />
            </div>
          )}

          {/* TELEGRAM */}
          <label className="notification-option">
            <input
              type="checkbox"
              checked={channels.telegram}
              onChange={() =>
                toggleChannel("telegram")
              }
            />

            <div>
              <strong>✈️ Telegram</strong>
              <span>
                Receive alerts on Telegram
              </span>
            </div>
          </label>

          {channels.telegram && (
            <>
              <div className="notification-input">
                <label>
                  Telegram Username
                </label>

                <input
                  type="text"
                  placeholder="@yourusername"
                  value={telegramUsername}
                  onChange={(e) =>
                    setTelegramUsername(
                      e.target.value
                    )
                  }
                />
              </div>

              <label className="notification-consent">
                <input
                  type="checkbox"
                  checked={consent.telegram}
                  onChange={() =>
                    toggleConsent("telegram")
                  }
                />

                <span>
                  I agree to receive CommodityTrack
                  alerts on Telegram.
                </span>
              </label>
            </>
          )}

        </div>

        {/* ERROR */}
        {error && (
          <div className="notification-error">
            {error}
          </div>
        )}

        {/* CONTINUE */}
        <button
          className="continue-button"
          onClick={handleContinue}
          disabled={saving}
        >
          {saving
            ? "Saving..."
            : "Continue →"}
        </button>

        <small className="notification-skip">
          You can change these preferences later
          in Settings.
        </small>

      </div>
    </div>
  );
}
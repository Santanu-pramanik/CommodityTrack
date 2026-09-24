const API_BASE =
  "https://commoditytrack-production-5160.up.railway.app";

export const loginWithGoogle = () => {
  window.location.href = `${API_BASE}/api/auth/google`;
};

export const getUserIdFromURL = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get("user_id");
};

export const isLoginSuccess = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get("login") === "success";
};
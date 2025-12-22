const TOKEN_KEY = "mud_token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

export function setToken(token) {
  if (!token) return;
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ignore
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

import { register, login } from "./api.js";

export function setupAuthPage() {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const messageEl = document.getElementById("message");

  if (!loginForm || !registerForm || !tabLogin || !tabRegister || !messageEl) {
    return;
  }

  const setMessage = (text, ok = false) => {
    messageEl.textContent = text;
    messageEl.className = ok ? "ok" : "err";
  };

  const clearMessage = () => {
    messageEl.textContent = "";
    messageEl.className = "";
  };

  const showLogin = () => {
    tabLogin.classList.add("active");
    tabRegister.classList.remove("active");
    loginForm.style.display = "";
    registerForm.style.display = "none";
    clearMessage();
  };

  const showRegister = () => {
    tabRegister.classList.add("active");
    tabLogin.classList.remove("active");
    loginForm.style.display = "none";
    registerForm.style.display = "";
    clearMessage();
  };

  tabLogin.addEventListener("click", showLogin);
  tabRegister.addEventListener("click", showRegister);

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();
    const submitBtn = loginForm.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    const { username, password } = e.target;
    try {
      const data = await login(username.value, password.value);
      setToken(data.access_token);
      setMessage("登录成功，正在进入游戏…", true);
      setTimeout(() => {
        window.location.href = "/game";
      }, 500);
    } catch (err) {
      if (err && err.detail) {
        setMessage("登录失败: " + JSON.stringify(err.detail));
      } else {
        setMessage("登录失败: " + (err.message || String(err)));
      }
    } finally {
      submitBtn.disabled = false;
    }
  });

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();
    const submitBtn = registerForm.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    const { username, password } = e.target;
    try {
      const data = await register(username.value, password.value);
      setMessage("注册成功，请切换到登录标签进行登录。", true);
      showLogin();
    } catch (err) {
      if (err && err.detail) {
        setMessage("注册失败: " + JSON.stringify(err.detail));
      } else {
        setMessage("注册失败: " + (err.message || String(err)));
      }
    } finally {
      submitBtn.disabled = false;
    }
  });
}



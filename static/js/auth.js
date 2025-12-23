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
      
      // 检查是否有角色
      try {
        const { getCharacter } = await import("./api.js");
        const character = await getCharacter(data.access_token);
        setMessage("登录成功，正在进入游戏…", true);
        setTimeout(() => {
          window.location.href = "/game";
        }, 500);
      } catch (charErr) {
        // 没有角色，也跳转到游戏页面（游戏页面会显示创建角色界面）
        setMessage("登录成功，但尚未创建角色，进入游戏后请先创建角色。", true);
        setTimeout(() => {
          window.location.href = "/game";
        }, 1000);
      }
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
    const registeredUsername = username.value;
    try {
      const data = await register(registeredUsername, password.value);
      setMessage("注册成功，已自动切换到登录标签，请登录。", true);
      // 切换到登录标签并填充用户名
      showLogin();
      const loginUsernameInput = loginForm.querySelector("input[name='username']");
      if (loginUsernameInput) {
        loginUsernameInput.value = registeredUsername;
        // 自动聚焦到密码输入框
        const loginPasswordInput = loginForm.querySelector("input[name='password']");
        if (loginPasswordInput) {
          loginPasswordInput.focus();
        }
      }
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



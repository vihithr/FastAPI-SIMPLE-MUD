import { getToken, clearToken } from "./auth.js";
import { getCharacter, createCharacter } from "./api.js";
import { GameWebSocket, WS_STATE } from "./ws.js";

export function setupGamePage() {
  const logEl = document.getElementById("log");
  const connDot = document.getElementById("connDot");
  const connText = document.getElementById("connText");
  const userLabel = document.getElementById("userLabel");
  const connectBtn = document.getElementById("connectBtn");
  const disconnectBtn = document.getElementById("disconnectBtn");
  const cmdInput = document.getElementById("cmdInput");
  const sendBtn = document.getElementById("sendBtn");
  const btnClearLog = document.getElementById("btnClearLog");
  const btnHelp = document.getElementById("btnHelp");
  const btnRefreshChar = document.getElementById("btnRefreshChar");
  const currentRoomName = document.getElementById("currentRoomName");
  const currentRoomDesc = document.getElementById("currentRoomDesc");
  const currentRoomExits = document.getElementById("currentRoomExits");
  const commandsContainer = document.getElementById("commandsContainer");

  const charName = document.getElementById("charName");
  const charLevel = document.getElementById("charLevel");
  const charExp = document.getElementById("charExp");
  const charHpLabel = document.getElementById("charHpLabel");
  const charMpLabel = document.getElementById("charMpLabel");
  const charAtk = document.getElementById("charAtk");
  const charDef = document.getElementById("charDef");
  const hpBar = document.getElementById("hpBar");
  const mpBar = document.getElementById("mpBar");
  const miniMapSvg = document.getElementById("miniMapSvg");
  const miniMapScale = document.getElementById("miniMapScale");
  const charCreateBox = document.getElementById("charCreateBox");
  const charInfoBox = document.getElementById("charInfoBox");
  const charCreateForm = document.getElementById("charCreateForm");
  const charNameInput = document.getElementById("charNameInput");
  const charCreateMessage = document.getElementById("charCreateMessage");

  if (
    !logEl ||
    !connDot ||
    !connText ||
    !userLabel ||
    !connectBtn ||
    !disconnectBtn ||
    !cmdInput ||
    !sendBtn
  ) {
    return;
  }

  let autoScroll = true;
  let lastCharacter = null;
  let lastRoom = null;
  const MAP_NODES = {
    1: { x: 100, y: 120, name: "新手村广场" },
    2: { x: 100, y: 80, name: "武器店" },
    3: { x: 140, y: 120, name: "魔法学院" },
    4: { x: 140, y: 80, name: "训练场" },
    5: { x: 140, y: 40, name: "黑暗森林入口" },
    6: { x: 140, y: 10, name: "森林深处" },
    7: { x: 180, y: 40, name: "神秘洞穴" },
    8: { x: 180, y: 10, name: "宝藏室" },
  };
  const MAP_EDGES = [
    [1, 2],
    [1, 3],
    [2, 4],
    [3, 4],
    [4, 5],
    [5, 6],
    [5, 7],
    [7, 8],
  ];

  const appendLog = (type, text) => {
    const line = document.createElement("div");
    line.className = "log-line " + type;
    const time = new Date().toLocaleTimeString();
    line.textContent = `[${time}] ${text}`;
    logEl.appendChild(line);
    // 始终滚动到底部，保证最新信息可见
    logEl.scrollTop = logEl.scrollHeight;
  };

  const setConnState = (state) => {
    connDot.classList.remove("connected", "connecting", "error");
    if (state === WS_STATE.CONNECTED) {
      connDot.classList.add("connected");
      connText.textContent = "已连接";
    } else if (state === WS_STATE.CONNECTING || state === WS_STATE.RECONNECTING) {
      connDot.classList.add("connecting");
      connText.textContent =
        state === WS_STATE.RECONNECTING ? "重连中…" : "连接中…";
    } else {
      connText.textContent = "未连接";
    }
  };

  const updateRoomInfo = (room) => {
    if (!room || !currentRoomName || !currentRoomDesc || !currentRoomExits) return;
    lastRoom = room;
    currentRoomName.textContent = room.name || "未知地点";
    currentRoomDesc.textContent = room.description || "";
    if (room.exits) {
      const exits = Object.keys(room.exits);
      currentRoomExits.textContent =
        exits.length > 0 ? `出口: ${exits.join(" / ")}` : "出口: -";
    } else {
      currentRoomExits.textContent = "出口: -";
    }
    renderMiniMap(room);
  };

  const renderCommands = (available) => {
    if (!commandsContainer) return;
    commandsContainer.textContent = "";
    if (!available) return;

    const createSection = (title) => {
      const group = document.createElement("div");
      group.className = "controls-group";
      const titleEl = document.createElement("div");
      titleEl.className = "controls-group-title";
      titleEl.textContent = title;
      group.appendChild(titleEl);
      const row = document.createElement("div");
      row.className = "btn-row";
      group.appendChild(row);
      return { group, row };
    };

    const addButtons = (row, cmds, displayMap) => {
      if (!cmds || cmds.length === 0) return;
      cmds.forEach((cmd) => {
        const btn = document.createElement("button");
        btn.className = "btn-sm";
        const label = (displayMap && displayMap[cmd]) || cmd;
        btn.textContent = label;
        btn.addEventListener("click", () => safeSend(cmd));
        row.appendChild(btn);
      });
    };

    // movement：3x3布局的方向键
    const { group: moveGroup, row: moveRow } = createSection("移动");
    const displayMap = {
      north: "北",
      south: "南",
      east: "东",
      west: "西",
    };
    const allowed = new Set(available.movement || []);
    
    // 清空原有的btn-row内容，改为3x3网格
    moveRow.innerHTML = "";
    moveRow.style.display = "flex";
    moveRow.style.justifyContent = "center";
    
    // 创建3x3网格容器
    const dpadGrid = document.createElement("div");
    dpadGrid.className = "dpad-grid";
    
    // 只创建需要的5个按钮，使用CSS Grid定位
    // 北 (row 1, col 2)
    const btnNorth = document.createElement("button");
    btnNorth.textContent = displayMap.north;
    btnNorth.className = "dpad-direction-btn";
    btnNorth.style.gridRow = "1";
    btnNorth.style.gridColumn = "2";
    if (!allowed.has("north")) {
      btnNorth.disabled = true;
    } else {
      btnNorth.addEventListener("click", () => safeSend("north"));
    }
    dpadGrid.appendChild(btnNorth);
    
    // 西 (row 2, col 1)
    const btnWest = document.createElement("button");
    btnWest.textContent = displayMap.west;
    btnWest.className = "dpad-direction-btn";
    btnWest.style.gridRow = "2";
    btnWest.style.gridColumn = "1";
    if (!allowed.has("west")) {
      btnWest.disabled = true;
    } else {
      btnWest.addEventListener("click", () => safeSend("west"));
    }
    dpadGrid.appendChild(btnWest);
    
    // 中心 (row 2, col 2) - 观察按钮
    const btnCenter = document.createElement("button");
    btnCenter.textContent = "观察";
    btnCenter.className = "dpad-direction-btn";
    btnCenter.style.gridRow = "2";
    btnCenter.style.gridColumn = "2";
    btnCenter.addEventListener("click", () => safeSend("look"));
    dpadGrid.appendChild(btnCenter);
    
    // 东 (row 2, col 3)
    const btnEast = document.createElement("button");
    btnEast.textContent = displayMap.east;
    btnEast.className = "dpad-direction-btn";
    btnEast.style.gridRow = "2";
    btnEast.style.gridColumn = "3";
    if (!allowed.has("east")) {
      btnEast.disabled = true;
    } else {
      btnEast.addEventListener("click", () => safeSend("east"));
    }
    dpadGrid.appendChild(btnEast);
    
    // 南 (row 3, col 2)
    const btnSouth = document.createElement("button");
    btnSouth.textContent = displayMap.south;
    btnSouth.className = "dpad-direction-btn";
    btnSouth.style.gridRow = "3";
    btnSouth.style.gridColumn = "2";
    if (!allowed.has("south")) {
      btnSouth.disabled = true;
    } else {
      btnSouth.addEventListener("click", () => safeSend("south"));
    }
    dpadGrid.appendChild(btnSouth);
    
    // 将网格添加到移动组
    moveRow.appendChild(dpadGrid);
    commandsContainer.appendChild(moveGroup);

    // global
    if (available.global && available.global.length) {
      const { group, row } = createSection("基础");
      const displayMap = {
        look: "观察",
        stats: "属性",
        inventory: "物品栏",
        equipment: "装备",
        say: "说话",
        help: "帮助",
      };
      addButtons(row, available.global, displayMap);
      commandsContainer.appendChild(group);
    }

    // room-specific
    if (available.room && available.room.length) {
      const { group, row } = createSection("房间专属");
      addButtons(row, available.room);
      commandsContainer.appendChild(group);
    }

    // combat
    if (available.combat && available.combat.length) {
      const { group, row } = createSection("战斗");
      const displayMap = {
        attack: "攻击",
      };
      addButtons(row, available.combat, displayMap);
      commandsContainer.appendChild(group);
    }
  };

  const renderMiniMap = (currentRoom) => {
    if (!miniMapSvg) return;
    miniMapSvg.innerHTML = "";
    const svgNS = "http://www.w3.org/2000/svg";
    const scale = parseFloat((miniMapScale && miniMapScale.value) || "1") || 1;
    const baseSize = 200;
    miniMapSvg.setAttribute("width", baseSize * scale);
    miniMapSvg.setAttribute("height", baseSize * scale);
    miniMapSvg.style.width = `${baseSize * scale}px`;
    miniMapSvg.style.height = `${baseSize * scale}px`;

    // 画连线
    MAP_EDGES.forEach(([a, b]) => {
      const na = MAP_NODES[a];
      const nb = MAP_NODES[b];
      if (!na || !nb) return;
      const line = document.createElementNS(svgNS, "line");
      line.setAttribute("x1", na.x * scale);
      line.setAttribute("y1", na.y * scale);
      line.setAttribute("x2", nb.x * scale);
      line.setAttribute("y2", nb.y * scale);
      line.setAttribute("stroke", "#1f2937");
      line.setAttribute("stroke-width", "2");
      miniMapSvg.appendChild(line);
    });

    // 画节点
    Object.entries(MAP_NODES).forEach(([id, node]) => {
      const cx = node.x * scale;
      const cy = node.y * scale;
      const circle = document.createElementNS(svgNS, "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", currentRoom && currentRoom.id == id ? String(8 * scale) : String(6 * scale));
      circle.setAttribute("fill", currentRoom && currentRoom.id == id ? "#a855f7" : "#374151");
      circle.setAttribute("stroke", "#111827");
      circle.setAttribute("stroke-width", "2");
      miniMapSvg.appendChild(circle);

      const text = document.createElementNS(svgNS, "text");
      text.setAttribute("x", cx + 10 * scale);
      text.setAttribute("y", cy + 12 * scale); // 下移避免与节点重叠
      text.setAttribute("fill", "#d1d5db");
      text.setAttribute("font-size", String(9 * scale));
      text.textContent = node.name;
      miniMapSvg.appendChild(text);
    });
  };

  const updateCharacterPanel = (ch) => {
    lastCharacter = ch;
    if (!ch) {
      charName.textContent = "未加载角色";
      charLevel.textContent = "-";
      charExp.textContent = "-";
      charHpLabel.textContent = "-";
      charMpLabel.textContent = "-";
      charAtk.textContent = "-";
      charDef.textContent = "-";
      hpBar.style.width = "0%";
      mpBar.style.width = "0%";
      return;
    }
    charName.textContent = ch.name;
    charLevel.textContent = ch.level;
    charExp.textContent = ch.exp;
    charHpLabel.textContent = `${ch.hp} / ${ch.max_hp}`;
    charMpLabel.textContent = `${ch.mp} / ${ch.max_mp}`;
    charAtk.textContent = ch.attack;
    charDef.textContent = ch.defense;
    const hpPct = ch.max_hp ? Math.max(0, Math.min(100, (ch.hp / ch.max_hp) * 100)) : 0;
    const mpPct = ch.max_mp ? Math.max(0, Math.min(100, (ch.mp / ch.max_mp) * 100)) : 0;
    hpBar.style.width = hpPct + "%";
    mpBar.style.width = mpPct + "%";
  };

  const token = getToken();
  if (!token) {
    appendLog(
      "error",
      "未检测到登录 token，请先在登录页面完成登录后再进入游戏。"
    );
    userLabel.textContent = "未登录";
  } else {
    userLabel.textContent = "已登录";
  }

  const socket = new GameWebSocket({
    onOpen: () => {
      appendLog("system", "WebSocket 已连接。");
    },
    onClose: (ev) => {
      if (ev && ev.code) {
        appendLog("system", `连接已关闭 (code=${ev.code}).`);
      } else {
        appendLog("system", "连接已关闭。");
      }
    },
    onError: (err) => {
      console.error("WS error", err);
      connDot.classList.add("error");
      appendLog("error", "WebSocket 错误: " + (err.message || String(err)));
    },
    onMessage: (data) => {
      // 确保 data 是对象
      if (!data || typeof data !== "object") {
        appendLog("info", String(data));
        return;
      }

      const t = data.type || "info";

      if (t === "error") {
        appendLog("error", data.message || "发生错误。");
      } else if (t === "info") {
        appendLog("info", data.message || "");
      } else if (t === "room") {
        // 房间类信息，优先展示服务端提供的 message 文本
        const room = data.data && data.data.room ? data.data.room : null;
        let text = data.message || "";
        // 若服务端消息中已包含“出口:”，则不再重复拼接出口信息
        const hasExitsText = /出口\s*:/.test(text);
        if (!hasExitsText && room && room.exits) {
          const exits = Object.keys(room.exits);
          if (exits.length > 0) {
            text += `\n\n出口: ${exits.join(" / ")}`;
          }
        }
        appendLog("room", text.trim() || "你来到了一个新的地点。");
        if (room) {
          updateRoomInfo(room);
        }
      } else if (t === "combat") {
        appendLog("combat", data.message || "");
      } else if (data.message) {
        // 其它类型但有 message 的，直接展示 message
        appendLog("info", data.message);
      } else {
        // 兜底：避免输出一整段 JSON，只给出一个简短提示
        appendLog("info", "[收到一条系统消息]");
      }

      // 若消息中包含 room 数据（例如移动成功返回），也更新房间信息与小地图
      if (data.data && data.data.room) {
        updateRoomInfo(data.data.room);
      }

      // 若数据中包含 available_commands，则刷新右侧指令区
      if (data.data && data.data.available_commands) {
        renderCommands(data.data.available_commands);
      }

      if (data.character) {
        updateCharacterPanel(data.character);
      }
    },
    onStatusChange: (state) => {
      setConnState(state);
    },
  });

  const safeSend = (cmd) => {
    if (!cmd) return;
    try {
      socket.sendCommand(cmd);
      appendLog("system", `>> ${cmd}`);
    } catch (e) {
      appendLog("error", e.message || String(e));
    }
  };

  const connect = () => {
    const t = getToken();
    if (!t) {
      appendLog("error", "未检测到 token，请返回登录页重新登录。");
      userLabel.textContent = "未登录";
      return;
    }
    socket.connect(t);
  };

  connectBtn.addEventListener("click", connect);
  disconnectBtn.addEventListener("click", () => socket.disconnect());

  sendBtn.addEventListener("click", () => {
    const cmd = cmdInput.value.trim();
    if (cmd) {
      safeSend(cmd);
      cmdInput.value = "";
    }
  });

  cmdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const cmd = cmdInput.value.trim();
      if (cmd) {
        safeSend(cmd);
        cmdInput.value = "";
      }
    }
  });

  if (btnClearLog) {
    btnClearLog.addEventListener("click", () => {
      logEl.textContent = "";
    });
  }

  if (btnHelp) {
    btnHelp.addEventListener("click", () => safeSend("help"));
  }

  if (btnRefreshChar) {
    btnRefreshChar.addEventListener("click", async () => {
      const t = getToken();
      if (!t) {
        appendLog("error", "未检测到 token，无法刷新角色。");
        return;
      }
      try {
        const ch = await getCharacter(t);
        updateCharacterPanel(ch);
        appendLog("info", "已刷新角色数据。");
      } catch (err) {
        appendLog("error", "刷新角色失败: " + (err.message || String(err)));
      }
    });
  }

  // 迷你地图缩放控制
  if (miniMapScale) {
    miniMapScale.addEventListener("input", () => {
      renderMiniMap(lastRoom);
    });
  }

  // 显示/隐藏角色创建界面
  const showCharCreate = (show) => {
    if (charCreateBox) charCreateBox.style.display = show ? "block" : "none";
    if (charInfoBox) charInfoBox.style.display = show ? "none" : "block";
  };

  // 角色创建表单处理
  if (charCreateForm) {
    charCreateForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const t = getToken();
      if (!t) {
        if (charCreateMessage) {
          charCreateMessage.textContent = "未检测到 token，请先登录。";
          charCreateMessage.className = "err";
        }
        return;
      }
      const name = charNameInput ? charNameInput.value.trim() : "";
      if (!name) {
        if (charCreateMessage) {
          charCreateMessage.textContent = "请输入角色名。";
          charCreateMessage.className = "err";
        }
        return;
      }
      const submitBtn = charCreateForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;
      if (charCreateMessage) {
        charCreateMessage.textContent = "创建中...";
        charCreateMessage.className = "";
      }
      try {
        const ch = await createCharacter(name, t);
        updateCharacterPanel(ch);
        showCharCreate(false);
        appendLog("system", `角色 ${ch.name} 创建成功！点击上方"连接"按钮进入游戏。`);
        if (charCreateMessage) {
          charCreateMessage.textContent = "角色创建成功！";
          charCreateMessage.className = "ok";
        }
        if (charNameInput) charNameInput.value = "";
      } catch (err) {
        const errMsg = err.detail || err.message || String(err);
        appendLog("error", "创建角色失败: " + errMsg);
        if (charCreateMessage) {
          charCreateMessage.textContent = "创建失败: " + errMsg;
          charCreateMessage.className = "err";
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // 初次尝试读取角色信息，若不存在则提示先创建角色
  (async () => {
    const t = getToken();
    if (!t) {
      showCharCreate(false);
      return;
    }
    try {
      const ch = await getCharacter(t);
      updateCharacterPanel(ch);
      showCharCreate(false);
      appendLog(
        "system",
        `已加载角色 ${ch.name}，点击上方"连接"按钮进入游戏。`
      );
    } catch (err) {
      // 角色不存在，显示创建界面
      showCharCreate(true);
      appendLog(
        "info",
        "尚未创建角色，请在左侧面板创建角色后再进入游戏。"
      );
    }
  })();
}



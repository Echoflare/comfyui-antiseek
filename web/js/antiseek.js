import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "AntiSeek.Settings",
    async setup() {
        const style = document.createElement("style");
        style.textContent = `
            #antiseek-button {
                position: fixed;
                bottom: 10px;
                right: 140px;
                width: 30px;
                height: 30px;
                background: #222;
                border: 1px solid #444;
                border-radius: 50%;
                color: #ddd;
                font-size: 16px;
                cursor: pointer;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 0 5px rgba(0,0,0,0.5);
                transition: background 0.2s, border-color 0.2s;
                user-select: none;
                touch-action: none;
            }
            #antiseek-button:hover {
                background: #444;
                border-color: #666;
            }
            #antiseek-panel {
                position: fixed;
                width: 250px;
                background: #2b2b2b;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
                z-index: 9999;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                color: #ddd;
                display: none;
            }
            #antiseek-panel.visible {
                display: block;
            }
            .antiseek-form-group {
                margin-bottom: 12px;
            }
            .antiseek-label {
                display: block;
                font-size: 12px;
                margin-bottom: 4px;
                color: #aaa;
            }
            .antiseek-input {
                width: 100%;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
                color: #fff;
                padding: 6px;
                font-size: 13px;
                box-sizing: border-box;
            }
            .antiseek-input:focus {
                border-color: #666;
                outline: none;
            }
            .antiseek-btn {
                width: 100%;
                background: #3a3a3a;
                border: none;
                border-radius: 4px;
                color: #fff;
                padding: 8px;
                cursor: pointer;
                font-size: 13px;
                transition: background 0.2s;
            }
            .antiseek-btn:hover {
                background: #505050;
            }
            .antiseek-title {
                margin: 0 0 15px 0;
                font-size: 14px;
                font-weight: bold;
                border-bottom: 1px solid #444;
                padding-bottom: 8px;
            }
        `;
        document.head.appendChild(style);

        const btn = document.createElement("div");
        btn.id = "antiseek-button";
        btn.innerText = "🔒";
        btn.title = "Anti-Seek Settings";
        document.body.appendChild(btn);

        const panel = document.createElement("div");
        panel.id = "antiseek-panel";
        panel.innerHTML = `
            <div class="antiseek-title">Anti-Seek Settings</div>
            <div class="antiseek-form-group">
                <label class="antiseek-label">Security Salt / 安全加盐</label>
                <input type="text" id="antiseek-salt" class="antiseek-input" placeholder="留空则不加盐">
            </div>
            <div class="antiseek-form-group">
                <label class="antiseek-label">Metadata Key Name / 元数据键名</label>
                <input type="text" id="antiseek-key" class="antiseek-input" value="s_tag">
            </div>
            <button id="antiseek-save" class="antiseek-btn">保存配置 (Save)</button>
        `;
        document.body.appendChild(panel);

        const loadConfig = async () => {
            try {
                const res = await api.fetchApi("/antiseek/config");
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById("antiseek-salt").value = data.antiseek_salt || "";
                    document.getElementById("antiseek-key").value = data.antiseek_keyname || "s_tag";
                }
            } catch (e) {
                console.error("[Anti-Seek] Load config error:", e);
            }
        };

        let isDragging = false;
        let dragMoved = false;
        let startX, startY;
        let initialLeft, initialTop;

        const onDragStart = (e) => {
            isDragging = true;
            dragMoved = false;
            
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = btn.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;

            btn.style.bottom = "auto";
            btn.style.right = "auto";
            btn.style.left = initialLeft + "px";
            btn.style.top = initialTop + "px";

            window.addEventListener("pointermove", onDragMove);
            window.addEventListener("pointerup", onDragEnd);
            
            e.preventDefault();
        };

        const onDragMove = (e) => {
            if (!isDragging) return;

            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
                dragMoved = true;
            }

            btn.style.left = (initialLeft + dx) + "px";
            btn.style.top = (initialTop + dy) + "px";
        };

        const onDragEnd = (e) => {
            isDragging = false;
            window.removeEventListener("pointermove", onDragMove);
            window.removeEventListener("pointerup", onDragEnd);

            if (!dragMoved) {
                togglePanel();
            }
        };

        btn.addEventListener("pointerdown", onDragStart);

        function togglePanel() {
            const isVisible = panel.classList.contains("visible");
            if (!isVisible) {
                const btnRect = btn.getBoundingClientRect();
                const viewportHeight = window.innerHeight;
                
                let left = btnRect.left - 260;
                if (left < 10) left = btnRect.right + 10;
                panel.style.left = left + "px";

                if (btnRect.top > viewportHeight / 2) {
                    panel.style.top = "auto";
                    panel.style.bottom = (viewportHeight - btnRect.top + 10) + "px";
                } else {
                    panel.style.top = (btnRect.bottom + 10) + "px";
                    panel.style.bottom = "auto";
                }

                panel.classList.add("visible");
                loadConfig();
            } else {
                panel.classList.remove("visible");
            }
        }

        document.getElementById("antiseek-save").addEventListener("click", async () => {
            const salt = document.getElementById("antiseek-salt").value;
            const key = document.getElementById("antiseek-key").value;

            try {
                const res = await api.fetchApi("/antiseek/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        antiseek_salt: salt,
                        antiseek_keyname: key
                    })
                });
                
                if (res.ok) {
                    const saveBtn = document.getElementById("antiseek-save");
                    const originalText = saveBtn.innerText;
                    saveBtn.innerText = "已保存 ✓";
                    saveBtn.style.background = "#2a5a2a";
                    setTimeout(() => {
                        saveBtn.innerText = originalText;
                        saveBtn.style.background = "#3a3a3a";
                        panel.classList.remove("visible");
                    }, 1000);
                } else {
                    alert("保存失败");
                }
            } catch (e) {
                console.error("[Anti-Seek] Save config error:", e);
                alert("保存出错: " + e);
            }
        });

        document.addEventListener("pointerdown", (e) => {
            if (!panel.contains(e.target) && !btn.contains(e.target) && panel.classList.contains("visible")) {
                panel.classList.remove("visible");
            }
        });
    }
});
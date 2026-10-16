/* =========================================================
   CRUNCH & CRAVE — ADMIN ANIMATIONS
========================================================= */

(function () {

    "use strict";

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;


    /* Greeting by time of day */

    const greeting = document.querySelector("[data-greeting]");
    if (greeting) {
        const hour = new Date().getHours();
        greeting.textContent =
            hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
    }


    /* Count-up numbers on the dashboard */

    function countUp(el) {
        const target = Number(el.dataset.count) || 0;
        if (reduceMotion || target === 0) {
            el.textContent = target.toLocaleString("en-US");
            return;
        }

        const duration = 1400;
        const start = performance.now();

        function frame(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            el.textContent = Math.round(target * eased).toLocaleString("en-US");
            if (progress < 1) requestAnimationFrame(frame);
        }

        el.textContent = "0";
        requestAnimationFrame(frame);
    }

    document.querySelectorAll("[data-count]").forEach((el, index) => {
        setTimeout(() => countUp(el), 200 + index * 90);
    });


    /* Rows of list pages slide in one after another */

    document.querySelectorAll("#result_list tbody tr").forEach((row, index) => {
        if (index > 30) return;
        row.style.setProperty("--i", index);
        row.classList.add("nja-row-in");
    });


    /* Live new-order alerts (sound + pop-up + browser notification) */

    const FEED_URL = "/staff/order-feed/";
    const STORE_KEY = "nja-last-order-id";
    const POLL_MS = 20000;
    let audioCtx = null;

    const store = {
        get() {
            try { return Number(localStorage.getItem(STORE_KEY)) || 0; } catch (e) { return 0; }
        },
        set(id) {
            try { localStorage.setItem(STORE_KEY, String(id)); } catch (e) { /* private mode */ }
        },
    };

    function chime() {
        if (!audioCtx) return;
        const now = audioCtx.currentTime;
        [880, 1175, 1568].forEach((freq, i) => {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = "sine";
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.0001, now + i * 0.14);
            gain.gain.exponentialRampToValueAtTime(0.25, now + i * 0.14 + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.14 + 0.5);
            osc.connect(gain).connect(audioCtx.destination);
            osc.start(now + i * 0.14);
            osc.stop(now + i * 0.14 + 0.55);
        });
    }

    // Browsers only allow sound after the user has clicked once.
    document.addEventListener("pointerdown", () => {
        if (!audioCtx && window.AudioContext) audioCtx = new AudioContext();
        if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
    });

    function alertBox(order) {
        let stack = document.querySelector(".nja-alerts");
        if (!stack) {
            stack = document.createElement("div");
            stack.className = "nja-alerts";
            stack.setAttribute("aria-live", "assertive");
            document.body.appendChild(stack);
        }
        const box = document.createElement("a");
        box.className = "nja-alert";
        box.href = order.url;
        box.innerHTML = '<span class="nja-alert-icon"><i class="fa-solid fa-bell"></i></span>' +
            '<span class="nja-alert-text"><strong></strong><small></small></span>' +
            '<i class="fa-solid fa-xmark nja-alert-close" title="Dismiss"></i>';
        box.querySelector("strong").textContent = `New order #${order.number}`;
        box.querySelector("small").textContent = `${order.name} · Rs. ${order.total.toLocaleString("en-US")}`;
        box.querySelector(".nja-alert-close").addEventListener("click", (event) => {
            event.preventDefault();
            box.remove();
        });
        stack.appendChild(box);
    }

    async function pollOrders() {
        try {
            const last = store.get();
            const response = await fetch(`${FEED_URL}?after=${last}`, { credentials: "same-origin" });
            if (!response.ok) return;
            const data = await response.json();

            document.querySelectorAll("[data-active-orders]").forEach((el) => {
                el.textContent = data.active;
                el.hidden = !data.active;
            });

            if (!last) {
                store.set(data.latest_id);  // first visit: start watching from now
                return;
            }
            if (!data.orders.length) return;

            store.set(data.latest_id);
            chime();
            data.orders.forEach((order) => {
                alertBox(order);
                if ("Notification" in window && Notification.permission === "granted") {
                    const note = new Notification(`🍔 New order #${order.number}`, {
                        body: `${order.name} · Rs. ${order.total.toLocaleString("en-US")}`,
                        tag: `order-${order.id}`,
                    });
                    note.onclick = () => { window.focus(); window.location.href = order.url; };
                }
            });
            document.title = `(${data.orders.length}) New order! · Crunch & Crave Admin`;
        } catch (error) {
            /* offline or logged out — try again next tick */
        }
    }

    if (document.body.dataset.adminUtcOffset !== undefined && !document.body.classList.contains("login")) {
        pollOrders();
        setInterval(pollOrders, POLL_MS);

        const enable = document.querySelector("[data-enable-alerts]");
        if (enable && "Notification" in window) {
            const refresh = () => {
                enable.classList.toggle("is-on", Notification.permission === "granted");
                enable.title = Notification.permission === "granted"
                    ? "Desktop alerts are on"
                    : "Turn on desktop alerts for new orders";
            };
            refresh();
            enable.addEventListener("click", async () => {
                await Notification.requestPermission();
                refresh();
                chime();
            });
        } else if (enable) {
            enable.hidden = true;
        }
    }


    /* Cards follow the cursor with a soft spotlight */

    if (!reduceMotion && window.matchMedia("(pointer: fine)").matches) {
        document.querySelectorAll(".nja-kpi, .nja-card, .nja-tile").forEach((card) => {
            card.addEventListener("pointermove", (event) => {
                const rect = card.getBoundingClientRect();
                card.style.backgroundImage =
                    `radial-gradient(400px circle at ${event.clientX - rect.left}px ${event.clientY - rect.top}px, rgba(139, 92, 246, 0.10), transparent 60%)`;
            });
            card.addEventListener("pointerleave", () => {
                card.style.backgroundImage = "";
            });
        });
    }

})();

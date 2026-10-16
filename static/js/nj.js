/* =========================================================
   CRUNCH & CRAVE — SITE SCRIPT
   One script for the whole site. Every feature checks
   for its elements first, so it is safe on every page.
========================================================= */

(function () {

    "use strict";

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

    const URLS = {
        add: "/cart/add/",
        update: "/cart/update/",
        remove: (slug) => `/cart/remove/${encodeURIComponent(slug)}/`,
        clear: "/cart/clear/",
        promo: "/cart/promo/",
        cart: "/cart/",
    };

    const money = (value) => "Rs. " + Number(value || 0).toLocaleString("en-US");


    /* =====================================================
       TOASTS
    ===================================================== */

    const toastStack = $("#toasts");

    function toast(message, type = "success", link = null) {
        if (!toastStack) return;

        const icons = {
            success: "fa-circle-check",
            error: "fa-circle-exclamation",
            info: "fa-bell",
            warning: "fa-circle-exclamation",
        };

        const el = document.createElement("div");
        el.className = `toast ${type}`;
        el.setAttribute("role", "status");
        el.innerHTML = `<span class="t-icon"><i class="fa-solid ${icons[type] || icons.info}"></i></span><span></span>`;
        el.children[1].textContent = message;

        if (link) {
            const a = document.createElement("a");
            a.href = link.href;
            a.textContent = link.label;
            el.appendChild(a);
        }

        toastStack.appendChild(el);
        dismissLater(el);
    }

    function dismissLater(el, delay = 3800) {
        setTimeout(() => {
            el.classList.add("is-leaving");
            el.addEventListener("animationend", () => el.remove(), { once: true });
        }, delay);
    }

    // Server-rendered Django messages
    $$(".toast", toastStack || document).forEach((el, i) => dismissLater(el, 4500 + i * 400));


    /* =====================================================
       HEADER, NAV, SEARCH, TO-TOP
    ===================================================== */

    const header = $("#header");
    const toTop = $("#toTop");

    function onScroll() {
        const y = window.scrollY;
        if (header) header.classList.toggle("is-scrolled", y > 20);
        if (toTop) toTop.classList.toggle("is-visible", y > 700);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (toTop) {
        toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    }

    const nav = $("#nav");
    const navToggle = $("#navToggle");

    function setNav(open) {
        if (!nav || !navToggle) return;
        nav.classList.toggle("is-open", open);
        navToggle.classList.toggle("is-open", open);
        navToggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("no-scroll", open);
    }

    if (navToggle) {
        navToggle.addEventListener("click", () => setNav(!nav.classList.contains("is-open")));
        const backdrop = $(".nav-backdrop");
        if (backdrop) backdrop.addEventListener("click", () => setNav(false));
    }

    // Highlight the current page
    const path = window.location.pathname;
    $$("#nav a[data-nav]").forEach((link) => {
        const href = link.getAttribute("href");
        if (href === path || (href !== "/" && path.startsWith(href))) {
            link.classList.add("is-active");
            link.setAttribute("aria-current", "page");
        }
    });

    const search = $("#search");

    function setSearch(open) {
        if (!search) return;
        search.classList.toggle("is-open", open);
        search.setAttribute("aria-hidden", String(!open));
        document.body.classList.toggle("no-scroll", open);
        if (open) setTimeout(() => $("input", search).focus(), 150);
    }

    $$("[data-search-open]").forEach((btn) => btn.addEventListener("click", () => {
        setNav(false);
        setSearch(true);
    }));
    $$("[data-search-close]").forEach((btn) => btn.addEventListener("click", () => setSearch(false)));

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setSearch(false);
            setNav(false);
            closeLightbox();
        }
    });


    /* =====================================================
       REVEAL ON SCROLL
    ===================================================== */

    const revealItems = $$("[data-reveal]");

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-in");
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

        revealItems.forEach((el) => observer.observe(el));
    } else {
        revealItems.forEach((el) => el.classList.add("is-in"));
    }


    /* =====================================================
       SERVER REQUESTS
    ===================================================== */

    function csrfToken() {
        const meta = $('meta[name="csrf-token"]');
        return meta ? meta.content : "";
    }

    async function post(url, data = {}) {
        const body = new FormData();
        Object.entries(data).forEach(([key, value]) => body.append(key, value));

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken(),
                "X-Requested-With": "XMLHttpRequest",
            },
            body,
            credentials: "same-origin",
        });

        let json = {};
        try {
            json = await response.json();
        } catch (error) {
            json = { success: false, message: "Something went wrong. Please try again." };
        }
        return json;
    }


    /* =====================================================
       CART UI
    ===================================================== */

    function setCartCount(count) {
        $$("[data-cart-count]").forEach((badge) => {
            badge.textContent = count;
            badge.dataset.count = count;
            badge.classList.remove("is-bump");
            void badge.offsetWidth;
            badge.classList.add("is-bump");
        });
    }

    function renderSummary(data) {
        const set = (key, value) => $$(`[data-summary="${key}"]`).forEach((el) => {
            el.textContent = value;
        });

        set("subtotal", money(data.subtotal));
        set("delivery", data.delivery_fee === 0 ? "FREE" : money(data.delivery_fee));
        set("discount", "− " + money(data.discount));
        set("total", money(data.total));
        set("count", data.cart_count);
        set("remaining", money(data.free_delivery_remaining));

        $$("[data-summary-row='discount']").forEach((row) => {
            row.hidden = !data.discount;
        });
        $$("[data-summary='promo-code']").forEach((el) => {
            el.textContent = data.promo || "";
        });

        const bar = $("[data-summary='progress']");
        if (bar) bar.style.width = data.free_delivery_progress + "%";

        const freeMsg = $("[data-free-msg]");
        const freeDone = $("[data-free-done]");
        if (freeMsg && freeDone) {
            freeMsg.hidden = data.free_delivery_remaining === 0;
            freeDone.hidden = data.free_delivery_remaining !== 0;
        }

        Object.entries(data.lines || {}).forEach(([slug, line]) => {
            const row = $(`.cart-line[data-slug="${CSS.escape(slug)}"]`);
            if (!row) return;
            $("[data-line-total]", row).textContent = money(line.total);
            const qty = $("[data-qty-value]", row);
            if (qty) qty.value = line.quantity;
        });
    }

    function handleCart(data) {
        if (typeof data.cart_count !== "undefined") setCartCount(data.cart_count);
        if ($(".cart-lines") || $(".summary")) renderSummary(data);
    }


    /* =====================================================
       QUANTITY STEPPERS
    ===================================================== */

    document.addEventListener("click", (event) => {
        const step = event.target.closest("[data-qty-step]");
        if (!step) return;

        const wrap = step.closest("[data-qty]");
        const input = $("[data-qty-value]", wrap);
        const next = Math.max(1, Math.min(20, Number(input.value || 1) + Number(step.dataset.qtyStep)));

        if (next === Number(input.value)) {
            if (next === 20) toast("Maximum quantity is 20.", "info");
            return;
        }

        input.value = next;
        input.dispatchEvent(new Event("change", { bubbles: true }));
    });


    /* =====================================================
       MOTION HELPERS
    ===================================================== */

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // The dish image flies into the cart icon
    function flyToCart(button) {
        const cartIcon = $(".cart-btn");
        const card = button.closest(".p-card, .pd-grid, .banner");
        const img = card ? $("img", card) : null;
        if (reduceMotion || !cartIcon || !img) return;

        const from = img.getBoundingClientRect();
        const to = cartIcon.getBoundingClientRect();
        const size = Math.min(from.width, from.height, 140);

        const ghost = img.cloneNode();
        ghost.className = "fly-ghost";
        Object.assign(ghost.style, {
            left: `${from.left + from.width / 2 - size / 2}px`,
            top: `${from.top + from.height / 2 - size / 2}px`,
            width: `${size}px`,
            height: `${size}px`,
        });
        document.body.appendChild(ghost);

        const dx = to.left + to.width / 2 - (from.left + from.width / 2);
        const dy = to.top + to.height / 2 - (from.top + from.height / 2);

        ghost.animate([
            { transform: "translate(0, 0) scale(1)", opacity: 1 },
            { transform: `translate(${dx * 0.55}px, ${dy * 0.55 - 80}px) scale(0.6)`, opacity: 0.95, offset: 0.55 },
            { transform: `translate(${dx}px, ${dy}px) scale(0.12)`, opacity: 0.4 },
        ], { duration: 850, easing: "cubic-bezier(0.5, 0, 0.3, 1)" }).onfinish = () => {
            ghost.remove();
            cartIcon.animate(
                [{ transform: "scale(1)" }, { transform: "scale(1.25) rotate(-8deg)" }, { transform: "scale(1)" }],
                { duration: 450, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }
            );
        };
    }

    // Ripple on button press
    document.addEventListener("pointerdown", (event) => {
        const button = event.target.closest(".btn, .add-btn, .chip");
        if (!button || reduceMotion) return;
        const rect = button.getBoundingClientRect();
        const ripple = document.createElement("span");
        const size = Math.max(rect.width, rect.height) * 2;
        ripple.className = "ripple";
        Object.assign(ripple.style, {
            width: `${size}px`,
            height: `${size}px`,
            left: `${event.clientX - rect.left - size / 2}px`,
            top: `${event.clientY - rect.top - size / 2}px`,
        });
        button.appendChild(ripple);
        ripple.addEventListener("animationend", () => ripple.remove());
    });

    // Numbers count up when they scroll into view
    const counters = $$("[data-count-up]");
    if (counters.length && "IntersectionObserver" in window) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                counterObserver.unobserve(entry.target);
                const el = entry.target;
                const target = parseFloat(el.dataset.countUp);
                const decimals = (el.dataset.countUp.split(".")[1] || "").length;
                if (reduceMotion || !target) return;
                const start = performance.now();
                const tick = (now) => {
                    const p = Math.min((now - start) / 1300, 1);
                    el.textContent = (target * (1 - Math.pow(1 - p, 4))).toFixed(decimals);
                    if (p < 1) requestAnimationFrame(tick);
                };
                requestAnimationFrame(tick);
            });
        }, { threshold: 0.6 });
        counters.forEach((el) => counterObserver.observe(el));
    }

    // Hero burger follows the mouse
    const heroVisual = $(".hero-visual");
    if (heroVisual && !reduceMotion && window.matchMedia("(pointer: fine)").matches) {
        const hero = heroVisual.closest(".hero");
        hero.addEventListener("pointermove", (event) => {
            const x = event.clientX / window.innerWidth - 0.5;
            const y = event.clientY / window.innerHeight - 0.5;
            heroVisual.style.transform = `translate3d(${x * -18}px, ${y * -18}px, 0) rotateY(${x * 6}deg) rotateX(${y * -6}deg)`;
        });
        hero.addEventListener("pointerleave", () => {
            heroVisual.style.transform = "";
        });
    }


    /* =====================================================
       ADD TO CART (any page)
    ===================================================== */

    document.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-add]");
        if (!button) return;
        event.preventDefault();

        const source = button.dataset.qtySource ? $(button.dataset.qtySource) : null;
        const quantity = source ? source.value : 1;
        const label = button.querySelector("[data-label]");
        const original = label ? label.textContent : "";

        button.classList.add("is-loading");

        const data = await post(URLS.add, { product: button.dataset.add, quantity });

        button.classList.remove("is-loading");

        if (data.success) {
            handleCart(data);
            if ($(".cart-lines")) {
                // New line on the cart page — re-render it from the server.
                window.location.reload();
                return;
            }
            flyToCart(button);
            toast(data.message, "success", { href: URLS.cart, label: "View cart" });
            button.classList.add("is-added");
            if (label) label.textContent = "Added";
            setTimeout(() => {
                button.classList.remove("is-added");
                if (label) label.textContent = original;
            }, 1600);
        } else {
            toast(data.message || "Could not add item.", "error");
        }
    });


    /* =====================================================
       CART PAGE
    ===================================================== */

    const cartLines = $(".cart-lines");

    if (cartLines) {

        cartLines.addEventListener("change", async (event) => {
            const input = event.target.closest("[data-qty-value]");
            if (!input) return;

            const row = input.closest(".cart-line");
            const data = await post(URLS.update, { product: row.dataset.slug, quantity: input.value });

            if (data.success) handleCart(data);
            else toast(data.message, "error");
        });

        cartLines.addEventListener("click", async (event) => {
            const button = event.target.closest("[data-remove]");
            if (!button) return;

            const row = button.closest(".cart-line");
            row.classList.add("is-removing");

            const data = await post(URLS.remove(row.dataset.slug));

            if (data.success) {
                handleCart(data);
                setTimeout(() => {
                    row.remove();
                    if (!$(".cart-line")) window.location.reload();
                }, 380);
                toast("Item removed from cart.", "info");
            } else {
                row.classList.remove("is-removing");
                toast(data.message, "error");
            }
        });
    }

    const clearBtn = $("#clearCart");

    if (clearBtn) {
        clearBtn.addEventListener("click", async () => {
            if (!window.confirm("Remove all items from your cart?")) return;
            const data = await post(URLS.clear);
            if (data.success) window.location.reload();
        });
    }

    const promoForm = $("#promoForm");

    if (promoForm) {
        promoForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const input = $("input", promoForm);
            const button = $("button", promoForm);

            button.classList.add("is-loading");
            const data = await post(URLS.promo, { code: input.value });
            button.classList.remove("is-loading");

            handleCart(data);
            toast(data.message, data.success ? "success" : "error");
        });
    }


    /* =====================================================
       FILTERABLE GRIDS (menu + gallery)
    ===================================================== */

    $$("[data-filter-scope]").forEach((scope) => {

        const chips = $$("[data-filter]", scope);
        const searchInput = $("[data-filter-search]", scope);
        const items = $$("[data-item]", scope);
        const groups = $$("[data-group]", scope);
        const empty = $("[data-empty]", scope);
        let active = scope.dataset.initial || "all";

        function apply() {
            const term = searchInput ? searchInput.value.trim().toLowerCase() : "";
            let visible = 0;

            items.forEach((item) => {
                const matchCategory = active === "all" || item.dataset.category === active;
                const matchTerm = !term || item.dataset.search.includes(term);
                const show = matchCategory && matchTerm;
                item.classList.toggle("is-hidden", !show);
                if (show) visible++;
            });

            groups.forEach((group) => {
                group.classList.toggle("is-hidden", !$("[data-item]:not(.is-hidden)", group));
            });

            chips.forEach((chip) => {
                const on = chip.dataset.filter === active;
                chip.classList.toggle("is-active", on);
                chip.setAttribute("aria-pressed", String(on));
            });

            if (empty) empty.hidden = visible > 0;
        }

        chips.forEach((chip) => chip.addEventListener("click", () => {
            active = chip.dataset.filter;
            apply();
            const url = new URL(window.location);
            if (active === "all") url.searchParams.delete("category");
            else url.searchParams.set("category", active);
            history.replaceState(null, "", url);
        }));

        if (searchInput) searchInput.addEventListener("input", apply);

        apply();
    });


    /* =====================================================
       LIGHTBOX (gallery)
    ===================================================== */

    const lightbox = $("#lightbox");
    let lbIndex = 0;

    function visibleGalleryItems() {
        return $$(".g-item:not(.is-hidden)");
    }

    function showLightbox(index) {
        const items = visibleGalleryItems();
        if (!lightbox || !items.length) return;

        lbIndex = (index + items.length) % items.length;
        const item = items[lbIndex];

        $("img", lightbox).src = item.dataset.full;
        $("img", lightbox).alt = item.dataset.title;
        $("[data-lb-title]", lightbox).textContent = item.dataset.title;
        $("[data-lb-link]", lightbox).href = item.dataset.link;

        lightbox.classList.add("is-open");
        lightbox.setAttribute("aria-hidden", "false");
        document.body.classList.add("no-scroll");
    }

    function closeLightbox() {
        if (!lightbox || !lightbox.classList.contains("is-open")) return;
        lightbox.classList.remove("is-open");
        lightbox.setAttribute("aria-hidden", "true");
        document.body.classList.remove("no-scroll");
    }

    if (lightbox) {
        document.addEventListener("click", (event) => {
            const item = event.target.closest(".g-item");
            if (item) showLightbox(visibleGalleryItems().indexOf(item));
        });

        $(".lb-close", lightbox).addEventListener("click", closeLightbox);
        $(".lb-prev", lightbox).addEventListener("click", () => showLightbox(lbIndex - 1));
        $(".lb-next", lightbox).addEventListener("click", () => showLightbox(lbIndex + 1));
        lightbox.addEventListener("click", (event) => {
            if (event.target === lightbox) closeLightbox();
        });

        document.addEventListener("keydown", (event) => {
            const item = event.target.closest && event.target.closest(".g-item");
            if (item && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                showLightbox(visibleGalleryItems().indexOf(item));
                return;
            }
            if (!lightbox.classList.contains("is-open")) return;
            if (event.key === "ArrowLeft") showLightbox(lbIndex - 1);
            if (event.key === "ArrowRight") showLightbox(lbIndex + 1);
        });
    }


    /* =====================================================
       FORMS: char counters, phone filter, submit state
    ===================================================== */

    $$("[data-counter]").forEach((field) => {
        const out = $(field.dataset.counter);
        const update = () => {
            out.textContent = field.value.length;
        };
        field.addEventListener("input", update);
        update();
    });

    $$("input[type='tel']").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = input.value.replace(/[^0-9+\-\s]/g, "");
        });
    });

    // Checkout: show account details + transaction ID only for online payments
    const payOptions = $("[data-pay-options]");
    const payDetails = $("[data-pay-details]");
    if (payOptions && payDetails) {
        payOptions.addEventListener("change", (event) => {
            const method = event.target.value;
            payDetails.hidden = method === "cod";
            $$("[data-pay-account]", payDetails).forEach((account) => {
                account.hidden = account.dataset.payAccount !== method;
            });
            if (method !== "cod") $("input", payDetails.querySelector(".field")).focus();
        });
    }

    // Tap an account number to copy it
    document.addEventListener("click", async (event) => {
        const el = event.target.closest("[data-copy]");
        if (!el) return;
        try {
            await navigator.clipboard.writeText(el.dataset.copy.replace(/\s/g, ""));
            toast("Account number copied.", "success");
        } catch (error) {
            toast("Couldn't copy — please note it down.", "info");
        }
    });

    $$("form[data-loading]").forEach((form) => {
        form.addEventListener("submit", () => {
            const button = $("button[type='submit']", form) || $(`button[form="${form.id}"]`);
            if (button) button.classList.add("is-loading");
        });
    });

})();

import { SITE_CONFIG } from "./site-config.js";

// Conditionally load Popover polyfill ONLY when native support is missing
if (!Object.hasOwn(HTMLElement.prototype, "popover")) {
  import("https://unpkg.com/@oddbird/popover-polyfill@latest/dist/popover.min.js").catch(() => {});
}

// ============================================================================
// Responsive Navbar: switches between popover (narrow) and inline (wide)
// ============================================================================

const header = document.querySelector(".site-header");
const headerInner = document.querySelector(".header-inner");
const siteMenu = document.getElementById("site-menu");

if (header && headerInner && siteMenu) {
  let lastHeaderWidth = 0;

  const updateNavLayout = () => {
    const currentWidth = header.getBoundingClientRect().width;
    const isCurrentlyWide = header.classList.contains("is-wide");

    // While collapsed, only remeasure when the header grows to avoid layout thrash
    if (!isCurrentlyWide && currentWidth <= lastHeaderWidth && lastHeaderWidth > 0) {
      return;
    }
    lastHeaderWidth = currentWidth;

    const wasOpen =
      !isCurrentlyWide &&
      (siteMenu.matches(":popover-open") || siteMenu.classList.contains(":popover-open"));

    header.classList.add("is-measuring");
    header.classList.add("is-wide");
    siteMenu.removeAttribute("popover");

    const fitsInline = headerInner.scrollWidth <= headerInner.clientWidth + 1;

    if (fitsInline) {
      header.classList.add("is-wide");
      siteMenu.removeAttribute("popover");
    } else {
      header.classList.remove("is-wide");
      siteMenu.setAttribute("popover", "auto");
      if (wasOpen && typeof siteMenu.showPopover === "function") {
        try {
          siteMenu.showPopover();
        } catch {
          // Ignore if already open or polyfill still initializing
        }
      }
    }

    requestAnimationFrame(() => {
      header.classList.remove("is-measuring");
    });
  };

  // Close mobile popover when a same-page hash link is chosen
  siteMenu.addEventListener("click", (event) => {
    const link = event.target.closest("a[href^='#']");
    if (link && !header.classList.contains("is-wide") && typeof siteMenu.hidePopover === "function") {
      try {
        siteMenu.hidePopover();
      } catch {
        // Ignore if already closed
      }
    }
  });

  if (typeof ResizeObserver === "function") {
    const ro = new ResizeObserver(() => updateNavLayout());
    ro.observe(header);
    ro.observe(siteMenu);
  } else {
    window.addEventListener("resize", updateNavLayout);
  }

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(updateNavLayout);
  }
  updateNavLayout();
}

// ============================================================================
// Native <dialog> Lightbox & Shop Info Modal + Safari closedby="any" fallback
// ============================================================================

const lightboxDialog = document.getElementById("lightbox-dialog");
const lightboxTitle = document.getElementById("lightbox-title");
const lightboxImg = document.getElementById("lightbox-img");
const lightboxCaption = document.getElementById("lightbox-caption");

if (lightboxDialog && lightboxTitle && lightboxImg && lightboxCaption) {
  for (const trigger of document.querySelectorAll("[data-lightbox-src]")) {
    trigger.addEventListener("click", () => {
      const src = trigger.getAttribute("data-lightbox-src") || "";
      const title = trigger.getAttribute("data-lightbox-title") || "Photo Preview";
      const caption = trigger.getAttribute("data-lightbox-caption") || "";
      const thumbImg = trigger.querySelector("img");

      lightboxTitle.textContent = title;
      lightboxImg.src = src;
      lightboxImg.alt = thumbImg ? thumbImg.alt : title;
      lightboxCaption.textContent = caption;

      lightboxDialog.showModal();
    });
  }

  lightboxDialog.addEventListener("close", () => {
    lightboxDialog.returnValue = "";
  });
}

const shopDialog = document.getElementById("shop-dialog");
if (shopDialog) {
  for (const btnId of ["open-shop-hero", "open-shop-card"]) {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener("click", () => shopDialog.showModal());
    }
  }

  shopDialog.addEventListener("close", () => {
    shopDialog.returnValue = "";
  });
}

// Fallback for browsers without <dialog closedby="any"> (e.g. Safari)
if (!("closedBy" in HTMLDialogElement.prototype)) {
  const isOutsideDialog = (event, dialog) => {
    const rect = dialog.getBoundingClientRect();
    return (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    );
  };

  for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {
    let pressedOutside = false;
    dialog.addEventListener("pointerdown", (event) => {
      pressedOutside = isOutsideDialog(event, dialog);
    });
    dialog.addEventListener("pointerup", (event) => {
      if (pressedOutside && isOutsideDialog(event, dialog)) {
        dialog.close();
      }
      pressedOutside = false;
    });
  }
}

// ============================================================================
// Mailing List Forms (Google Sheets via Apps Script + Accessible Validation)
// ============================================================================

const mailingForms = [...document.querySelectorAll("[data-mailing-form]")];

if (mailingForms.length > 0) {
  const endpoint = (SITE_CONFIG?.mailingList?.endpoint || "").trim();
  const supportsUserInvalid =
    typeof CSS !== "undefined" &&
    typeof CSS.supports === "function" &&
    CSS.supports("selector(:user-invalid)");

  // Link each field's error message in aria-describedby only while it is shown
  const linkError = (el, shown) => {
    const errorId = el.dataset.error;
    if (!errorId) return;
    const ids = (el.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter((id) => id && id !== errorId);
    if (shown) ids.push(errorId);
    if (ids.length) el.setAttribute("aria-describedby", ids.join(" "));
    else el.removeAttribute("aria-describedby");
  };

  // Single polite live region for announcing blur/change validation errors
  const announcer = document.createElement("div");
  announcer.setAttribute("aria-live", "polite");
  announcer.classList.add("visually-hidden");
  document.body.append(announcer);

  let announceTimer;
  let announcedField;

  const spokenText = (node) => {
    const copy = node.cloneNode(true);
    copy.querySelectorAll('[aria-hidden="true"]').forEach((n) => n.remove());
    copy
      .querySelectorAll('[role="img"][aria-label]')
      .forEach((n) => n.replaceWith(`${n.getAttribute("aria-label")}: `));
    return copy.textContent.replace(/\s+/g, " ").trim();
  };

  const announceError = (el) => {
    const error = el.dataset.error ? document.getElementById(el.dataset.error) : null;
    if (!error) return;
    const label = el.labels?.[0] ? `${spokenText(el.labels[0])}: ` : "";
    clearTimeout(announceTimer);
    announcer.textContent = "";
    announcedField = el;
    announceTimer = setTimeout(() => {
      announcer.textContent = label + spokenText(error);
    }, 500);
  };

  const flagged = new WeakSet();
  const announced = new WeakSet();
  const dirtyState = new WeakMap();

  const isFieldUserInvalid = (el) => {
    if (supportsUserInvalid) {
      return el.matches(":user-invalid");
    }
    return el.classList.contains("user-invalid-fallback");
  };

  const syncAria = (el, announce = false) => {
    if (!el.matches?.("input, select, textarea")) return;
    const invalid = isFieldUserInvalid(el);
    if (invalid) {
      if (announce && !announced.has(el)) {
        announceError(el);
        announced.add(el);
      }
      el.setAttribute("aria-invalid", "true");
      linkError(el, true);
      flagged.add(el);
    } else if (flagged.has(el) || el.getAttribute("aria-invalid") !== "true") {
      el.setAttribute("aria-invalid", "false");
      linkError(el, false);
      flagged.delete(el);
      announced.delete(el);
      if (announcedField === el) {
        clearTimeout(announceTimer);
        announcer.textContent = "";
      }
    }
  };

  const updateFallbackState = (el) => {
    if (supportsUserInvalid || !el.validity) return;
    const isValid = el.validity.valid;
    el.classList.toggle("user-invalid-fallback", !isValid);
    el.classList.toggle("user-valid-fallback", isValid);
  };

  const setStatus = (statusEl, kind, text) => {
    if (!statusEl) return;
    statusEl.className = `form-status${kind ? ` is-${kind}` : ""}`;
    statusEl.textContent = text;
  };

  const prefillEmail = new URLSearchParams(window.location.search).get("email");

  for (const form of mailingForms) {
    const formAction = (form.dataset.formAction || "subscribe").toLowerCase();
    const isUnsubscribe = formAction === "unsubscribe";

    if (endpoint) {
      form.setAttribute("action", endpoint);
    }

    if (isUnsubscribe && prefillEmail) {
      const emailInput = form.querySelector('input[type="email"]');
      if (emailInput && !emailInput.value) {
        emailInput.value = prefillEmail.trim();
      }
    }

    const fields = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
    for (const field of fields) {
      if (field.closest(".honeypot-field")) continue;
      field.setAttribute("aria-invalid", "false");
    }

    form.addEventListener(
      "blur",
      (event) => {
        const el = event.target;
        if (!el.matches?.("input, select, textarea") || el.closest(".honeypot-field")) return;
        if (!supportsUserInvalid) {
          const state = dirtyState.get(el) || { hasInteracted: false, hasBlurred: false };
          state.hasBlurred = true;
          dirtyState.set(el, state);
          if (state.hasInteracted) updateFallbackState(el);
        }
        syncAria(el, true);
      },
      true
    );

    form.addEventListener("input", (event) => {
      const el = event.target;
      if (!el.matches?.("input, select, textarea") || el.closest(".honeypot-field")) return;
      if (!supportsUserInvalid) {
        const state = dirtyState.get(el) || { hasInteracted: false, hasBlurred: false };
        state.hasInteracted = true;
        dirtyState.set(el, state);
        if (state.hasBlurred) updateFallbackState(el);
      }
      if (el.hasAttribute("aria-invalid")) {
        syncAria(el, false);
      }
    });

    form.addEventListener(
      "invalid",
      (event) => {
        const el = event.target;
        if (!supportsUserInvalid) {
          dirtyState.set(el, { hasInteracted: true, hasBlurred: true });
          updateFallbackState(el);
        }
        announced.add(el);
        syncAria(el, false);
      },
      true
    );

    form.addEventListener("reset", () => {
      setTimeout(() => {
        for (const el of form.elements) {
          dirtyState.delete(el);
          el.classList?.remove("user-invalid-fallback", "user-valid-fallback");
          if (el.matches?.("input, select, textarea") && !el.closest(".honeypot-field")) {
            syncAria(el, false);
          }
        }
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const statusEl = form.querySelector(".form-status");
      const submitBtn = form.querySelector('button[type="submit"]');

      // Trigger native constraint validation and focus first invalid field
      if (!form.checkValidity()) {
        const firstInvalid = form.querySelector(":invalid");
        if (firstInvalid) {
          if (!supportsUserInvalid) {
            dirtyState.set(firstInvalid, { hasInteracted: true, hasBlurred: true });
            updateFallbackState(firstInvalid);
          }
          syncAria(firstInvalid, false);
          firstInvalid.focus();
        }
        return;
      }

      if (!endpoint) {
        setStatus(
          statusEl,
          "info",
          "Mailing list setup is almost done — add your Google Apps Script Web App URL to docs/site-config.js (see mailing-list/README.md)."
        );
        return;
      }

      const originalBtnText = submitBtn ? submitBtn.textContent : "";
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = isUnsubscribe ? "Unsubscribing..." : "Saving...";
      }
      setStatus(statusEl, "", "");

      try {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        for (const [key, value] of formData.entries()) {
          params.append(key, String(value));
        }

        const response = await fetch(endpoint, {
          method: "POST",
          body: params,
          redirect: "follow",
        });

        let result = { ok: response.ok };
        try {
          result = await response.json();
        } catch {
          // If the Apps Script response isn't JSON, rely on HTTP status
        }

        if (!response.ok || result.ok === false) {
          throw new Error(
            result.error ||
              (isUnsubscribe
                ? "Could not process your unsubscribe request right now. Please try again in a moment."
                : "Could not save your email right now. Please try again in a moment.")
          );
        }

        const message = isUnsubscribe
          ? "You've been unsubscribed and won't receive future DoDad Puzzles emails."
          : result.status === "updated"
            ? "You're already on the list — we saved your updated preferences!"
            : "You're on the list! We'll email you when new DoDad Puzzles updates drop.";

        setStatus(statusEl, "success", message);
        form.reset();
      } catch (err) {
        setStatus(
          statusEl,
          "error",
          err instanceof Error && err.message
            ? err.message
            : "Could not complete your request right now. Please try again in a moment."
        );
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalBtnText;
        }
      }
    });
  }
}


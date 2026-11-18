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


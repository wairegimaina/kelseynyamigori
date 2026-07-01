/* ============================================
   BRANDS — toggle inline edit panel
============================================ */
function toggleBrandEdit(pk) {
  const row = document.getElementById("brand-row-" + pk);
  const panel = document.getElementById("brand-edit-" + pk);
  const isOpen = panel.classList.contains("open");
  document
    .querySelectorAll(".edit-panel")
    .forEach((p) => p.classList.remove("open"));
  if (!isOpen) {
    panel.classList.add("open");
    panel.querySelector("input")?.focus();
  }
}

/* ============================================
   CONTACTS — expand/collapse detail row
============================================ */
function toggleDetail(pk) {
  const row = document.getElementById("detail-" + pk);
  const btn = document.querySelector("#row-" + pk + " .expand-btn");
  if (row.style.display === "none") {
    row.style.display = "";
    btn.textContent = "▼";
  } else {
    row.style.display = "none";
    btn.textContent = "▶";
  }
}

/* ============================================
   IMAGES — toggle display/edit state
============================================ */
function toggleImgEdit(pk) {
  const display = document.getElementById("img-display-" + pk);
  const edit = document.getElementById("img-edit-" + pk);
  const isOpen = edit.classList.contains("open");
  document
    .querySelectorAll(".card-edit")
    .forEach((e) => e.classList.remove("open"));
  document
    .querySelectorAll(".card-display")
    .forEach((d) => (d.style.display = ""));
  if (!isOpen) {
    display.style.display = "none";
    edit.classList.add("open");
    edit.querySelector("input")?.focus();
  }
}

/* ============================================
   RATES — toggle inline edit row
============================================ */
function toggleEdit(type, pk) {
  const row = document.getElementById(type + "-row-" + pk);
  const edit = document.getElementById(type + "-edit-" + pk);
  const isOpen = edit.classList.contains("open");
  document
    .querySelectorAll(".edit-row")
    .forEach((r) => r.classList.remove("open"));
  document
    .querySelectorAll(".rate-row[id]")
    .forEach((r) => (r.style.display = ""));
  if (!isOpen) {
    row.style.display = "none";
    edit.classList.add("open");
    const first = edit.querySelector("input, textarea");
    if (first) first.focus();
  }
}

/* ============================================
   SOCIAL — platform icon preview
============================================ */
const PLATFORMS = {
  instagram: {
    label: "Instagram",
    color: "#E1306C",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#E1306C" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
  },
  tiktok: {
    label: "TikTok",
    color: "#010101",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"><path fill="#69C9D0" d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.34 6.34 0 0 0-6.13 6.33 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.17 8.17 0 0 0 4.78 1.52V6.76a4.85 4.85 0 0 1-1.01-.07z" opacity=".6"/><path fill="#010101" d="M18.58 6.62a4.83 4.83 0 0 1-3.76-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.34 6.34 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.17 8.17 0 0 0 4.78 1.52V6.76a4.85 4.85 0 0 1-1.02-.14z"/></svg>',
  },
  facebook: {
    label: "Facebook",
    color: "#1877F2",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#1877F2"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>',
  },
  youtube: {
    label: "YouTube",
    color: "#FF0000",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"><path fill="#FF0000" d="M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46A2.78 2.78 0 0 0 1.46 6.42 29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.95 1.96C5.12 20 12 20 12 20s6.88 0 8.59-.46a2.78 2.78 0 0 0 1.95-1.96A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z"/><polygon fill="#fff" points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02"/></svg>',
  },
  twitter: {
    label: "Twitter / X",
    color: "#000000",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#000"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
  },
  snapchat: {
    label: "Snapchat",
    color: "#F7C900",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#FFFC00" stroke="#bbb" stroke-width="0.4"><path d="M12 2C8.68 2 6 4.68 6 8v1.09c-.34.1-.7.16-1.07.16-.35 0-.65.21-.76.54-.11.33 0 .69.27.9.79.6 1.3 1.35 1.53 2.23-.28.13-.58.2-.9.2-.39 0-.76.22-.93.58-.17.36-.1.78.18 1.07.79.81 2.13 1.23 4.07 1.28.44.78 1.32 1.95 3.61 1.95s3.17-1.17 3.61-1.95c1.94-.05 3.28-.47 4.07-1.28.28-.29.35-.71.18-1.07-.17-.36-.54-.58-.93-.58-.32 0-.62-.07-.9-.2.23-.88.74-1.63 1.53-2.23.27-.21.38-.57.27-.9-.11-.33-.41-.54-.76-.54-.37 0-.73-.06-1.07-.16V8c0-3.32-2.68-6-6-6z"/></svg>',
  },
  pinterest: {
    label: "Pinterest",
    color: "#E60023",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#E60023"><path d="M12 2C6.477 2 2 6.477 2 12c0 4.236 2.636 7.855 6.356 9.312-.088-.791-.167-2.005.035-2.868.181-.78 1.172-4.97 1.172-4.97s-.299-.598-.299-1.482c0-1.388.806-2.428 1.808-2.428.853 0 1.267.64 1.267 1.408 0 .858-.546 2.14-.828 3.33-.236.995.499 1.806 1.476 1.806 1.772 0 3.137-1.868 3.137-4.566 0-2.387-1.715-4.057-4.164-4.057-2.837 0-4.501 2.128-4.501 4.327 0 .856.33 1.773.741 2.274a.3.3 0 0 1 .069.283c-.076.315-.243.995-.277 1.134-.044.183-.146.222-.337.134-1.249-.581-2.03-2.407-2.03-3.874 0-3.154 2.292-6.052 6.608-6.052 3.469 0 6.165 2.473 6.165 5.776 0 3.447-2.173 6.22-5.19 6.22-1.013 0-1.966-.527-2.292-1.148l-.623 2.378c-.226.869-.835 1.958-1.244 2.621.937.29 1.931.446 2.962.446 5.523 0 10-4.477 10-10S17.523 2 12 2z"/></svg>',
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#0A66C2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7H10v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>',
  },
  threads: {
    label: "Threads",
    color: "#101010",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 192 192" fill="#101010"><path d="M141.537 88.988a66.667 66.667 0 0 0-2.518-1.143c-1.482-27.307-16.403-42.94-41.457-43.1h-.34c-14.986 0-27.449 6.396-35.12 18.05l13.78 9.426c5.73-8.695 14.724-10.548 21.347-10.548h.229c8.249.053 14.474 2.452 18.503 7.129 2.932 3.405 4.893 8.111 5.864 14.05-7.314-1.243-15.224-1.626-23.68-1.14-23.82 1.372-39.134 15.265-38.105 34.569.522 9.792 5.4 18.216 13.735 23.719 7.047 4.652 16.124 6.927 25.557 6.412 12.458-.683 22.231-5.436 29.049-14.127 5.178-6.6 8.453-15.153 9.899-25.93 5.937 3.583 10.337 8.298 12.767 13.966 4.132 9.635 4.373 25.468-8.546 38.376-11.319 11.308-24.925 16.2-45.488 16.351-22.809-.169-40.06-7.484-51.275-21.742C35.236 139.966 29.808 120.682 29.605 96c.203-24.682 5.63-43.966 16.133-57.317C56.954 24.425 74.204 17.11 97.013 16.94c22.975.17 40.526 7.52 52.171 21.847 5.71 7.026 10.015 15.86 12.853 26.162l16.147-4.308c-3.44-12.68-8.853-23.606-16.219-32.668C147.036 9.607 125.202.195 97.07 0h-.113C68.882.195 47.292 9.642 32.788 28.08 19.882 44.485 13.224 67.315 13.001 95.932L13 96v.067c.224 28.617 6.882 51.447 19.788 67.854C47.292 182.358 68.882 191.805 96.957 192h.113c24.96-.173 42.554-6.708 57.048-21.189 18.963-18.945 18.392-42.692 12.142-57.27-4.484-10.454-13.033-18.945-24.723-24.553zM98.44 129.507c-10.44.588-21.286-4.098-21.82-14.135-.398-7.442 5.276-15.745 22.427-16.734 1.96-.113 3.895-.169 5.807-.169 6.31 0 12.193.621 17.548 1.79-1.997 24.967-13.376 28.665-23.962 29.248z"/></svg>',
  },
  whatsapp: {
    label: "WhatsApp",
    color: "#25D366",
    svg: '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#25D366"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>',
  },
};

function updatePreview(platform) {
  const p = PLATFORMS[platform];
  if (!p) return;
  const icon = document.getElementById("previewIcon");
  const name = document.getElementById("previewName");
  const preview = document.getElementById("platformPreview");
  icon.innerHTML = p.svg;
  name.textContent = p.label;
  name.style.color = p.color;
  preview.style.borderColor = p.color + "55";
}

/* ============================================
   WORK — toggle item edit, category edit, forms
============================================ */
function toggleItemEdit(pk) {
  const display = document.getElementById("item-display-" + pk);
  const form = document.getElementById("item-edit-" + pk);
  const actions = document.getElementById("item-actions-" + pk);
  // Use a data attribute as the source of truth — avoids fighting computed vs inline style
  const editing = form.dataset.open === "1";
  if (editing) {
    form.style.display = "none";
    form.dataset.open = "0";
    display.style.display = "block";
    actions.style.display = "flex";
  } else {
    form.style.display = "block";
    form.dataset.open = "1";
    display.style.display = "none";
    actions.style.display = "none";
  }
}

function toggleCatEdit(pk) {
  const display = document.getElementById("cat-display-" + pk);
  const form = document.getElementById("cat-edit-" + pk);
  const editing = form.style.display === "flex";
  display.style.display = editing ? "flex" : "none";
  form.style.display = editing ? "none" : "flex";
}

function toggleForm(id, btn) {
  const wrap = document.getElementById(id);
  const isOpen = wrap.classList.toggle("open");
  if (btn) btn.textContent = isOpen ? "− Cancel" : "+ Add video";
}

function toggleVideoSource(catPk, value) {
  // Supports both add panel IDs (upload-{pk}, embed-{pk})
  // and edit panel IDs (upload-edit-{pk}, embed-edit-{pk})
  const isEdit = catPk.startsWith("edit-");
  const prefix = isEdit ? "" : "";
  const uploadDiv = document.getElementById("upload-" + catPk);
  const embedDiv = document.getElementById("embed-" + catPk);
  if (!uploadDiv || !embedDiv) return;
  if (value === "upload") {
    uploadDiv.style.display = "block";
    embedDiv.style.display = "none";
  } else {
    uploadDiv.style.display = "none";
    embedDiv.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const nameInput = document.getElementById("cat-name");
  const slugInput = document.getElementById("cat-slug");
  if (nameInput && slugInput) {
    nameInput.addEventListener("input", function () {
      slugInput.value = nameInput.value
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "-");
    });
  }
});

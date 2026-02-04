// Minimal JS: optional enhancements can go here.
// Keeping it light for learning-focused demo.

(function () {
  // Auto-dismiss flash messages after a few seconds.
  const flashes = document.querySelectorAll('.flash');
  if (flashes.length) {
    setTimeout(() => {
      flashes.forEach((f) => {
        f.style.transition = 'opacity 300ms ease';
        f.style.opacity = '0';
        setTimeout(() => f.remove(), 350);
      });
    }, 4500);
  }

  // Chat enhancements (emoji + attachment preview). Progressive enhancement.
  const composer = document.querySelector('.dm-composer');
  const thread = document.querySelector('.dm-thread');
  if (thread) {
    // Scroll to latest message on load.
    thread.scrollTop = thread.scrollHeight;
  }

  if (!composer) return;

  const emojiToggle = composer.querySelector('[data-emoji-toggle]');
  const emojiPopover = composer.querySelector('.emoji-popover');
  const emojiPicker = composer.querySelector('emoji-picker');
  const input = composer.querySelector('input[name="body"]');
  const fileInput = composer.querySelector('input[type="file"][name="attachment"]');

  const preview = composer.querySelector('.composer-preview');
  const previewImg = composer.querySelector('.preview-img');
  const previewClear = composer.querySelector('[data-preview-clear]');

  function insertAtCursor(el, text) {
    if (!el) return;
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? el.value.length;
    const before = el.value.slice(0, start);
    const after = el.value.slice(end);
    el.value = before + text + after;

    const pos = start + text.length;
    el.setSelectionRange(pos, pos);
    el.focus();
  }

  function closeEmoji() {
    if (emojiPopover) emojiPopover.hidden = true;
    if (emojiToggle) emojiToggle.setAttribute('aria-expanded', 'false');
  }

  if (emojiToggle && emojiPopover) {
    emojiToggle.addEventListener('click', () => {
      const open = emojiPopover.hidden === false;
      emojiPopover.hidden = open;
      emojiToggle.setAttribute('aria-expanded', String(!open));
      if (!open) input?.focus();
    });
  }

  // If the web component loads, use its event.
  if (emojiPicker) {
    emojiPicker.addEventListener('emoji-click', (e) => {
      const detail = e.detail;
      const emoji = detail?.emoji?.unicode;
      if (emoji) {
        insertAtCursor(input, emoji);
      }
    });
  }

  // Close the emoji popover when tapping outside.
  document.addEventListener('click', (e) => {
    const target = e.target;
    if (!emojiPopover || emojiPopover.hidden) return;
    if (composer.contains(target)) {
      // Click inside composer: allow.
      return;
    }
    closeEmoji();
  });

  // Attachment image preview.
  function clearPreview() {
    if (!preview) return;
    preview.hidden = true;
    if (previewImg) previewImg.src = '';
    if (fileInput) fileInput.value = '';
  }

  if (fileInput && preview && previewImg) {
    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) {
        clearPreview();
        return;
      }

      if (!file.type.startsWith('image/')) {
        clearPreview();
        return;
      }

      const url = URL.createObjectURL(file);
      previewImg.src = url;
      preview.hidden = false;
    });
  }

  if (previewClear) {
    previewClear.addEventListener('click', clearPreview);
  }
})();

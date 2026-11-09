document.querySelectorAll('input[type=file]').forEach(function (input) {
  input.addEventListener('change', function () {
    var zone = input.closest('.dz');
    var target = zone && zone.querySelector('[data-chosen]');
    if (target) target.textContent = input.files[0] ? input.files[0].name : '';
  });
});
document.querySelectorAll('form[data-busy]').forEach(function (form) {
  form.addEventListener('submit', function () {
    var button = form.querySelector('button[type=submit]');
    if (button) { button.disabled = true; button.textContent = 'Calcul en cours…'; }
  });
});
document.querySelectorAll('[data-copy]').forEach(function (button) {
  button.addEventListener('click', function () {
    navigator.clipboard.writeText(button.dataset.copy).then(function () {
      button.textContent = 'Lien copié';
    });
  });
});

(function () {
  var button = document.querySelector('.burger'), menu = document.getElementById('menu');
  if (!button || !menu) return;
  function setOpen(open) {
    menu.classList.toggle('open', open);
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
    button.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  }
  button.addEventListener('click', function () { setOpen(button.getAttribute('aria-expanded') !== 'true'); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) { setOpen(false); button.focus(); }
  });
  document.addEventListener('click', function (e) {
    if (menu.classList.contains('open') && !menu.contains(e.target) && !button.contains(e.target)) setOpen(false);
  });
})();

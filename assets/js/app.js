'use strict';

document.querySelectorAll('[data-role-option]').forEach(card => card.addEventListener('click', () => {
  document.querySelectorAll('[data-role-option]').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
  const radio = card.querySelector('input[type=radio]');
  if (radio) radio.checked = true;
}));

document.querySelectorAll('[data-service-filter]').forEach(category => {
  const service = document.querySelector(category.dataset.serviceFilter || '');
  if (!service) return;
  const sync = () => {
    [...service.options].forEach((option, index) => {
      if (index > 0) option.hidden = Boolean(category.value) && option.dataset.category !== category.value;
    });
    if (service.selectedOptions[0]?.hidden) service.value = '';
  };
  category.addEventListener('change', sync);
  sync();
});

document.addEventListener('submit', event => {
  const form = event.target.closest('form[data-confirm-submit]');
  if (form && !window.confirm(form.dataset.confirmSubmit || 'Continue?')) event.preventDefault();
});

document.querySelectorAll('select[data-auto-submit]').forEach(select => {
  select.addEventListener('change', () => select.form?.requestSubmit());
});

function renderFavoriteButton(button, favorite) {
  button.replaceChildren();
  const icon = document.createElement('i');
  icon.className = favorite ? 'fa-solid fa-heart me-1' : 'fa-regular fa-heart me-1';
  button.append(icon, document.createTextNode(favorite ? ' Saved' : ' Save'));
  button.classList.toggle('btn-danger', favorite);
  button.classList.toggle('btn-outline-danger', !favorite);
}

document.addEventListener('click', async event => {
  const button = event.target.closest('.js-favorite');
  if (!button) return;
  event.preventDefault();
  const body = new URLSearchParams({target_user_id: button.dataset.target || '', csrf_token: window.LOCALCONNECT_CSRF || ''});
  const base = typeof window.LOCALCONNECT_BASE_URL === 'string' ? window.LOCALCONNECT_BASE_URL : '/localconnect/';
  try {
    const response = await fetch(base + 'ajax/favorite.php', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest'}, body, credentials:'same-origin'});
    const data = await response.json();
    if (!response.ok || !data.ok) { window.alert(data.message || 'Could not update favorite.'); return; }
    renderFavoriteButton(button, Boolean(data.favorite));
    if (!data.favorite && location.pathname.endsWith('/favorites.php')) button.closest('.col-md-6')?.remove();
  } catch(e) { window.alert('Could not update favorite. Please try again.'); }
});

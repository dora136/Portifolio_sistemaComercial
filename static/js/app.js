// NovaCRM - Global Application Script

document.addEventListener('DOMContentLoaded', () => {

  // ========================================
  // 1. Sidebar Navigation
  // ========================================
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.querySelector('.toggle-btn');

  // Restore collapsed state from localStorage
  if (localStorage.getItem('sidebarCollapsed') === 'true' && sidebar) {
    sidebar.classList.add('collapsed');
    updateToggleIcon(true);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const collapsed = sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebarCollapsed', String(collapsed));
      updateToggleIcon(collapsed);
    });
  }

  function updateToggleIcon(collapsed) {
    const icon = document.querySelector('.toggle-btn i');
    if (icon) {
      icon.setAttribute('data-lucide', collapsed ? 'chevron-right' : 'chevron-left');
      lucide.createIcons();
    }
  }

  // Active nav-item highlighting
  const currentPage = document.body.getAttribute('data-page');
  if (currentPage) {
    document.querySelectorAll('[data-view]').forEach(item => {
      if (item.getAttribute('data-view') === currentPage) {
        item.classList.add('active');

        // Auto-open parent <details> if the active item is inside one
        const parentDetails = item.closest('details.nav-group');
        if (parentDetails) {
          parentDetails.setAttribute('open', '');
        }
      }
    });
  }

  // "Cadastro" button opens the lead creation modal
  const addLeadBtn = document.querySelector('[data-view="add-lead"]');
  if (addLeadBtn) {
    addLeadBtn.addEventListener('click', () => openLeadModal());
  }

  // ========================================
  // 2. Lead Creation Modal
  // ========================================
  const leadModal = document.querySelector('[data-lead-modal]');
  const leadForm = document.querySelector('[data-lead-form]');
  const leadIndicator = document.querySelector('[data-lead-indicator]');
  const leadToggleContainer = document.querySelector('[data-lead-toggle]');

  function openLeadModal() {
    if (!leadModal) return;
    leadModal.classList.add('open');
    setLeadMode('parceiro');
    lucide.createIcons();
  }

  function closeLeadModal() {
    if (!leadModal) return;
    leadModal.classList.remove('open');
    if (leadForm) leadForm.reset();
    // Reset multi-select labels
    document.querySelectorAll('[data-multi-select] .multi-select-label').forEach(label => {
      label.textContent = 'Selecione as soluções';
    });
  }

  // Close buttons
  document.querySelectorAll('[data-lead-modal-close]').forEach(el => {
    el.addEventListener('click', closeLeadModal);
  });

  // Toggle between "parceiro" and "lead" modes
  if (leadToggleContainer) {
    leadToggleContainer.querySelectorAll('[data-lead-type]').forEach(btn => {
      btn.addEventListener('click', () => {
        setLeadMode(btn.getAttribute('data-lead-type'));
      });
    });
  }

  function setLeadMode(mode) {
    if (!leadForm) return;
    leadForm.setAttribute('data-mode', mode);

    // Update toggle button active state
    if (leadToggleContainer) {
      leadToggleContainer.querySelectorAll('[data-lead-type]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-lead-type') === mode);
      });
    }

    // Move indicator to the active button
    if (leadIndicator && leadToggleContainer) {
      const activeBtn = leadToggleContainer.querySelector(`[data-lead-type="${mode}"]`);
      if (activeBtn) {
        leadIndicator.style.left = activeBtn.offsetLeft + 'px';
        leadIndicator.style.width = activeBtn.offsetWidth + 'px';
      }
    }

    // Show/hide variant sections
    document.querySelectorAll('[data-variant]').forEach(section => {
      const variant = section.getAttribute('data-variant');
      section.style.display = variant === mode ? '' : 'none';
    });
  }

  // ========================================
  // 3. Multi-Select Component
  // ========================================
  let solucoesCache = null;

  async function fetchSolucoes() {
    if (solucoesCache) return solucoesCache;
    try {
      const res = await fetch('/portfolio/api/solucoes-ativas');
      solucoesCache = await res.json();
      return solucoesCache;
    } catch (err) {
      console.error('Erro ao carregar solucoes:', err);
      return [];
    }
  }

  async function initMultiSelects() {
    const multiSelects = document.querySelectorAll('[data-multi-select]');
    if (multiSelects.length === 0) return;

    const solucoes = await fetchSolucoes();

    multiSelects.forEach(container => {
      const fieldName = container.getAttribute('data-multi-select');
      const toggle = container.querySelector('.multi-select-toggle');
      const menu = container.querySelector('.multi-select-menu');
      const label = container.querySelector('.multi-select-label');
      const hiddenInput = container.closest('label')?.querySelector(`input[name="${fieldName}"]`)
        || document.querySelector(`input[name="${fieldName}"]`);

      // Render checkboxes
      menu.innerHTML = solucoes.map(sol => `
        <label class="multi-select-option">
          <input type="checkbox" value="${sol.id}" data-name="${sol.name}" />
          <span>${sol.name}</span>
        </label>
      `).join('');

      // Toggle menu open/close
      toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isOpen = !menu.hidden;
        closeAllMultiSelectMenus();
        if (!isOpen) {
          menu.hidden = false;
          toggle.setAttribute('aria-expanded', 'true');
        }
      });

      // Update selection on checkbox change
      menu.addEventListener('change', () => {
        const checked = menu.querySelectorAll('input[type="checkbox"]:checked');
        const ids = [];
        const names = [];
        checked.forEach(cb => {
          ids.push(cb.value);
          names.push(cb.getAttribute('data-name'));
        });

        if (hiddenInput) {
          hiddenInput.value = ids.join(',');
        }

        label.textContent = names.length > 0
          ? names.join(', ')
          : 'Selecione as soluções';
      });
    });
  }

  function closeAllMultiSelectMenus() {
    document.querySelectorAll('[data-multi-select]').forEach(container => {
      const menu = container.querySelector('.multi-select-menu');
      const toggle = container.querySelector('.multi-select-toggle');
      if (menu) menu.hidden = true;
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    });
  }

  // Close multi-select when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-multi-select]')) {
      closeAllMultiSelectMenus();
    }
  });

  initMultiSelects();

  // ========================================
  // 4. Comercial Select
  // ========================================
  async function initComercialSelect() {
    const select = document.querySelector('[data-comercial-select]');
    if (!select) return;

    try {
      const res = await fetch('/portfolio/api/comerciais');
      const comerciais = await res.json();

      comerciais.forEach(c => {
        const option = document.createElement('option');
        option.value = c.id_col || c.id_crm_colab || '';
        option.textContent = c.nome;
        select.appendChild(option);
      });
    } catch (err) {
      console.error('Erro ao carregar comerciais:', err);
    }
  }

  initComercialSelect();

  // ========================================
  // 5. CNPJ Input Mask
  // ========================================
  const cnpjInput = document.querySelector('[data-cnpj-input]');

  if (cnpjInput) {
    cnpjInput.addEventListener('input', () => {
      let v = cnpjInput.value.replace(/\D/g, '');
      if (v.length > 14) v = v.slice(0, 14);

      // Format: XX.XXX.XXX/XXXX-XX
      let formatted = '';
      if (v.length > 12) {
        formatted = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2})/, '$1.$2.$3/$4-$5');
      } else if (v.length > 8) {
        formatted = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{1,4})/, '$1.$2.$3/$4');
      } else if (v.length > 5) {
        formatted = v.replace(/^(\d{2})(\d{3})(\d{1,3})/, '$1.$2.$3');
      } else if (v.length > 2) {
        formatted = v.replace(/^(\d{2})(\d{1,3})/, '$1.$2');
      } else {
        formatted = v;
      }

      cnpjInput.value = formatted;
    });
  }

  // ========================================
  // 6. CNPJ Search
  // ========================================
  const cnpjSearchBtn = document.querySelector('.cnpj-search-btn');
  const cnpjResultsModal = document.querySelector('[data-cnpj-results-modal]');

  if (cnpjSearchBtn && cnpjInput) {
    cnpjSearchBtn.addEventListener('click', async () => {
      const cnpj = cnpjInput.value.replace(/\D/g, '');
      if (!cnpj || cnpj.length < 14) {
        alert('Informe um CNPJ valido.');
        return;
      }

      cnpjSearchBtn.disabled = true;
      try {
        const res = await fetch('/portfolio/api/cnpj-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cnpj }),
        });
        const data = await res.json();
        showCnpjResults(data);
      } catch (err) {
        console.error('Erro na pesquisa de CNPJ:', err);
        alert('Erro ao pesquisar CNPJ. Tente novamente.');
      } finally {
        cnpjSearchBtn.disabled = false;
      }
    });
  }

  function showCnpjResults(data) {
    if (!cnpjResultsModal) return;

    const body = cnpjResultsModal.querySelector('[data-cnpj-results-body]');
    const subtitle = cnpjResultsModal.querySelector('[data-cnpj-results-subtitle]');

    let html = '';

    if (data.company) {
      html += `
        <div class="cnpj-company-info">
          <h4>${data.company.nome_fantasia || data.company.razao_social || 'Empresa'}</h4>
          ${data.company.razao_social ? `<p><strong>Razao Social:</strong> ${data.company.razao_social}</p>` : ''}
          ${data.company.cnpj ? `<p><strong>CNPJ:</strong> ${data.company.cnpj}</p>` : ''}
          ${data.company.segmento ? `<p><strong>Segmento:</strong> ${data.company.segmento}</p>` : ''}
        </div>
      `;
    }

    if (data.leads && data.leads.length > 0) {
      if (subtitle) {
        subtitle.textContent = `${data.leads.length} lead(s) encontrado(s) para o CNPJ informado.`;
      }
      html += '<div class="cnpj-leads-list">';
      data.leads.forEach(lead => {
        html += `
          <div class="cnpj-lead-card">
            <strong>${lead.nome_fantasia || lead.razao_social || 'Lead'}</strong>
            ${lead.solucao ? `<span class="badge">${lead.solucao}</span>` : ''}
            ${lead.status ? `<span class="badge badge-${lead.status}">${lead.status}</span>` : ''}
          </div>
        `;
      });
      html += '</div>';
    } else {
      if (subtitle) {
        subtitle.textContent = 'Nenhum lead encontrado para o CNPJ informado.';
      }
      if (!data.company) {
        html += '<p class="cnpj-no-results">Nenhum resultado encontrado.</p>';
      }
    }

    if (body) body.innerHTML = html;
    cnpjResultsModal.classList.add('open');
    lucide.createIcons();
  }

  // Close CNPJ results modal
  document.querySelectorAll('[data-cnpj-results-close]').forEach(el => {
    el.addEventListener('click', () => {
      if (cnpjResultsModal) cnpjResultsModal.classList.remove('open');
    });
  });

  // ========================================
  // 7. Form Submission
  // ========================================
  const saveBtn = document.querySelector('.solucao-edit-save');

  if (saveBtn && leadForm) {
    saveBtn.addEventListener('click', async () => {
      if (!leadForm.checkValidity()) {
        leadForm.reportValidity();
        return;
      }

      const mode = leadForm.getAttribute('data-mode') || 'parceiro';
      const formData = new FormData(leadForm);
      const payload = {};

      formData.forEach((value, key) => {
        payload[key] = value;
      });

      payload.tipo = mode;

      // Use the correct solucao field based on mode
      if (mode === 'parceiro') {
        payload.solucao = payload.solucao_parceiro || '';
        delete payload.solucao_lead;
      } else {
        payload.solucao = payload.solucao_lead || '';
        delete payload.solucao_parceiro;
      }

      saveBtn.disabled = true;
      saveBtn.innerHTML = '<i data-lucide="loader" style="width:16px;height:16px;animation:spin 1s linear infinite"></i> Salvando...';

      try {
        const res = await fetch('/portfolio/api/cadastro', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await res.json();

        if (res.ok) {
          showToast('Cadastro realizado com sucesso!');
          closeLeadModal();
          setTimeout(() => window.location.reload(), 800);
        } else {
          alert(result.detail || result.message || 'Erro ao salvar cadastro.');
        }
      } catch (err) {
        console.error('Erro ao salvar cadastro:', err);
        alert('Erro ao salvar cadastro. Tente novamente.');
      } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i data-lucide="check" style="width:16px;height:16px;"></i> Salvar';
        lucide.createIcons();
      }
    });
  }

  // ========================================
  // Toast notification
  // ========================================
  function showToast(message, duration = 3000) {
    const existing = document.querySelector('.app-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'app-toast';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      background: hsl(var(--primary, 220 90% 56%));
      color: #fff;
      padding: 0.75rem 1.25rem;
      border-radius: 0.5rem;
      font-size: 0.875rem;
      font-weight: 500;
      z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      animation: toast-in 0.3s ease;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  // ========================================
  // 8. Re-init Lucide Icons
  // ========================================
  // Expose a global helper so page-specific scripts can re-init icons
  window.NovaCRM = window.NovaCRM || {};
  window.NovaCRM.reinitIcons = () => lucide.createIcons();
  window.NovaCRM.openLeadModal = openLeadModal;
  window.NovaCRM.showToast = showToast;

});

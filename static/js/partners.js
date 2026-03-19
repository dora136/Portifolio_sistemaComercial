// Partners Module - Manages the Master-Detail layout for Partners
class PartnersManager {
  constructor() {
    this.partners = [];
    this.selectedPartner = null;
    this.filteredPartners = [];
    this.activeFilters = {
      status: 'all',
      module: 'all'
    };
    this.filterLabels = {
      status: {
        all: 'Todos',
        active: 'Ativo',
        pending: 'Pendente',
        blocked: 'Bloqueado'
      },
      module: {
        all: 'Todos',
        comercial: 'Comercial',
        indicador: 'Indicacao'
      }
    };

    this.leadSlideOver = null;
    this.init();
    this.bindPartnerActions();
  }

  init() {
    // Inicializa o slide-over de leads independente
    this.leadSlideOver = new LeadSlideOver();

    // Load partners from global data
    if (window.PARTNERS_DATA) {
      this.partners = window.PARTNERS_DATA;
      this.filteredPartners = [...this.partners];
      this.render();

      // Select first partner by default
      if (this.partners.length > 0) {
        this.selectPartner(this.partners[0].id);
      }
    }

    // Setup search
    const searchInput = document.getElementById('partnerSearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterPartners(e.target.value);
      });
    }

    this.bindFilterControls();
    this.updateAppliedFilters();
    this.bindModuleActions();
  }

  filterPartners(query) {
    query = query.toLowerCase().trim();

    this.filteredPartners = this.partners.filter(partner => {
      const matchesQuery = !query ||
        partner.name.toLowerCase().includes(query) ||
        partner.cnpj.includes(query);

      const matchesStatus = this.activeFilters.status === 'all' ||
        partner.status === this.activeFilters.status;

      const matchesModule = this.activeFilters.module === 'all' ||
        (partner.modules && partner.modules.includes(this.activeFilters.module));

      return matchesQuery && matchesStatus && matchesModule;
    });

    this.renderList();

    // If selected partner is not in filtered list, clear selection
    if (this.selectedPartner && !this.filteredPartners.find(p => p.id === this.selectedPartner.id)) {
      this.selectedPartner = null;
      this.renderDetail();
    }
  }

  bindFilterControls() {
    const filterPanel = document.querySelector('[data-filter-panel]');
    const searchBox = document.querySelector('.search-box');
    const appliedFilters = document.querySelector('[data-applied-filters]');
    if (!filterPanel || !searchBox) return;

    const filterButtons = filterPanel.querySelectorAll('[data-filter-group]');
    filterButtons.forEach(button => {
      button.addEventListener('click', () => {
        const group = button.getAttribute('data-filter-group');
        const value = button.getAttribute('data-filter-value');
        if (!group || !value) return;

        this.activeFilters[group] = value;
        filterPanel.querySelectorAll(`[data-filter-group="${group}"]`).forEach(el => {
          el.classList.toggle('active', el === button);
        });

        const query = document.getElementById('partnerSearch')?.value || '';
        this.filterPartners(query);
        this.updateAppliedFilters();
      });
    });

    const openPanel = () => filterPanel.classList.add('open');
    const closePanel = () => filterPanel.classList.remove('open');

    searchBox.addEventListener('click', openPanel);
    document.getElementById('partnerSearch')?.addEventListener('focus', openPanel);

    document.addEventListener('click', (event) => {
      if (!filterPanel.contains(event.target) && !searchBox.contains(event.target)) {
        closePanel();
      }
    });

    if (appliedFilters) {
      appliedFilters.addEventListener('click', (event) => {
        const target = event.target.closest('[data-filter-clear]');
        if (!target) return;
        const group = target.getAttribute('data-filter-group');
        if (!group) return;
        this.activeFilters[group] = 'all';

        const activeButton = filterPanel.querySelector(`[data-filter-group="${group}"][data-filter-value="all"]`);
        if (activeButton) {
          filterPanel.querySelectorAll(`[data-filter-group="${group}"]`).forEach(el => {
            el.classList.toggle('active', el === activeButton);
          });
        }

        const query = document.getElementById('partnerSearch')?.value || '';
        this.filterPartners(query);
        this.updateAppliedFilters();
      });
    }
  }

  updateAppliedFilters() {
    const container = document.querySelector('[data-applied-filters]');
    if (!container) return;

    const chips = [];
    if (this.activeFilters.status !== 'all') {
      chips.push(this.renderAppliedFilter('status', this.filterLabels.status[this.activeFilters.status]));
    }
    if (this.activeFilters.module !== 'all') {
      chips.push(this.renderAppliedFilter('module', this.filterLabels.module[this.activeFilters.module]));
    }

    container.innerHTML = chips.join('');
    container.classList.toggle('has-filters', chips.length > 0);
    lucide.createIcons();
  }

  renderAppliedFilter(group, label) {
    return `
      <button type="button" class="applied-filter-chip" data-filter-clear data-filter-group="${group}">
        <span>${label}</span>
        <i data-lucide="x"></i>
      </button>
    `;
  }

  render() {
    this.renderList();
    this.renderDetail();
  }

  renderList() {
    const container = document.querySelector('.partner-list');
    if (!container) return;

    if (this.filteredPartners.length === 0) {
      container.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: hsl(var(--muted-foreground));">
          <p class="text-sm">Nenhum parceiro encontrado</p>
        </div>
      `;
      return;
    }

    const html = this.filteredPartners.map(partner => {
      const isSelected = this.selectedPartner && this.selectedPartner.id === partner.id;
      return `
        <button class="partner-item ${isSelected ? 'selected' : ''}" onclick="window.partnersManager.selectPartner('${partner.id}')">
          <div class="partner-header">
            <div style="min-width: 0; flex: 1;">
              <div class="partner-name">${partner.name}</div>
              <div class="partner-cnpj">${partner.cnpj}</div>
            </div>
            <span class="badge badge-${partner.status}">
              ${this.getStatusLabel(partner.status)}
            </span>
          </div>
          ${partner.modules && partner.modules.length > 0 ? `
            <div class="module-tags">
              ${partner.modules.map(mod => `
                <span class="badge tag-${mod}">
                  🏷️ ${mod === 'comercial' ? 'Comercial' : 'Indicação'}
                </span>
              `).join('')}
            </div>
          ` : ''}
        </button>
      `;
    }).join('');

    container.innerHTML = html;
  }

  selectPartner(partnerId) {
    this.selectedPartner = this.partners.find(p => p.id === partnerId);
    this.renderList(); // Re-render to update selected state
    this.renderDetail();
  }

  renderDetail() {
    const container = document.querySelector('.detail-panel');
    if (!container) return;

    if (!this.selectedPartner) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-lucide="users"></i>
          <h3>Selecione um parceiro</h3>
          <p>Escolha um parceiro na lista para ver os detalhes</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const partner = this.selectedPartner;

    container.innerHTML = `
      <div class="fade-in">
        <!-- Header -->
        <div class="detail-header">
          <div class="detail-title-row">
            <div>
              <h1 class="detail-title">${partner.name}</h1>
              <p class="detail-subtitle">${partner.cnpj}</p>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="badge badge-${partner.status}">
                ${this.getStatusLabel(partner.status)}
              </span>
              <button class="detail-action-btn" type="button" data-action="edit-partner" data-partner-id="${partner.id}" title="Editar parceiro">
                <i data-lucide="pencil"></i>
              </button>
              <button class="detail-action-btn" type="button" data-action="delete-partner" data-partner-id="${partner.id}" title="Excluir parceiro" style="color: hsl(var(--danger, 0 84% 60%));">
                <i data-lucide="trash-2"></i>
              </button>
            </div>
          </div>
        </div>

        <div class="detail-cards">
          <!-- Dados Cadastrais -->
          <div class="card">
            <div class="card-header">
              <div class="card-header-title">
                <i data-lucide="building-2"></i>
                <h3 class="card-title">Dados Cadastrais</h3>
              </div>
              <button class="detail-action-btn" type="button">
                <i data-lucide="folder-open"></i>
                Abrir pasta
              </button>
            </div>
            <div class="card-content">
              ${partner.razaoSocial ? this.renderInfoRow('file-text', 'Razao social', partner.razaoSocial) : ''}
              ${this.renderInfoRow('map-pin', 'Estado', partner.state || '-')}
              ${partner.email ? this.renderInfoRow('mail', 'E-mail', partner.email) : ''}
              ${partner.phone ? this.renderInfoRow('phone', 'Telefone', partner.phone) : ''}
            </div>
          </div>

          <!-- Módulo Comercial -->
          ${partner.modules.includes('comercial') ? `
            <div class="card">
              <div class="card-header card-header-space">
                <div class="card-header-title">
                  <span style="width: 8px; height: 8px; border-radius: 50%; background-color: hsl(var(--comercial));"></span>
                  <h3 class="card-title">Módulo Comercial</h3>
                </div>
                <span class="badge badge-primary">Ativo</span>
              </div>
              ${partner.comercialSolutions && partner.comercialSolutions.length > 0 ? `
                <div class="solutions-list">
                  ${partner.comercialSolutions.map(solution => this.renderSolutionRow(solution, partner.id)).join('')}
                </div>
              ` : `
                <div class="solutions-empty">Nenhuma solucao associada.</div>
              `}
            </div>
          ` : `
            ${this.renderEmptyModuleCard('comercial', 'Módulo Comercial', 'Ative o módulo Comercial para contratos Enterprise', 'Ativar Módulo', partner.id)}
          `}

          <!-- Módulo Indicação -->
          ${partner.modules.includes('indicador') && partner.indicadorData ? `
            <div class="card">
              <div class="card-header card-header-space">
                <div class="card-header-title">
                  <span style="width: 8px; height: 8px; border-radius: 50%; background-color: hsl(var(--indicador));"></span>
                  <h3 class="card-title">Módulo Indicação</h3>
                </div>
                <span class="badge badge-primary">Ativo</span>
              </div>
              <div class="indicator-funnel">
                <div class="funnel-steps">
                  <div class="funnel-step funnel-step-neutral">
                    <div class="funnel-step-label">Gerados</div>
                    <div class="funnel-step-value">${partner.indicadorData.leadsGenerated}</div>
                  </div>
                  <i class="funnel-connector" data-lucide="chevron-right"></i>
                  <div class="funnel-step funnel-step-warm">
                    <div class="funnel-step-label">Em negociacao</div>
                    <div class="funnel-step-value">${partner.indicadorData.leadsNegotiation}</div>
                  </div>
                  <i class="funnel-connector" data-lucide="chevron-right"></i>
                  <div class="funnel-step funnel-step-success">
                    <div class="funnel-step-label">Fechamento</div>
                    <div class="funnel-step-value">${partner.indicadorData.leadsClosed}</div>
                  </div>
                </div>
                <div class="funnel-kpi">
                  <i class="funnel-kpi-icon" data-lucide="target"></i>
                  <div class="funnel-kpi-content">
                    <div class="funnel-kpi-label">Taxa</div>
                    <div class="funnel-kpi-value">${partner.indicadorData.conversionRate}%</div>
                  </div>
                </div>
              </div>
            </div>
          ` : `
            ${this.renderEmptyModuleCard('indicador', 'Módulo Indicação', 'Ative o programa de indicação para este parceiro', 'Ativar Módulo', partner.id)}
          `}
        </div>
      </div>
    `;

    lucide.createIcons();
  }

  renderEmptyModuleCard(moduleType, title, description, buttonText, partnerId = null) {
    const actionAttrs = moduleType === 'indicador' && partnerId
      ? `data-action="activate-module" data-module="indicador" data-partner-id="${partnerId}"`
      : moduleType === 'comercial' && partnerId
        ? `data-action="activate-module" data-module="comercial" data-partner-id="${partnerId}"`
      : '';
    return `
      <div class="card" style="border: 2px dashed hsl(var(--border)); background-color: hsl(var(--muted) / 0.3);">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; text-align: center;">
          <i data-lucide="plus" style="width: 32px; height: 32px; color: hsl(var(--muted-foreground)); margin-bottom: 0.75rem;"></i>
          <h4 style="font-weight: 500; color: hsl(var(--foreground)); margin-bottom: 0.25rem;">${title}</h4>
          <p style="font-size: 0.875rem; color: hsl(var(--muted-foreground)); margin-bottom: 1rem;">${description}</p>
          <button ${actionAttrs} style="padding: 0.5rem 1rem; border: 1px solid hsl(var(--border)); background-color: hsl(var(--background)); border-radius: 0.375rem; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.backgroundColor='hsl(var(--accent))'" onmouseout="this.style.backgroundColor='hsl(var(--background))'">
            ${buttonText}
          </button>
        </div>
      </div>
    `;
  }

  bindModuleActions() {
    document.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-action="activate-module"]');
      if (!button) return;

      const moduleType = button.getAttribute('data-module');
      const partnerId = button.getAttribute('data-partner-id');
      if (!partnerId) return;

      let selectedSolutions = null;
      if (moduleType === 'indicador') {
        const confirmed = await this.openIndicacaoModal();
        if (!confirmed) return;
      } else if (moduleType === 'comercial') {
        selectedSolutions = await this.openComercialModal(partnerId);
        if (!selectedSolutions || selectedSolutions.length === 0) {
          return;
        }
      }

      button.disabled = true;
      const previousText = button.textContent;
      button.textContent = 'Ativando...';

      try {
        let response;
        if (moduleType === 'indicador') {
          response = await fetch(`/portfolio/parceiros/${partnerId}/indicacao/ativar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });
        } else if (moduleType === 'comercial') {
          response = await fetch(`/portfolio/parceiros/${partnerId}/portfolio/ativar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ solution_ids: selectedSolutions }),
          });
        }

        if (!response || !response.ok) {
          throw new Error('Falha ao ativar modulo.');
        }

        if (this.selectedPartner && String(this.selectedPartner.id) === String(partnerId)) {
          if (moduleType === 'indicador') {
            if (!this.selectedPartner.modules.includes('indicador')) {
              this.selectedPartner.modules.push('indicador');
            }
            if (!this.selectedPartner.indicadorData) {
              this.selectedPartner.indicadorData = {
                leadsGenerated: 0,
                leadsNegotiation: 0,
                leadsClosed: 0,
                conversionRate: 0,
              };
            }
          } else if (moduleType === 'comercial') {
            if (!this.selectedPartner.modules.includes('comercial')) {
              this.selectedPartner.modules.push('comercial');
            }
            if (!this.selectedPartner.comercialSolutions) {
              this.selectedPartner.comercialSolutions = [];
            }
            const selected = this.comercialSolutionsCatalog.filter(solution =>
              selectedSolutions.includes(String(solution.id))
            );
            selected.forEach(solution => {
              const exists = this.selectedPartner.comercialSolutions.find(item => String(item.id) === String(solution.id));
              if (exists) return;
              this.selectedPartner.comercialSolutions.push({
                id: solution.id,
                name: solution.name,
                icon: solution.icon,
                color: solution.color,
                status: 'active',
                startDate: null,
                endDate: null,
                closedLeads: 0,
              });
            });
          }
          this.selectedPartner.status = 'active';
          this.renderList();
          this.renderDetail();
        }
      } catch (error) {
        showToast('error', 'Erro na ativação', error.message || 'Não foi possível ativar o módulo.');
      } finally {
        button.disabled = false;
        button.textContent = previousText;
      }
    });
  }

  ensureComercialModal() {
    let modal = document.querySelector('[data-comercial-modal]');
    if (modal) return modal;

    const wrapper = document.createElement('div');
    wrapper.className = 'solucao-edit-modal';
    wrapper.setAttribute('data-comercial-modal', '');
    wrapper.innerHTML = `
      <div class="solucao-edit-backdrop" data-comercial-close></div>
      <div class="solucao-edit-panel comercial-modal-panel">
        <div class="solucao-edit-header">
          <div>
            <h3>Ativar modulo Comercial</h3>
            <p>Selecione as solucoes que este parceiro tera acesso.</p>
          </div>
          <button class="solucao-edit-close" type="button" data-comercial-close>
            <i data-lucide="x"></i>
          </button>
        </div>
        <div class="comercial-solution-grid" data-comercial-solutions>
          <div class="solutions-empty">Carregando solucoes...</div>
        </div>
        <div class="comercial-modal-actions">
          <button type="button" class="solucao-confirm-cancel" data-comercial-close>Cancelar</button>
          <button type="button" class="solucao-confirm-accept" data-comercial-accept disabled>Ativar</button>
        </div>
      </div>
    `;

    document.body.appendChild(wrapper);
    lucide.createIcons();
    return wrapper;
  }

  async openComercialModal(partnerId) {
    const modal = this.ensureComercialModal();
    const solutionsContainer = modal.querySelector('[data-comercial-solutions]');
    const acceptButton = modal.querySelector('[data-comercial-accept]');
    modal.dataset.partnerId = partnerId;
    this.comercialSolutionsCatalog = [];
    modal._selectedSolutions = new Set();
    acceptButton.disabled = true;
    acceptButton.textContent = 'Ativar';

    const updateAcceptState = () => {
      const size = modal._selectedSolutions.size;
      acceptButton.disabled = size === 0;
      acceptButton.textContent = size > 0 ? `Ativar (${size})` : 'Ativar';
    };

    const handleSolutionClick = (event) => {
      const card = event.target.closest('[data-solution-id]');
      if (!card) return;
      const solutionId = card.getAttribute('data-solution-id');
      if (modal._selectedSolutions.has(solutionId)) {
        modal._selectedSolutions.delete(solutionId);
        card.classList.remove('selected');
      } else {
        modal._selectedSolutions.add(solutionId);
        card.classList.add('selected');
      }
      updateAcceptState();
    };

    solutionsContainer.replaceWith(solutionsContainer.cloneNode(false));
    const freshContainer = modal.querySelector('[data-comercial-solutions]');
    freshContainer.addEventListener('click', handleSolutionClick);
    freshContainer.innerHTML = '<div class="solutions-empty">Carregando solucoes...</div>';

    try {
      const response = await fetch('/portfolio/parceiros/solucoes-ativas');
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error('Nao foi possivel carregar as solucoes.');
      }
      this.comercialSolutionsCatalog = payload.solucoes || [];
      if (this.comercialSolutionsCatalog.length === 0) {
        freshContainer.innerHTML = '<div class="solutions-empty">Nenhuma solucao disponivel.</div>';
      } else {
        freshContainer.innerHTML = this.comercialSolutionsCatalog.map((solution) => {
          const accent = this.resolveAccentColor(solution.color);
          const gradientStart = this.withAlphaColor(accent, 0.16);
          const gradientEnd = this.withAlphaColor(accent, 0.04);
          return `
            <button type="button" class="comercial-solution-card" data-solution-id="${solution.id}" style="--solution-accent:${accent}; background: linear-gradient(135deg, ${gradientStart}, ${gradientEnd});">
              <div class="comercial-solution-icon">
                <i data-lucide="${solution.icon || 'layers'}"></i>
              </div>
              <div class="comercial-solution-info">
                <div class="comercial-solution-name">${solution.name}</div>
                <div class="comercial-solution-type">${solution.type || 'Solucao'}</div>
              </div>
            </button>
          `;
        }).join('');
        lucide.createIcons();
      }
    } catch (error) {
      freshContainer.innerHTML = '<div class="solutions-empty">Erro ao carregar solucoes.</div>';
    }

    modal.classList.add('open');

    return new Promise((resolve) => {
      const closeButtons = modal.querySelectorAll('[data-comercial-close]');
      const cleanup = () => {
        closeButtons.forEach((button) => {
          button.removeEventListener('click', onClose);
        });
        acceptButton.removeEventListener('click', onAccept);
      };

      const onClose = () => {
        modal.classList.remove('open');
        cleanup();
        resolve([]);
      };

      const onAccept = () => {
        const selected = Array.from(modal._selectedSolutions);
        modal.classList.remove('open');
        cleanup();
        resolve(selected);
      };

      closeButtons.forEach((button) => {
        button.addEventListener('click', onClose);
      });
      acceptButton.addEventListener('click', onAccept);
    });
  }

  resolveAccentColor(colorId) {
    if (!colorId) return 'hsl(var(--primary))';
    const trimmed = String(colorId).trim();
    if (trimmed.startsWith('#') || trimmed.startsWith('hsl(') || trimmed.startsWith('rgb(')) {
      return trimmed;
    }
    return `hsl(var(--${trimmed}))`;
  }

  withAlphaColor(color, alpha) {
    if (!color) return `hsl(var(--primary) / ${alpha})`;
    if (color.startsWith('hsl(')) {
      return this.withAlpha(color, alpha);
    }
    if (color.startsWith('#')) {
      const hex = color.replace('#', '');
      const normalized = hex.length === 3
        ? hex.split('').map((ch) => ch + ch).join('')
        : hex;
      const r = parseInt(normalized.slice(0, 2), 16);
      const g = parseInt(normalized.slice(2, 4), 16);
      const b = parseInt(normalized.slice(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    return color;
  }

  ensureIndicacaoModal() {
    let modal = document.querySelector('[data-indicacao-confirm-modal]');
    if (modal) return modal;

    const wrapper = document.createElement('div');
    wrapper.className = 'solucao-confirm-modal indicacao-confirm-modal';
    wrapper.setAttribute('data-indicacao-confirm-modal', '');
    wrapper.innerHTML = `
      <div class="solucao-confirm-backdrop" data-indicacao-confirm-close></div>
      <div class="solucao-confirm-panel">
        <div class="solucao-confirm-header">
          <div class="solucao-confirm-icon">
            <i data-lucide="sparkles"></i>
          </div>
          <div>
            <h3>Ativar modulo de indicacao</h3>
            <p>Deseja ativar este modulo para o parceiro selecionado?</p>
          </div>
        </div>
        <div class="solucao-confirm-actions">
          <button type="button" class="solucao-confirm-cancel" data-indicacao-confirm-close>Cancelar</button>
          <button type="button" class="solucao-confirm-accept" data-indicacao-confirm-accept>Ativar</button>
        </div>
      </div>
    `;

    document.body.appendChild(wrapper);
    lucide.createIcons();
    return wrapper;
  }

  openIndicacaoModal() {
    const modal = this.ensureIndicacaoModal();
    return new Promise((resolve) => {
      const closeButtons = modal.querySelectorAll('[data-indicacao-confirm-close]');
      const acceptButton = modal.querySelector('[data-indicacao-confirm-accept]');

      const cleanup = () => {
        closeButtons.forEach((button) => {
          button.removeEventListener('click', onClose);
        });
        if (acceptButton) {
          acceptButton.removeEventListener('click', onAccept);
        }
      };

      const onClose = () => {
        modal.classList.remove('open');
        cleanup();
        resolve(false);
      };

      const onAccept = () => {
        modal.classList.remove('open');
        cleanup();
        resolve(true);
      };

      closeButtons.forEach((button) => {
        button.addEventListener('click', onClose);
      });
      if (acceptButton) {
        acceptButton.addEventListener('click', onAccept);
      }

      modal.classList.add('open');
    });
  }

  bindPartnerActions() {
    document.addEventListener('click', async (event) => {
      const editBtn = event.target.closest('[data-action="edit-partner"]');
      if (editBtn) {
        const partnerId = editBtn.getAttribute('data-partner-id');
        if (partnerId) this.openEditPartnerModal(partnerId);
        return;
      }

      const deleteBtn = event.target.closest('[data-action="delete-partner"]');
      if (deleteBtn) {
        const partnerId = deleteBtn.getAttribute('data-partner-id');
        if (partnerId) this.openDeletePartnerModal(partnerId);
        return;
      }
    });
  }

  // ── Modal de confirmacao generico ──────────────────────────────
  ensureConfirmModal() {
    let modal = document.querySelector('[data-generic-confirm-modal]');
    if (modal) return modal;

    const wrapper = document.createElement('div');
    wrapper.className = 'solucao-confirm-modal';
    wrapper.setAttribute('data-generic-confirm-modal', '');
    wrapper.innerHTML = `
      <div class="solucao-confirm-backdrop" data-generic-confirm-close></div>
      <div class="solucao-confirm-panel">
        <div class="solucao-confirm-header">
          <div class="solucao-confirm-icon" data-generic-confirm-icon>
            <i data-lucide="alert-circle"></i>
          </div>
          <div>
            <h3 data-generic-confirm-title>Confirmar</h3>
            <p data-generic-confirm-msg>Tem certeza?</p>
          </div>
        </div>
        <div class="solucao-confirm-actions">
          <button type="button" class="solucao-confirm-cancel" data-generic-confirm-close>Cancelar</button>
          <button type="button" class="solucao-confirm-accept" data-generic-confirm-accept>Confirmar</button>
        </div>
      </div>
    `;

    document.body.appendChild(wrapper);
    lucide.createIcons();
    return wrapper;
  }

  /**
   * Abre um modal de confirmacao generico.
   * @param {Object} opts - { title, message, confirmText, icon, danger }
   * @returns {Promise<boolean>}
   */
  openConfirmModal({ title = 'Confirmar', message = 'Tem certeza?', confirmText = 'Confirmar', icon = 'alert-circle', danger = false } = {}) {
    const modal = this.ensureConfirmModal();
    modal.querySelector('[data-generic-confirm-title]').textContent = title;
    modal.querySelector('[data-generic-confirm-msg]').textContent = message;

    const iconEl = modal.querySelector('[data-generic-confirm-icon]');
    iconEl.style.color = danger ? 'hsl(var(--danger, 0 84% 60%))' : '';
    iconEl.innerHTML = `<i data-lucide="${icon}"></i>`;

    const acceptBtn = modal.querySelector('[data-generic-confirm-accept]');
    acceptBtn.textContent = confirmText;
    if (danger) {
      acceptBtn.style.backgroundColor = 'hsl(var(--danger, 0 84% 60%))';
      acceptBtn.style.borderColor = 'hsl(var(--danger, 0 84% 60%))';
    } else {
      acceptBtn.style.backgroundColor = '';
      acceptBtn.style.borderColor = '';
    }

    lucide.createIcons();
    modal.classList.add('open');

    return new Promise((resolve) => {
      const closeButtons = modal.querySelectorAll('[data-generic-confirm-close]');

      const cleanup = () => {
        closeButtons.forEach(b => b.removeEventListener('click', onClose));
        acceptBtn.removeEventListener('click', onAccept);
      };

      const onClose = () => {
        modal.classList.remove('open');
        cleanup();
        resolve(false);
      };

      const onAccept = () => {
        modal.classList.remove('open');
        cleanup();
        resolve(true);
      };

      closeButtons.forEach(b => b.addEventListener('click', onClose));
      acceptBtn.addEventListener('click', onAccept);
    });
  }

  // ── Editar parceiro ────────────────────────────────────────────
  ensureEditPartnerModal() {
    let modal = document.querySelector('[data-edit-partner-modal]');
    if (modal) return modal;

    const wrapper = document.createElement('div');
    wrapper.className = 'solucao-edit-modal';
    wrapper.setAttribute('data-edit-partner-modal', '');
    wrapper.innerHTML = `
      <div class="solucao-edit-backdrop" data-edit-partner-close></div>
      <div class="solucao-edit-panel" style="max-width: 480px;">
        <div class="solucao-edit-header">
          <div>
            <h3>Editar parceiro</h3>
            <p>Altere os dados cadastrais do parceiro.</p>
          </div>
          <button class="solucao-edit-close" type="button" data-edit-partner-close>
            <i data-lucide="x"></i>
          </button>
        </div>
        <form data-edit-partner-form style="display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem;">
          <div class="partner-edit-field" style="display: flex; flex-direction: column; gap: 0.25rem;">
            <label style="font-size: 0.875rem; font-weight: 500;">Nome</label>
            <input name="nome" type="text" required style="padding: 0.5rem 0.75rem; border: 1px solid hsl(var(--border)); border-radius: 0.375rem; font-size: 0.875rem; background: hsl(var(--background)); color: hsl(var(--foreground)); transition: background 0.2s, border-color 0.2s;" />
          </div>
          <div class="partner-edit-field" style="display: flex; flex-direction: column; gap: 0.25rem;">
            <label style="font-size: 0.875rem; font-weight: 500;">CNPJ</label>
            <input name="cnpj" type="text" style="padding: 0.5rem 0.75rem; border: 1px solid hsl(var(--border)); border-radius: 0.375rem; font-size: 0.875rem; background: hsl(var(--background)); color: hsl(var(--foreground)); transition: background 0.2s, border-color 0.2s;" />
          </div>
          <div class="partner-edit-field" style="display: flex; flex-direction: column; gap: 0.25rem;">
            <label style="font-size: 0.875rem; font-weight: 500;">Razao Social</label>
            <input name="razao_social" type="text" style="padding: 0.5rem 0.75rem; border: 1px solid hsl(var(--border)); border-radius: 0.375rem; font-size: 0.875rem; background: hsl(var(--background)); color: hsl(var(--foreground)); transition: background 0.2s, border-color 0.2s;" />
          </div>
        </form>
        <div class="comercial-modal-actions" style="display: flex; align-items: center; gap: 0.75rem;">
          <span data-edit-partner-change-count style="flex: 1; font-size: 0.8rem; color: hsl(var(--muted-foreground));"></span>
          <button type="button" class="solucao-confirm-cancel" data-edit-partner-close>Cancelar</button>
          <button type="button" class="solucao-confirm-accept" data-edit-partner-save disabled>Salvar</button>
        </div>
      </div>
    `;

    document.body.appendChild(wrapper);
    lucide.createIcons();
    return wrapper;
  }

  _setupEditChangeTracking(modal, initialValues) {
    const form = modal.querySelector('[data-edit-partner-form]');
    const saveBtn = modal.querySelector('[data-edit-partner-save]');
    const countLabel = modal.querySelector('[data-edit-partner-change-count]');
    const inputs = form.querySelectorAll('input');

    const checkChanges = () => {
      let changeCount = 0;
      inputs.forEach((input) => {
        const key = input.name;
        const initial = initialValues[key] || '';
        const current = input.value;
        const changed = current !== initial;
        const field = input.closest('.partner-edit-field');
        if (field) {
          if (changed) {
            input.style.background = '#dcfce7';
            input.style.borderColor = '#22c55e';
            changeCount++;
          } else {
            input.style.background = '';
            input.style.borderColor = '';
          }
        }
      });
      saveBtn.disabled = changeCount === 0;
      if (changeCount > 0) {
        countLabel.textContent = `${changeCount} alteracao(oes)`;
        countLabel.style.color = '#22c55e';
        countLabel.style.fontWeight = '500';
      } else {
        countLabel.textContent = '';
      }
      return changeCount;
    };

    inputs.forEach((input) => {
      input.addEventListener('input', checkChanges);
      input.addEventListener('change', checkChanges);
    });

    // Reset inicial
    checkChanges();

    return checkChanges;
  }

  async openEditPartnerModal(partnerId) {
    const partner = this.partners.find(p => String(p.id) === String(partnerId));
    if (!partner) return;

    const modal = this.ensureEditPartnerModal();
    const form = modal.querySelector('[data-edit-partner-form]');

    // Preenche valores iniciais
    const initialValues = {
      nome: partner.name || '',
      cnpj: partner.cnpj || '',
      razao_social: partner.razaoSocial || '',
    };
    form.querySelector('[name="nome"]').value = initialValues.nome;
    form.querySelector('[name="cnpj"]').value = initialValues.cnpj;
    form.querySelector('[name="razao_social"]').value = initialValues.razao_social;

    // Reset estilos verdes
    form.querySelectorAll('input').forEach((input) => {
      input.style.background = '';
      input.style.borderColor = '';
    });

    // Setup change tracking (campos ficam verdes ao alterar)
    const getChangeCount = this._setupEditChangeTracking(modal, initialValues);

    modal.classList.add('open');

    return new Promise((resolve) => {
      const closeButtons = modal.querySelectorAll('[data-edit-partner-close]');
      const saveButton = modal.querySelector('[data-edit-partner-save]');

      const cleanup = () => {
        closeButtons.forEach(b => b.removeEventListener('click', onClose));
        saveButton.removeEventListener('click', onSave);
        // Remove change listeners
        form.querySelectorAll('input').forEach((input) => {
          input.replaceWith(input.cloneNode(true));
        });
      };

      const onClose = () => {
        modal.classList.remove('open');
        cleanup();
        resolve(false);
      };

      const onSave = async () => {
        const nome = form.querySelector('[name="nome"]').value.trim();
        if (!nome) {
          showToast('error', 'Erro', 'O nome do parceiro e obrigatorio.');
          return;
        }

        const changeCount = getChangeCount();

        // ── Confirmacao antes de salvar ──
        modal.classList.remove('open');
        const confirmed = await this.openConfirmModal({
          title: 'Confirmar alteracoes',
          message: `Voce fez ${changeCount} alteracao(oes) nos dados do parceiro "${nome}". Deseja prosseguir?`,
          confirmText: 'Salvar alteracoes',
          icon: 'save',
        });

        if (!confirmed) {
          modal.classList.add('open');
          return;
        }

        saveButton.disabled = true;
        saveButton.textContent = 'Salvando...';
        modal.classList.add('open');

        try {
          const response = await fetch(`/portfolio/api/parceiros/${partnerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              nome: nome,
              cnpj: form.querySelector('[name="cnpj"]').value.trim() || null,
              razao_social: form.querySelector('[name="razao_social"]').value.trim() || null,
            }),
          });

          if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Erro ao salvar parceiro.');
          }

          partner.name = nome;
          partner.cnpj = form.querySelector('[name="cnpj"]').value.trim();
          partner.razaoSocial = form.querySelector('[name="razao_social"]').value.trim();

          this.renderList();
          this.renderDetail();
          showToast('success', 'Sucesso', 'Parceiro atualizado com sucesso.');

          modal.classList.remove('open');
          cleanup();
          resolve(true);
        } catch (error) {
          showToast('error', 'Erro', error.message || 'Nao foi possivel salvar.');
        } finally {
          saveButton.disabled = false;
          saveButton.textContent = 'Salvar';
        }
      };

      closeButtons.forEach(b => b.addEventListener('click', onClose));
      saveButton.addEventListener('click', onSave);
    });
  }

  // ── Excluir parceiro ───────────────────────────────────────────
  async openDeletePartnerModal(partnerId) {
    const partner = this.partners.find(p => String(p.id) === String(partnerId));
    if (!partner) return;

    // Primeira confirmacao
    const confirmed = await this.openConfirmModal({
      title: 'Excluir parceiro',
      message: `Deseja excluir o parceiro "${partner.name}"? Todos os dados de parceria e solucoes vinculadas serao removidos.`,
      confirmText: 'Sim, excluir',
      icon: 'alert-triangle',
      danger: true,
    });

    if (!confirmed) return;

    // Segunda confirmacao (acao irreversivel)
    const doubleConfirmed = await this.openConfirmModal({
      title: 'Confirmacao final',
      message: `Esta acao NAO pode ser desfeita. Confirma a exclusao de "${partner.name}"?`,
      confirmText: 'Excluir permanentemente',
      icon: 'trash-2',
      danger: true,
    });

    if (!doubleConfirmed) return;

    try {
      const response = await fetch(`/portfolio/api/parceiros/${partnerId}`, {
        method: 'DELETE',
      });

      if (response.status === 409) {
        const err = await response.json().catch(() => ({}));
        showToast('error', 'Nao permitido', err.detail || 'Parceiro possui leads vinculados e nao pode ser excluido.');
        return;
      }

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Erro ao excluir parceiro.');
      }

      this.partners = this.partners.filter(p => String(p.id) !== String(partnerId));
      this.filteredPartners = this.filteredPartners.filter(p => String(p.id) !== String(partnerId));
      this.selectedPartner = null;
      this.renderList();
      this.renderDetail();
      showToast('success', 'Sucesso', 'Parceiro excluido com sucesso.');
    } catch (error) {
      showToast('error', 'Erro', error.message || 'Nao foi possivel excluir.');
    }
  }

  renderInfoRow(icon, label, value) {
    return `
      <div class="info-row">
        <i data-lucide="${icon}"></i>
        <div>
          <div class="info-label">${label}</div>
          <div class="info-value">${value}</div>
        </div>
      </div>
    `;
  }

  renderSolutionRow(solution, partnerId) {
    const statusLabel = this.getSolutionStatusLabel(solution.status);
    const statusClass = this.getSolutionStatusClass(solution.status);
    const icon = solution.icon || 'layers';
    const accentColor = this.resolveAccentColor(solution.color);
    const period = solution.startDate && solution.endDate
      ? `${this.formatDate(solution.startDate)} - ${this.formatDate(solution.endDate)}`
      : '-';
    const gradientStart = this.withAlpha(accentColor, 0.18);
    const gradientEnd = this.withAlpha(accentColor, 0.04);

    const leadsGenerated = solution.leadsGenerated ?? 0;
    const leadsNegotiation = solution.leadsNegotiation ?? 0;
    const leadsClosed = solution.closedLeads ?? 0;
    const conversionRate = leadsGenerated > 0 ? Math.round((leadsClosed / leadsGenerated) * 100) : 0;

    // Get dynamic text colors based on background darkness
    const textColors = this.getTextColors(accentColor);

    return `
      <div class="solution-row" style="border-color: ${this.withAlpha(accentColor, 0.2)}; background: linear-gradient(135deg, ${gradientStart}, ${gradientEnd}); cursor: pointer;" onclick="window.partnersManager.openLeadSlideOver(${partnerId}, ${solution.id})">
        <div class="solution-avatar" style="background-color: ${accentColor};">
          <i data-lucide="${icon}"></i>
        </div>
        <div class="solution-main">
          <div class="solution-name" style="color: ${textColors.name};">${solution.name}</div>
          <div class="solution-meta">
            <span class="badge ${statusClass}">${statusLabel}</span>
            <span class="solution-period">${period}</span>
          </div>
        </div>
        <div class="solution-stats-grid">
          <div class="solution-stat">
            <div class="solution-stat-label" style="color: ${textColors.label};">Gerados</div>
            <div class="solution-stat-value" style="color: ${textColors.value};">${leadsGenerated}</div>
          </div>
          <div class="solution-stat">
            <div class="solution-stat-label" style="color: ${textColors.label};">Em negociacao</div>
            <div class="solution-stat-value" style="color: ${textColors.value};">${leadsNegotiation}</div>
          </div>
          <div class="solution-stat">
            <div class="solution-stat-label" style="color: ${textColors.label};">Fechamento</div>
            <div class="solution-stat-value" style="color: ${textColors.value};">${leadsClosed}</div>
          </div>
          <div class="solution-stat">
            <div class="solution-stat-label" style="color: ${textColors.label};">Taxa</div>
            <div class="solution-stat-value" style="color: ${textColors.value};">${conversionRate}%</div>
          </div>
        </div>
      </div>
    `;
  }

  async openLeadSlideOver(partnerId, solucaoId) {
    try {
      const response = await fetch(`/portfolio/api/leads/parceiro/${partnerId}`);
      if (!response.ok) throw new Error('Erro ao buscar leads');
      const data = await response.json();
      const leads = data.leads || [];
      const solucoes = data.solucoes || [];

      if (leads.length === 0) return;

      // Encontra o primeiro lead com essa solução, ou o primeiro lead geral
      const targetLead = leads.find(l => l.id_solucao === solucaoId) || leads[0];

      this.leadSlideOver.open(targetLead, leads, solucoes);
    } catch (error) {
      console.error('Erro ao abrir lead:', error);
    }
  }

  withAlpha(color, alpha) {
    if (color && color.startsWith('hsl(') && color.endsWith(')')) {
      return `${color.slice(0, -1)} / ${alpha})`;
    }
    return color;
  }

  /**
   * Calculate luminance from HSL color to determine if background is dark
   * Returns true if the color is dark (requires light text)
   */
  isDarkColor(color) {
    if (!color || !color.startsWith('hsl(')) {
      return false;
    }

    // If color uses CSS variable, resolve it to actual HSL value
    if (color.includes('var(--')) {
      color = this.resolveCssVariable(color);
    }

    // Extract lightness value from hsl(h, s%, l%)
    const match = color.match(/hsl\([\d.]+,\s*([\d.]+)%,\s*([\d.]+)%/);
    if (match) {
      const lightness = parseFloat(match[2]);
      // If lightness is below 50%, consider it dark
      return lightness < 50;
    }

    return false;
  }

  /**
   * Resolve CSS variable colors to their actual HSL values
   * Maps common color variables used in the system
   */
  resolveCssVariable(color) {
    // Extract variable name from hsl(var(--variable-name))
    const varMatch = color.match(/hsl\(var\(--([^)]+)\)\)/);
    if (!varMatch) return color;

    const varName = varMatch[1];

    // Map of CSS variables to their HSL values
    // These should match the colors defined in your CSS
    const colorMap = {
      'primary': 'hsl(210, 70%, 50%)',      // Blue - light
      'comercial': 'hsl(180, 65%, 45%)',        // Teal/Cyan - dark
      'indicador': 'hsl(280, 60%, 55%)',    // Purple - medium
      'success': 'hsl(142, 71%, 45%)',      // Green - dark
      'warning': 'hsl(38, 92%, 50%)',       // Orange - light
      'danger': 'hsl(0, 84%, 60%)',         // Red - light
      'muted': 'hsl(220, 14%, 96%)',        // Light gray - very light
    };

    return colorMap[varName] || 'hsl(210, 70%, 50%)'; // Default to primary
  }

  /**
   * Get appropriate text colors based on background darkness
   */
  getTextColors(accentColor) {
    const isDark = this.isDarkColor(accentColor);

    if (isDark) {
      return {
        name: '#e5e5e5',      // Light gray for solution name
        label: '#b8b8b8',     // Medium-light gray for labels
        value: '#ffffff',     // White for values (emphasis)
      };
    } else {
      return {
        name: 'inherit',      // Default dark text
        label: 'inherit',     // Default dark text
        value: 'inherit',     // Default dark text
      };
    }
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  }

  formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  getStatusLabel(status) {
    const labels = {
      'active': 'Ativo',
      'pending': 'Pendente',
      'blocked': 'Bloqueado'
    };
    return labels[status] || status;
  }

  getImplantationLabel(status) {
    const labels = {
      'pending': 'Pendente',
      'in_progress': 'Em Progresso',
      'completed': 'Concluído'
    };
    return labels[status] || status;
  }

  getImplantationBadgeClass(status) {
    const classes = {
      'pending': 'badge-pending',
      'in_progress': 'badge-active',
      'completed': 'badge-active'
    };
    return classes[status] || 'badge-pending';
  }

  getSolutionStatusLabel(status) {
    const labels = {
      active: 'Ativo',
      negotiation: 'Negociacao',
      closed: 'Encerrado'
    };
    return labels[status] || 'Ativo';
  }

  getSolutionStatusClass(status) {
    const classes = {
      active: 'badge-active',
      negotiation: 'badge-pending',
      closed: 'badge-blocked'
    };
    return classes[status] || 'badge-active';
  }
}

// Initialize as global for onclick handlers
window.partnersManager = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.partners-layout')) {
    window.partnersManager = new PartnersManager();
  }
});

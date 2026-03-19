class PartnerAcompanhamentoManager {
  constructor() {
    this.items = Array.isArray(window.PARTNER_KANBAN_DATA) ? window.PARTNER_KANBAN_DATA : [];
    this.solucoes = this.sortSolucoesGdFirst(Array.isArray(window.SOLUCOES_DATA) ? window.SOLUCOES_DATA : []);
    this.activeSolucaoId = this.getInitialSolucaoId();
    this.responsavelFilter = '__all__';
    this.searchFilter = '';
    this.draggingId = null;
    this.suppressCardClickUntil = 0;
    this.partnerSlideOver = null;
    this.partnerLeadsCache = {};
    this.comerciaisCache = null;
    this.init();
  }

  init() {
    const editBtn = document.getElementById('acompanhamento-editar-kanban');
    if (editBtn) editBtn.addEventListener('click', () => this.openKanbanEditor());

    this.renderServiceTabs();
    this.renderKanban();
    this.setStatus('Arraste os parceiros para alterar etapas.');
    this.ensurePartnerSlideOver();

    // Precarrega comerciais para resolver nomes no card por id_colab_comercial.
    this.fetchComerciais()
      .then(() => {
        this.enrichComercialNames();
        this.renderKanban();
      })
      .catch(() => {});
  }

  getInitialSolucaoId() {
    if (!Array.isArray(this.solucoes) || this.solucoes.length === 0) return null;
    const gd = this.solucoes.find((s) => this.normalizeText(s?.name || '') === 'gd');
    return gd ? gd.id : this.solucoes[0].id;
  }

  sortSolucoesGdFirst(solucoes) {
    return [...(solucoes || [])].sort((a, b) => {
      const nameA = this.normalizeText(a?.name || '');
      const nameB = this.normalizeText(b?.name || '');
      const weightA = (nameA === 'gd' || nameA.includes('geracao-distribuida')) ? 0 : 1;
      const weightB = (nameB === 'gd' || nameB.includes('geracao-distribuida')) ? 0 : 1;
      if (weightA !== weightB) return weightA - weightB;
      return nameA.localeCompare(nameB);
    });
  }

  getSolucaoById(id) {
    const target = String(id);
    return this.solucoes.find((s) => String(s.id) === target) || null;
  }

  switchSolucao(solucaoId) {
    this.activeSolucaoId = solucaoId;
    this.responsavelFilter = '__all__';
    this.searchFilter = '';
    this.renderServiceTabs();
    this.renderKanban();
  }

  renderServiceTabs() {
    const container = document.querySelector('.service-tabs');
    if (!container) return;
    container.innerHTML = this.solucoes.map((solucao) => `
      <button class="service-tab ${String(this.activeSolucaoId) === String(solucao.id) ? 'active' : ''}"
              data-solucao-tab="${this.escapeHtml(String(solucao.id))}">
        <i data-lucide="${solucao.icon || 'layers'}"></i>
        <span>${this.escapeHtml(solucao.name || 'Solucao')}</span>
      </button>
    `).join('');

    container.querySelectorAll('[data-solucao-tab]').forEach((btn) => {
      btn.addEventListener('click', () => this.switchSolucao(btn.getAttribute('data-solucao-tab')));
    });
    lucide.createIcons();
  }

  normalizeText(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-')
      .trim();
  }

  getOrderedEtapas(etapas) {
    return [...(Array.isArray(etapas) ? etapas : [])]
      .filter((etapa) => etapa && (etapa.ativo === undefined || etapa.ativo === 1 || etapa.ativo === true || etapa.ativo === '1'))
      .sort((a, b) => Number(a?.ordem_id || a?.id || 0) - Number(b?.ordem_id || b?.id || 0));
  }

  getEtapasForSolucao(solucaoId) {
    const solucao = this.getSolucaoById(solucaoId);
    if (solucao && Array.isArray(solucao.etapas) && solucao.etapas.length > 0) {
      return this.getOrderedEtapas(solucao.etapas);
    }
    return [];
  }

  filterItemsBySolucao() {
    const target = String(this.activeSolucaoId || '');
    return this.items.filter((item) => String(item.id_solucao) === target);
  }

  getComercialNome(item) {
    if (item?.colab_comercial_nome) return String(item.colab_comercial_nome);
    if (!Array.isArray(this.comerciaisCache) || this.comerciaisCache.length === 0) return null;

    const current = item && item.id_colab_comercial !== undefined && item.id_colab_comercial !== null
      ? String(item.id_colab_comercial)
      : '';
    if (!current) return null;

    const found = this.comerciaisCache.find((colab) => {
      const idCol = colab?.id_col !== undefined && colab?.id_col !== null ? String(colab.id_col) : '';
      const crm = colab?.id_crm_colab ? String(colab.id_crm_colab) : '';
      return current === idCol || current === crm;
    });
    return found?.nome ? String(found.nome) : null;
  }

  enrichComercialNames() {
    this.items.forEach((item) => {
      if (!item) return;
      if (item.colab_comercial_nome) return;
      const nome = this.getComercialNome(item);
      if (nome) item.colab_comercial_nome = nome;
    });
  }

  getResponsavelOptions(items) {
    const byId = new Map();
    (items || []).forEach((item) => {
      const id = item && item.id_colab_comercial !== undefined && item.id_colab_comercial !== null
        ? String(item.id_colab_comercial)
        : '';
      const nome = item && item.colab_comercial_nome ? String(item.colab_comercial_nome).trim() : '';
      if (!id || !nome) return;
      if (!byId.has(id)) byId.set(id, nome);
    });
    return Array.from(byId.entries()).map(([id, nome]) => ({ id, nome }));
  }

  applyResponsavelFilter(items) {
    if (!this.responsavelFilter || this.responsavelFilter === '__all__') return items;
    return (items || []).filter((item) => String(item.id_colab_comercial || '') === String(this.responsavelFilter));
  }

  applySearchFilter(items) {
    const term = String(this.searchFilter || '').trim().toLowerCase();
    if (!term) return items;
    return (items || []).filter((item) => {
      const searchable = [
        item?.name,
        item?.razao_social,
        item?.cnpj,
        item?.colab_comercial_nome,
      ];
      return searchable.some((value) => String(value || '').toLowerCase().includes(term));
    });
  }

  renderKanban() {
    const container = document.querySelector('.kanban-columns');
    if (!container) return;
    const board = document.querySelector('.kanban-board');
    if (!board) return;
    const activeEl = document.activeElement;
    const activeId = activeEl && activeEl.id ? activeEl.id : null;
    const activeStart = activeEl && typeof activeEl.selectionStart === 'number' ? activeEl.selectionStart : null;
    const activeEnd = activeEl && typeof activeEl.selectionEnd === 'number' ? activeEl.selectionEnd : null;

    const etapas = this.getEtapasForSolucao(this.activeSolucaoId);
    if (!this.activeSolucaoId || etapas.length === 0) {
      this.renderEmptyState('Nenhuma etapa configurada para esta solucao.');
      return;
    }

    const allItems = this.filterItemsBySolucao();
    const responsaveis = this.getResponsavelOptions(allItems);
    const filteredByResponsavel = this.applyResponsavelFilter(allItems);
    const items = this.applySearchFilter(filteredByResponsavel);

    let toolbar = board.querySelector('.kanban-toolbar-filters');
    if (!toolbar) {
      toolbar = document.createElement('div');
      toolbar.className = 'kanban-toolbar kanban-toolbar-filters';
      board.insertBefore(toolbar, container);
    }
    toolbar.innerHTML = `
      <div class="kanban-toolbar-item kanban-toolbar-item-search">
        <label class="kanban-toolbar-label" for="partner-kanban-search-filter">Buscar</label>
        <input
          id="partner-kanban-search-filter"
          class="kanban-toolbar-select kanban-toolbar-search-input"
          type="search"
          placeholder="Nome, empresa, CNPJ..."
          value="${this.escapeHtml(this.searchFilter)}"
        />
      </div>
      <div class="kanban-toolbar-item kanban-toolbar-item-responsavel">
        <label class="kanban-toolbar-label" for="partner-kanban-responsavel-filter">Responsavel</label>
        <select id="partner-kanban-responsavel-filter" class="kanban-toolbar-select">
          <option value="__all__">Todos</option>
          ${responsaveis.map((item) => `<option value="${this.escapeHtml(item.id)}" ${this.responsavelFilter === item.id ? 'selected' : ''}>${this.escapeHtml(item.nome)}</option>`).join('')}
        </select>
      </div>
    `;

    const responsavelSelect = toolbar.querySelector('#partner-kanban-responsavel-filter');
    if (responsavelSelect) {
      responsavelSelect.addEventListener('change', (event) => {
        this.responsavelFilter = event.target.value || '__all__';
        this.renderKanban();
      });
    }
    const searchInput = toolbar.querySelector('#partner-kanban-search-filter');
    if (searchInput) {
      searchInput.addEventListener('input', (event) => {
        this.searchFilter = String(event.target.value || '');
        this.renderKanban();
      });
    }

    container.innerHTML = etapas.map((etapa) => {
      const cards = items.filter((item) => Number(item.id_status_kanban) === Number(etapa.id));
      const totalValue = cards.reduce((sum, item) => sum + (item.value || 0), 0);
      return `
        <div class="kanban-column" data-etapa-id="${etapa.id}">
          <div class="kanban-column-header">
            <div class="kanban-column-title">
              <span class="stage-indicator" style="background-color: ${etapa.color_HEX || '#626D84'};"></span>
              <span class="column-name">${this.escapeHtml(etapa.nome_etapa || 'Etapa')}</span>
              <span class="column-count">${cards.length}</span>
            </div>
            <span class="column-total">${this.formatCurrency(totalValue)}</span>
          </div>
          <div class="kanban-cards-container" data-etapa-id="${etapa.id}">
            ${cards.map((item) => this.renderCard(item)).join('')}
          </div>
        </div>
      `;
    }).join('');

    this.setupDnD(container);
    lucide.createIcons();

    if (activeId) {
      const nextActive = board.querySelector(`#${activeId}`);
      if (nextActive) {
        nextActive.focus();
        if (typeof nextActive.setSelectionRange === 'function' && activeStart !== null && activeEnd !== null) {
          nextActive.setSelectionRange(activeStart, activeEnd);
        }
      }
    }
  }

  renderCard(item) {
    const cnpj = item.cnpj || '-';
    const comercialNome = this.getComercialNome(item) || '-';
    return `
      <button class="kanban-card" data-item-id="${this.escapeHtml(String(item.id || ''))}" draggable="true">
        <div class="kanban-card-header">
          <h4 class="kanban-card-name">${this.escapeHtml(item.name || '-')}</h4>
        </div>
        <div class="kanban-card-company">
          <i data-lucide="building-2"></i>
          <span>${this.escapeHtml(item.razao_social || '-')}</span>
        </div>
        <div class="kanban-card-company">
          <i data-lucide="user"></i>
          <span>${this.escapeHtml(comercialNome)}</span>
        </div>
        <div class="kanban-card-footer">
          <div class="kanban-card-date">
            <i data-lucide="badge-check"></i>
            <span>${this.escapeHtml(cnpj)}</span>
          </div>
        </div>
      </button>
    `;
  }

  setupDnD(container) {
    container.querySelectorAll('.kanban-card[data-item-id]').forEach((card) => {
      card.addEventListener('click', (event) => {
        if (Date.now() < this.suppressCardClickUntil) {
          event.preventDefault();
          return;
        }
        const id = card.getAttribute('data-item-id');
        if (!id) return;
        this.openPartnerSlideOver(id);
      });

      card.addEventListener('dragstart', (event) => {
        const id = card.getAttribute('data-item-id');
        if (!id || !event.dataTransfer) return;
        this.draggingId = id;
        event.dataTransfer.setData('text/plain', id);
        card.classList.add('is-dragging');
      });
      card.addEventListener('dragend', () => {
        card.classList.remove('is-dragging');
        this.draggingId = null;
      });
    });

    container.querySelectorAll('.kanban-cards-container[data-etapa-id]').forEach((zone) => {
      zone.addEventListener('dragover', (event) => {
        event.preventDefault();
        zone.classList.add('is-drop-target');
      });
      zone.addEventListener('dragleave', () => zone.classList.remove('is-drop-target'));
      zone.addEventListener('drop', async (event) => {
        event.preventDefault();
        zone.classList.remove('is-drop-target');
        const id = event.dataTransfer?.getData('text/plain') || this.draggingId;
        const etapa = parseInt(zone.getAttribute('data-etapa-id') || '', 10);
        if (!id || !Number.isFinite(etapa)) return;
        await this.moveItem(id, etapa);
      });
    });
  }

  async moveItem(itemId, targetEtapaId) {
    const item = this.items.find((x) => String(x.id) === String(itemId));
    if (!item) return;
    if (Number(item.id_status_kanban) === Number(targetEtapaId)) return;
    this.suppressCardClickUntil = Date.now() + 300;

    try {
      const response = await fetch('/portfolio/api/parceiros/kanban-status', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_comercial: Number(item.id_comercial),
          id_solucao: Number(item.id_solucao),
          id_status_kanban: Number(targetEtapaId),
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${response.status}`);
      }
      item.id_status_kanban = Number(targetEtapaId);
      this.renderKanban();
    } catch (error) {
      window.alert((error && error.message) ? error.message : 'Nao foi possivel atualizar etapa do parceiro.');
      this.renderKanban();
    }
  }

  async openKanbanEditor() {
    const solucao = this.getSolucaoById(this.activeSolucaoId);
    if (!solucao) return;
    const rows = this.getEtapasForSolucao(solucao.id).map((etapa, index) => `
      <div class="kanban-etapa-item" data-editor-row data-id="${etapa.id || index + 1}">
        <input type="color" class="kanban-etapa-color" value="${etapa.color_HEX || '#626D84'}" />
        <input type="text" class="kanban-etapa-name" value="${this.escapeHtml(etapa.nome_etapa || '')}" placeholder="Nome da etapa" style="flex: 1;" />
        <button type="button" class="registro-field-remove" data-remove-row>x</button>
      </div>
    `).join('');

    const modal = document.createElement('div');
    modal.className = 'solucao-edit-modal open';
    modal.innerHTML = `
      <div class="solucao-edit-backdrop" data-close></div>
      <div class="solucao-edit-panel">
        <div class="solucao-edit-header">
          <div><h3>Editar Kanban</h3><p>${this.escapeHtml(solucao.name || 'Solucao')}</p></div>
          <button class="solucao-edit-close" type="button" data-close><i data-lucide="x"></i></button>
        </div>
        <div class="kanban-editor">
          <div class="kanban-etapas-list" data-editor-list>${rows}</div>
          <button type="button" class="kanban-add-etapa" data-add-row style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: hsl(var(--primary)); color: white; border: none; border-radius: 4px; cursor: pointer;">Adicionar Etapa</button>
        </div>
        <div class="solucao-edit-actions">
          <button type="button" class="solucao-edit-cancel" data-close>Cancelar</button>
          <button type="button" class="solucao-edit-save" data-save>Salvar</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    lucide.createIcons();

    const close = () => modal.remove();
    modal.querySelectorAll('[data-close]').forEach((el) => el.addEventListener('click', close));

    modal.addEventListener('click', (event) => {
      const removeBtn = event.target.closest('[data-remove-row]');
      if (removeBtn) removeBtn.closest('[data-editor-row]')?.remove();
    });
    modal.querySelector('[data-add-row]')?.addEventListener('click', () => {
      const list = modal.querySelector('[data-editor-list]');
      if (!list) return;
      const row = document.createElement('div');
      row.className = 'kanban-etapa-item';
      row.setAttribute('data-editor-row', '');
      row.setAttribute('data-id', String(list.querySelectorAll('[data-editor-row]').length + 1));
      row.innerHTML = `
        <input type="color" class="kanban-etapa-color" value="#626D84" />
        <input type="text" class="kanban-etapa-name" value="" placeholder="Nome da etapa" style="flex: 1;" />
        <button type="button" class="registro-field-remove" data-remove-row>x</button>
      `;
      list.appendChild(row);
    });

    modal.querySelector('[data-save]')?.addEventListener('click', async () => {
      const payload = [];
      const rowsEl = Array.from(modal.querySelectorAll('[data-editor-row]'));
      rowsEl.forEach((row, index) => {
        const nome = row.querySelector('.kanban-etapa-name')?.value?.trim() || '';
        if (!nome) return;
        payload.push({
          id: Number(row.getAttribute('data-id') || index + 1),
          nome_etapa: nome,
          color_HEX: row.querySelector('.kanban-etapa-color')?.value || '#626D84',
          ativo: 1,
          ordem_id: index + 1,
          sucesso: 0,
          perdido: 0,
        });
      });

      try {
        const response = await fetch(`/portfolio/solucoes/${encodeURIComponent(String(solucao.id))}/kanban`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ kanban_etapas: payload }),
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.detail || `Erro ${response.status}`);
        }
        solucao.etapas = payload;
        this.renderKanban();
        close();
      } catch (error) {
        window.alert((error && error.message) ? error.message : 'Nao foi possivel salvar kanban.');
      }
    });
  }

  setStatus(message) {
    const el = document.getElementById('acompanhamento-status');
    if (el) el.textContent = message || '';
  }

  ensurePartnerSlideOver() {
    let el = document.getElementById('partnerSlideOver');
    if (!el) {
      el = document.createElement('div');
      el.id = 'partnerSlideOver';
      el.className = 'slide-over';
      el.innerHTML = `
        <div class="slide-over-backdrop" data-partner-slideover-close></div>
        <div class="slide-over-panel"></div>
      `;
      document.body.appendChild(el);
    }
    this.partnerSlideOver = el;
    const backdrop = el.querySelector('[data-partner-slideover-close]');
    if (backdrop) backdrop.addEventListener('click', () => this.closePartnerSlideOver());
  }

  async openPartnerSlideOver(itemId) {
    if (!this.partnerSlideOver) this.ensurePartnerSlideOver();
    const item = this.items.find((x) => String(x.id) === String(itemId));
    if (!item || !this.partnerSlideOver) return;

    const solucao = this.getSolucaoById(item.id_solucao);
    const etapas = this.getEtapasForSolucao(item.id_solucao);
    const etapa = etapas.find((e) => Number(e.id) === Number(item.id_status_kanban));
    const panel = this.partnerSlideOver.querySelector('.slide-over-panel');
    if (!panel) return;

    panel.innerHTML = `
      <div class="slide-over-header">
        <div class="slide-over-title">
          <h2>${this.escapeHtml(item.name || 'Parceiro')}</h2>
          <p>${this.escapeHtml(item.razao_social || '-')}</p>
        </div>
        <button class="slide-over-close" data-partner-slideover-close>
          <i data-lucide="x"></i>
        </button>
      </div>

      <div class="slide-over-content">
        <div class="slide-over-section">
          <h3 class="slide-over-section-title">Resumo do Parceiro</h3>
          <div class="slide-over-info-grid">
            <div class="slide-over-info-item">
              <i data-lucide="badge-check"></i>
              <div class="slide-over-info-content">
                <div class="slide-over-info-label">CNPJ</div>
                <div class="slide-over-info-value">${this.escapeHtml(item.cnpj || '-')}</div>
              </div>
            </div>
            <div class="slide-over-info-item">
              <i data-lucide="layers"></i>
              <div class="slide-over-info-content">
                <div class="slide-over-info-label">Solução</div>
                <div class="slide-over-info-value">${this.escapeHtml(solucao?.name || '-')}</div>
              </div>
            </div>
            <div class="slide-over-info-item">
              <i data-lucide="columns-3"></i>
              <div class="slide-over-info-content">
                <div class="slide-over-info-label">Etapa Atual</div>
                <div class="slide-over-info-value">${this.escapeHtml(etapa?.nome_etapa || '-')}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="slide-over-section">
          <h3 class="slide-over-section-title">Responsáveis</h3>
          <div class="slide-over-info-grid">
            <div class="slide-over-info-item">
              <i data-lucide="user-check"></i>
              <div class="slide-over-info-content">
                <div class="slide-over-info-label">Comercial Responsável</div>
                <select class="slide-over-info-select" data-partner-colab-comercial>
                  <option value="">Carregando...</option>
                </select>
              </div>
            </div>
            <div class="slide-over-info-item">
              <i data-lucide="briefcase-business"></i>
              <div class="slide-over-info-content">
                <div class="slide-over-info-label">Comercial Responsável</div>
                <select class="slide-over-info-select" data-partner-colab-comercial>
                  <option value="">Carregando...</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="slide-over-section">
          <h3 class="slide-over-section-title">Leads Vinculados</h3>
          <div id="partner-leads-container">
            <div style="padding: 1rem; border: 1px solid hsl(var(--border)); border-radius: 0.5rem; color: hsl(var(--muted-foreground));">
              Carregando leads do parceiro...
            </div>
          </div>
        </div>
      </div>

      <div class="slide-over-footer">
        <button class="slide-over-btn slide-over-btn-primary" data-save-responsaveis>
          Salvar Responsáveis
        </button>
        <button class="slide-over-btn slide-over-btn-secondary" data-partner-slideover-close>
          Fechar
        </button>
      </div>
    `;

    panel.querySelectorAll('[data-partner-slideover-close]').forEach((btn) => {
      btn.addEventListener('click', () => this.closePartnerSlideOver());
    });
    panel.querySelector('[data-save-responsaveis]')?.addEventListener('click', async () => {
      await this.savePartnerResponsaveis(panel, item);
    });
    this.partnerSlideOver.classList.add('open');
    lucide.createIcons();

    await this.populateResponsaveisSelects(panel, item);

    const leadsContainer = panel.querySelector('#partner-leads-container');
    if (leadsContainer) {
      const leads = await this.fetchPartnerLeads(item.id_comercial);
      this.renderPartnerLeads(leadsContainer, leads);
    }
  }

  closePartnerSlideOver() {
    if (!this.partnerSlideOver) return;
    this.partnerSlideOver.classList.remove('open');
  }

  async fetchPartnerLeads(partnerId) {
    const key = String(partnerId || '');
    if (!key) return [];
    if (Array.isArray(this.partnerLeadsCache[key])) return this.partnerLeadsCache[key];

    try {
      const response = await fetch(`/portfolio/api/leads/parceiro/${encodeURIComponent(key)}`);
      if (!response.ok) throw new Error(`Erro ${response.status}`);
      const payload = await response.json();
      const leads = Array.isArray(payload?.leads) ? payload.leads : [];
      this.partnerLeadsCache[key] = leads;
      return leads;
    } catch (_error) {
      this.partnerLeadsCache[key] = [];
      return [];
    }
  }

  async fetchComerciais() {
    if (Array.isArray(this.comerciaisCache)) return this.comerciaisCache;
    try {
      const response = await fetch('/portfolio/api/comerciais');
      if (!response.ok) throw new Error(`Erro ${response.status}`);
      const payload = await response.json();
      this.comerciaisCache = Array.isArray(payload?.comerciais) ? payload.comerciais : [];
    } catch (_error) {
      this.comerciaisCache = [];
    }
    return this.comerciaisCache;
  }

  async populateResponsaveisSelects(panel, item) {
    const comercialSelect = panel.querySelector('[data-partner-colab-comercial]');
    if (!comercialSelect) return;

    const comerciais = await this.fetchComerciais();
    const options = [`<option value="">Selecione</option>`];
    comerciais.forEach((colab) => {
      const crm = colab?.id_crm_colab ? String(colab.id_crm_colab) : '';
      const idCol = colab?.id_col !== undefined && colab?.id_col !== null ? String(colab.id_col) : '';
      const nome = colab?.nome ? String(colab.nome) : '';
      if (!nome) return;
      options.push(`<option value="${this.escapeHtml(crm || idCol)}" data-id-col="${this.escapeHtml(idCol)}">${this.escapeHtml(nome)}</option>`);
    });

    comercialSelect.innerHTML = options.join('');

    const currentComercial = item.id_colab_comercial ? String(item.id_colab_comercial) : '';

    if (currentComercial) {
      const byComercial = Array.from(comercialSelect.options).find((opt) => String(opt.dataset.idCol || '') === currentComercial || String(opt.value) === currentComercial);
      if (byComercial) comercialSelect.value = byComercial.value;
    }
  }

  async savePartnerResponsaveis(panel, item) {
    const comercialSelect = panel.querySelector('[data-partner-colab-comercial]');
    const saveBtn = panel.querySelector('[data-save-responsaveis]');
    if (!comercialSelect || !saveBtn) return;

    const selectedComercialOpt = comercialSelect.selectedOptions && comercialSelect.selectedOptions[0]
      ? comercialSelect.selectedOptions[0]
      : null;
    const selectedComercial = selectedComercialOpt && selectedComercialOpt.dataset?.idCol
      ? Number(selectedComercialOpt.dataset.idCol)
      : null;

    try {
      saveBtn.disabled = true;
      saveBtn.textContent = 'Salvando...';
      const response = await fetch('/portfolio/api/parceiros/responsaveis', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_comercial: Number(item.id_comercial),
          id_colab_comercial: Number.isFinite(selectedComercial) ? selectedComercial : null,
        }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${response.status}`);
      }

      item.id_colab_comercial = Number.isFinite(selectedComercial) ? selectedComercial : null;
      item.colab_comercial_nome = selectedComercialOpt ? selectedComercialOpt.textContent.trim() : null;
      this.renderKanban();
      saveBtn.textContent = 'Salvo';
      setTimeout(() => {
        saveBtn.textContent = 'Salvar Responsáveis';
      }, 1000);
    } catch (error) {
      window.alert((error && error.message) ? error.message : 'Nao foi possivel salvar responsaveis.');
      saveBtn.textContent = 'Salvar Responsáveis';
    } finally {
      saveBtn.disabled = false;
    }
  }

  renderPartnerLeads(container, leads) {
    const list = Array.isArray(leads) ? leads : [];
    if (list.length === 0) {
      container.innerHTML = `
        <div style="padding: 1rem; border: 1px dashed hsl(var(--border)); border-radius: 0.5rem; color: hsl(var(--muted-foreground));">
          Nenhum lead vinculado a este parceiro.
        </div>
      `;
      return;
    }

    const total = list.length;
    const fechamento = list.filter((lead) => this.normalizeText(lead.stage || '').includes('fech')).length;
    const andamento = total - fechamento;

    container.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem;">
        <div style="border: 1px solid hsl(var(--border)); border-radius: 0.5rem; padding: 0.65rem;">
          <div style="font-size: 0.75rem; color: hsl(var(--muted-foreground));">Total</div>
          <div style="font-size: 1rem; font-weight: 600;">${total}</div>
        </div>
        <div style="border: 1px solid hsl(var(--border)); border-radius: 0.5rem; padding: 0.65rem;">
          <div style="font-size: 0.75rem; color: hsl(var(--muted-foreground));">Em andamento</div>
          <div style="font-size: 1rem; font-weight: 600;">${andamento}</div>
        </div>
        <div style="border: 1px solid hsl(var(--border)); border-radius: 0.5rem; padding: 0.65rem;">
          <div style="font-size: 0.75rem; color: hsl(var(--muted-foreground));">Fechamento</div>
          <div style="font-size: 1rem; font-weight: 600;">${fechamento}</div>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.5rem;">
        ${list.map((lead) => `
          <div style="border: 1px solid hsl(var(--border)); border-radius: 0.5rem; padding: 0.65rem;">
            <div style="display: flex; justify-content: space-between; align-items: start; gap: 0.5rem;">
              <div>
                <div style="font-weight: 600; color: hsl(var(--foreground));">${this.escapeHtml(lead.name || '-')}</div>
                <div style="font-size: 0.78rem; color: hsl(var(--muted-foreground));">${this.escapeHtml(lead.company || lead.razao_social || '-')}</div>
              </div>
              <span style="font-size: 0.72rem; border: 1px solid hsl(var(--border)); border-radius: 999px; padding: 0.1rem 0.45rem; color: hsl(var(--muted-foreground));">
                ${this.escapeHtml(lead.stage || '-')}
              </span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderEmptyState(message) {
    const container = document.querySelector('.kanban-columns');
    if (!container) return;
    container.innerHTML = `
      <div class="kanban-column" style="width: 100%; max-width: none;">
        <div class="empty-state" style="height: 100%; min-height: 260px;">
          <i data-lucide="inbox"></i>
          <h3>Nenhum dado para exibir</h3>
          <p>${this.escapeHtml(message || 'Sem dados para montar o kanban.')}</p>
        </div>
      </div>
    `;
    lucide.createIcons();
  }

  escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(value);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.partnerAcompanhamentoManager = new PartnerAcompanhamentoManager();
});

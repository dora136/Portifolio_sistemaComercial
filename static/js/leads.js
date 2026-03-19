// Leads Kanban Module
class LeadsManager {
  constructor() {
    this.leads = [];
    this.solucoes = [];
    this.activeSolucaoId = null;
    this.selectedLead = null;
    this.slideOver = null;
    this.contractResponsaveis = [];
    this.contractResponsaveisLoaded = false;
    this.contractParceiros = [];
    this.contractParceirosLoaded = false;
    this.contractCustomColumnCount = 0;
    this.contractStateByKey = {};
    this.contractModalExisting = null;
    this.contractInitialState = null;
    this.responsavelFilter = '__all__';
    this.searchFilter = '';
    this.draggingLeadId = null;
    this.suppressCardClickUntil = 0;
    this.init();
  }

  init() {
    // Carrega soluções do backend
    if (window.SOLUCOES_DATA && window.SOLUCOES_DATA.length > 0) {
      this.solucoes = this.sortSolucoesGdFirst(window.SOLUCOES_DATA);
      this.activeSolucaoId = this.solucoes[0].id;
    }

    // Carrega leads
    if (window.LEADS_DATA) {
      this.leads = window.LEADS_DATA;
    }

    // Inicializa o slide-over independente
    this.slideOver = new LeadSlideOver({
      onSave: () => {
        this.renderKanban();
        this.preloadContractStatusForSuccessLeads();
      },
      onDelete: (lead) => {
        this.leads = this.leads.filter((item) => item.id !== lead.id);
        this.renderKanban();
      },
      canDelete: true,
    });

    this.render();
    this.preloadContractStatusForSuccessLeads();
  }

  getSolucaoById(id) {
    const target = String(id);
    return this.solucoes.find(s => String(s.id) === target);
  }

  sortSolucoesGdFirst(solucoes) {
    const normalize = (value) => String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
    return [...(solucoes || [])].sort((a, b) => {
      const nameA = normalize(a?.name || '');
      const nameB = normalize(b?.name || '');
      const weightA = (nameA === 'cloud' || nameA.includes('cloud computing')) ? 0 : 1;
      const weightB = (nameB === 'cloud' || nameB.includes('cloud computing')) ? 0 : 1;
      if (weightA !== weightB) return weightA - weightB;
      return nameA.localeCompare(nameB);
    });
  }

  getActiveSolucao() {
    return this.getSolucaoById(this.activeSolucaoId);
  }

  getEtapasForSolucao(solucaoId) {
    const solucao = this.getSolucaoById(solucaoId);
    if (solucao && solucao.etapas && solucao.etapas.length > 0) {
      return this.getOrderedEtapas(solucao.etapas, false);
    }
    // Fallback para etapas padrão
    return this.getOrderedEtapas([
      { id: 1, nome_etapa: "Triagem", color_HEX: "#626D84", ativo: 1, ordem_id: 1 },
      { id: 2, nome_etapa: "Reunião", color_HEX: "#2964D9", ativo: 1, ordem_id: 2 },
      { id: 3, nome_etapa: "Proposta", color_HEX: "#F59F0A", ativo: 1, ordem_id: 3 },
      { id: 4, nome_etapa: "Fechamento", color_HEX: "#16A249", ativo: 1, ordem_id: 4 },
    ], false);
  }

  normalizeStage(stage) {
    if (!stage) return '';
    return stage
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '-');
  }

  filterBySolucao(solucaoId) {
    const target = String(solucaoId);
    return this.leads.filter(lead => String(lead.id_solucao) === target);
  }

  filterByEtapa(leads, etapa) {
    const normalizedEtapa = this.normalizeStage(etapa.nome_etapa);
    return leads.filter(lead => {
      const normalizedLeadStage = this.normalizeStage(lead.stage);
      return lead.id_etapa === etapa.id || normalizedLeadStage === normalizedEtapa;
    });
  }

  switchSolucao(solucaoId) {
    this.activeSolucaoId = solucaoId;
    this.responsavelFilter = '__all__';
    this.searchFilter = '';
    this.render();
  }

  render() {
    this.renderServiceTabs();
    this.renderKanban();
  }

  renderServiceTabs() {
    const container = document.querySelector('.service-tabs');
    if (!container) return;

    container.innerHTML = this.solucoes.map(solucao => `
      <button class="service-tab ${this.activeSolucaoId === solucao.id ? 'active' : ''}"
              onclick="window.leadsManager.switchSolucao(${solucao.id})"
              style="${this.activeSolucaoId === solucao.id ? this.getActiveTabStyle(solucao.color) : ''}">
        <i data-lucide="${solucao.icon || 'layers'}"></i>
        <span>${solucao.name}</span>
      </button>
    `).join('');

    lucide.createIcons();
  }

  getActiveTabStyle(color) {
    if (color && color.startsWith('#')) {
      const foreground = this.getContrastingTextColor(color);
      return `--tab-accent: ${color}; --tab-accent-foreground: ${foreground};`;
    }
    const accent = this.getSolucaoBadgeColor(color || 'primary');
    const foreground = this.getContrastingTextColor(accent);
    return `--tab-accent: ${accent}; --tab-accent-foreground: ${foreground};`;
  }

  getContrastingTextColor(color) {
    if (!color) return 'hsl(var(--foreground))';
    const normalized = color.trim();

    if (normalized.startsWith('#')) {
      const rgb = this.hexToRgb(normalized);
      if (!rgb) return 'hsl(var(--foreground))';
      const luminance = (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255;
      return luminance < 0.55 ? '#ffffff' : 'hsl(var(--foreground))';
    }

    const lightness = this.getHslLightness(normalized);
    if (lightness !== null) {
      return lightness < 55 ? '#ffffff' : 'hsl(var(--foreground))';
    }

    return 'hsl(var(--foreground))';
  }

  getHslLightness(color) {
    const match = color.match(/hsl\(\s*[\d.]+\s*[,\s]\s*[\d.]+%\s*[,\s]\s*([\d.]+)%\s*\)/i);
    if (!match) return null;
    const lightness = parseFloat(match[1]);
    return Number.isNaN(lightness) ? null : lightness;
  }

  hexToRgb(hex) {
    const cleaned = hex.replace('#', '').trim();
    const normalized = cleaned.length === 3
      ? cleaned.split('').map(ch => ch + ch).join('')
      : cleaned;
    if (normalized.length !== 6) return null;
    const value = parseInt(normalized, 16);
    return {
      r: (value >> 16) & 255,
      g: (value >> 8) & 255,
      b: value & 255
    };
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

    const allLeadsBySolucao = this.filterBySolucao(this.activeSolucaoId);
    const responsaveis = this.getResponsavelOptions(allLeadsBySolucao);
    const filteredByResponsavel = this.applyResponsavelFilter(allLeadsBySolucao);
    const filteredLeads = this.applySearchFilter(filteredByResponsavel);
    const etapas = this.getEtapasForSolucao(this.activeSolucaoId);

    let toolbar = board.querySelector('.kanban-toolbar');
    if (!toolbar) {
      toolbar = document.createElement('div');
      toolbar.className = 'kanban-toolbar';
      board.insertBefore(toolbar, container);
    }
    toolbar.innerHTML = `
      <div class="kanban-toolbar-item kanban-toolbar-item-search">
        <label class="kanban-toolbar-label" for="kanban-search-filter">Buscar</label>
        <input
          id="kanban-search-filter"
          class="kanban-toolbar-select kanban-toolbar-search-input"
          type="search"
          placeholder="Nome, empresa, CNPJ..."
          value="${this.escapeHtml(this.searchFilter)}"
        />
      </div>
      <div class="kanban-toolbar-item kanban-toolbar-item-responsavel">
        <label class="kanban-toolbar-label" for="kanban-responsavel-filter">Responsavel</label>
        <select id="kanban-responsavel-filter" class="kanban-toolbar-select">
          <option value="__all__">Todos</option>
          ${responsaveis.map((item) => `<option value="${this.escapeHtml(item.id)}" ${this.responsavelFilter === item.id ? 'selected' : ''}>${this.escapeHtml(item.nome)}</option>`).join('')}
        </select>
      </div>
    `;
    const responsavelSelect = toolbar.querySelector('#kanban-responsavel-filter');
    if (responsavelSelect) {
      responsavelSelect.addEventListener('change', (event) => {
        this.responsavelFilter = event.target.value || '__all__';
        this.renderKanban();
      });
    }
    const searchInput = toolbar.querySelector('#kanban-search-filter');
    if (searchInput) {
      searchInput.addEventListener('input', (event) => {
        this.searchFilter = String(event.target.value || '');
        this.renderKanban();
      });
    }

    container.innerHTML = etapas.map(etapa => {
      const etapaLeads = this.filterByEtapa(filteredLeads, etapa);
      const totalValue = etapaLeads.reduce((sum, lead) => sum + (lead.value || 0), 0);

      return `
        <div class="kanban-column" data-etapa-id="${etapa.id}">
          <div class="kanban-column-header">
            <div class="kanban-column-title">
              <span class="stage-indicator" style="background-color: ${etapa.color_HEX || '#626D84'};"></span>
              <span class="column-name">${etapa.nome_etapa}</span>
              <span class="column-count">${etapaLeads.length}</span>
            </div>
            <span class="column-total">${this.formatCurrency(totalValue)}</span>
          </div>
          <div class="kanban-cards-container" data-etapa-id="${etapa.id}">
            ${etapaLeads.map(lead => this.renderCard(lead, etapa)).join('')}
          </div>
        </div>
      `;
    }).join('');

    this.setupKanbanInteractions(container);
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

  getResponsavelOptions(leads) {
    const byId = new Map();
    (leads || []).forEach((lead) => {
      const id = lead && lead.id_colab_comercial !== undefined && lead.id_colab_comercial !== null
        ? String(lead.id_colab_comercial)
        : '';
      const nome = lead && lead.colab_comercial_nome ? String(lead.colab_comercial_nome).trim() : '';
      if (!id || !nome) return;
      if (!byId.has(id)) byId.set(id, nome);
    });
    return Array.from(byId.entries()).map(([id, nome]) => ({ id, nome }));
  }

  applyResponsavelFilter(leads) {
    if (!this.responsavelFilter || this.responsavelFilter === '__all__') return leads;
    return (leads || []).filter((lead) => String(lead.id_colab_comercial || '') === String(this.responsavelFilter));
  }

  applySearchFilter(leads) {
    const term = String(this.searchFilter || '').trim().toLowerCase();
    if (!term) return leads;
    return (leads || []).filter((lead) => {
      const searchable = [
        lead?.name,
        lead?.company,
        lead?.razao_social,
        lead?.cnpj,
        lead?.colab_comercial_nome,
        lead?.representante_parceiro_nome,
      ];
      return searchable.some((value) => String(value || '').toLowerCase().includes(term));
    });
  }

  setupKanbanInteractions(container) {
    const cards = container.querySelectorAll('.kanban-card[data-lead-id]');
    cards.forEach((card) => {
      card.setAttribute('draggable', 'true');
      card.addEventListener('click', (event) => {
        if (Date.now() < this.suppressCardClickUntil) {
          event.preventDefault();
          return;
        }
        const leadId = card.getAttribute('data-lead-id');
        if (leadId) this.openSlideOver(leadId);
      });
      card.addEventListener('dragstart', (event) => {
        const leadId = card.getAttribute('data-lead-id');
        if (!leadId || !event.dataTransfer) return;
        this.draggingLeadId = leadId;
        event.dataTransfer.setData('text/plain', leadId);
        event.dataTransfer.effectAllowed = 'move';
        card.classList.add('is-dragging');
      });
      card.addEventListener('dragend', () => {
        card.classList.remove('is-dragging');
        this.draggingLeadId = null;
      });
    });

    const dropZones = container.querySelectorAll('.kanban-cards-container[data-etapa-id]');
    dropZones.forEach((zone) => {
      zone.addEventListener('dragover', (event) => {
        event.preventDefault();
        zone.classList.add('is-drop-target');
      });
      zone.addEventListener('dragleave', () => {
        zone.classList.remove('is-drop-target');
      });
      zone.addEventListener('drop', async (event) => {
        event.preventDefault();
        zone.classList.remove('is-drop-target');
        const leadId = event.dataTransfer?.getData('text/plain') || this.draggingLeadId;
        const targetEtapa = parseInt(zone.getAttribute('data-etapa-id') || '', 10);
        if (!leadId || !Number.isFinite(targetEtapa)) return;
        await this.moveLeadToEtapa(leadId, targetEtapa);
      });
    });
  }

  async moveLeadToEtapa(leadId, targetEtapaId) {
    const lead = this.leads.find((item) => String(item.id) === String(leadId));
    if (!lead) return;
    const currentEtapa = Number(lead.id_etapa || 0);
    if (currentEtapa === Number(targetEtapaId)) return;

    this.suppressCardClickUntil = Date.now() + 300;

    const informacoes = Array.isArray(lead.informacoes)
      ? lead.informacoes.map((field) => ({
          name: field?.name || '',
          type: field?.type || 'string',
          value: field?.value ?? null,
        }))
      : [];

    const payload = {
      id_comercial: Number(lead.id_comercial),
      id_colab_comercial: lead.id_colab_comercial !== undefined && lead.id_colab_comercial !== null && String(lead.id_colab_comercial).trim() !== ''
        ? String(lead.id_colab_comercial)
        : null,
      solucoes: [
        {
          id_solucao: Number(lead.id_solucao),
          id_etapa_kanban: Number(targetEtapaId),
          id_comercial_parceiro: lead.id_comercial_parceiro || null,
          informacoes,
        },
      ],
    };

    try {
      const response = await fetch('/portfolio/api/leads', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        let detail = err && err.detail ? err.detail : '';
        if (Array.isArray(detail)) {
          detail = detail
            .map((item) => {
              const loc = Array.isArray(item?.loc) ? item.loc.join('.') : '';
              const msg = item?.msg || '';
              return [loc, msg].filter(Boolean).join(': ');
            })
            .filter(Boolean)
            .join(' | ');
        } else if (detail && typeof detail !== 'string') {
          detail = JSON.stringify(detail);
        }
        throw new Error(detail || `Erro ${response.status}`);
      }

      lead.id_etapa = Number(targetEtapaId);
      const etapas = this.getEtapasForSolucao(lead.id_solucao);
      const etapa = etapas.find((item) => Number(item.id) === Number(targetEtapaId));
      if (etapa) lead.stage = etapa.nome_etapa;
      this.renderKanban();
      this.preloadContractStatusForSuccessLeads();
    } catch (error) {
      const message = error && error.message ? error.message : 'Nao foi possivel mover o lead.';
      window.alert(message);
      this.renderKanban();
    }
  }

  isSuccessEtapa(etapa) {
    if (!etapa) return false;
    const flag = etapa.sucesso;
    return flag === true || flag === 1 || flag === '1';
  }

  isLeadInSuccessEtapa(lead) {
    if (!lead) return false;
    const etapas = this.getEtapasForSolucao(lead.id_solucao);
    const etapaAtual = etapas.find((etapa) => {
      const stageById = lead.id_etapa === etapa.id;
      const stageByName = this.normalizeStage(lead.stage) === this.normalizeStage(etapa.nome_etapa);
      return stageById || stageByName;
    });
    return this.isSuccessEtapa(etapaAtual);
  }

  buildContractKeyFromLead(lead) {
    if (!lead) return '';
    const a = Number(lead.id_comercial || 0);
    const b = Number(lead.id_solucao || 0);
    const c = Number(lead.id_comercial_parceiro || 0);
    if (!a || !b || !c) return '';
    return `${a}|${b}|${c}`;
  }

  async fetchContratoByLead(lead) {
    const idComercialLead = Number(lead?.id_comercial || 0);
    const idSolucao = Number(lead?.id_solucao || 0);
    const idParceiro = Number(lead?.id_comercial_parceiro || 0);
    if (!idComercialLead || !idSolucao || !idParceiro) return { exists: false, contrato: null };

    const query = new URLSearchParams({
      id_comercial_lead: String(idComercialLead),
      id_solucao: String(idSolucao),
      id_comercial_parceiro: String(idParceiro),
    });
    const response = await fetch(`/portfolio/api/contratos-financeiro?${query.toString()}`);
    if (!response.ok) throw new Error(`Erro ${response.status}`);
    const payload = await response.json();
    return {
      exists: Boolean(payload?.exists),
      contrato: payload?.contrato || null,
    };
  }

  async ensureContractStatusForLead(lead, options = {}) {
    const key = this.buildContractKeyFromLead(lead);
    if (!key) return { loaded: true, exists: false, contrato: null };
    const force = options.force === true;
    const current = this.contractStateByKey[key];
    if (!force && current && current.loaded) return current;

    try {
      const data = await this.fetchContratoByLead(lead);
      const next = { loaded: true, exists: data.exists, contrato: data.contrato };
      this.contractStateByKey[key] = next;
      return next;
    } catch (_error) {
      const next = { loaded: true, exists: false, contrato: null };
      this.contractStateByKey[key] = next;
      return next;
    }
  }

  async preloadContractStatusForSuccessLeads() {
    const successLeads = this.leads.filter((lead) => this.isLeadInSuccessEtapa(lead));
    if (successLeads.length === 0) return;

    await Promise.all(
      successLeads.map((lead) => this.ensureContractStatusForLead(lead))
    );
    this.renderKanban();
  }

  resolveCadastroTargetByLead(lead) {
    const solucao = this.getSolucaoById(lead?.id_solucao);
    const normalizedName = this.normalizeStage(solucao?.name || '');
    if (normalizedName.includes('indicacao')) return 'outros';
    if (normalizedName === 'cloud' || normalizedName.includes('cloud-computing')) {
      return 'cloud-computing';
    }
    return 'modelo-comercial';
  }

  async openSuccessCadastro(event, encodedLeadId) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    const leadId = decodeURIComponent(encodedLeadId || '');
    const lead = this.leads.find((item) => String(item.id) === String(leadId));
    if (!lead) return;

    const state = await this.ensureContractStatusForLead(lead, { force: true });
    this.openContractModalForLead(lead, state && state.exists ? state.contrato : null);
  }

  resolveContractModelByLead(lead) {
    const solucao = this.getSolucaoById(lead?.id_solucao);
    const bySolucao = this.normalizeStage(solucao?.name || '');
    const byModelo = this.normalizeStage(lead?.modelo || '');
    const normalized = bySolucao || byModelo;

    if (normalized.includes('indicacao')) return 'outro';
    if (normalized === 'cloud' || normalized.includes('cloud-computing')) return 'cloud';
    return 'comercial';
  }

  ensureContractModalElement() {
    let modal = document.querySelector('[data-contract-create-modal]');
    if (modal) return modal;

    modal = document.createElement('div');
    modal.className = 'contract-create-modal';
    modal.setAttribute('data-contract-create-modal', '');
    modal.innerHTML = `
      <div class="contract-create-backdrop" onclick="window.leadsManager.closeContractModal()"></div>
      <div class="contract-create-panel" data-contract-create-panel></div>
    `;
    document.body.appendChild(modal);
    return modal;
  }

  openContractModalForLead(lead, existingContrato = null) {
    this.contractModalLead = lead;
    this.contractModalExisting = existingContrato;
    const modeloSalvo = this.normalizeStage(existingContrato?.infos_json?.modelo_contrato || '');
    if (modeloSalvo === 'cloud') this.contractModalModel = 'cloud';
    else if (modeloSalvo === 'outro') this.contractModalModel = 'outro';
    else this.contractModalModel = this.resolveContractModelByLead(lead);
    const modal = this.ensureContractModalElement();
    modal.classList.add('open');
    this.renderContractModalPanel();
  }

  closeContractModal() {
    const modal = document.querySelector('[data-contract-create-modal]');
    if (!modal) return;
    modal.classList.remove('open');
    this.contractModalExisting = null;
    this.contractInitialState = null;
  }

  switchContractModel(model) {
    this.contractModalModel = model;
    this.renderContractModalPanel();
  }

  renderContractModalPanel() {
    const modal = document.querySelector('[data-contract-create-modal]');
    const panel = modal ? modal.querySelector('[data-contract-create-panel]') : null;
    const lead = this.contractModalLead;
    const model = this.contractModalModel || 'comercial';
    if (!panel || !lead) return;

    panel.innerHTML = this.buildContractModalContent(model, lead);
    lucide.createIcons();
    this.enhanceContractModal(model);
  }

  normalizePlain(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\*/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  getProductByModel(model) {
    if (model === 'cloud') return 'Cloud Computing';
    if (model === 'outro') return 'Outros';
    return 'Modelo Comercial';
  }

  getResponsavelOptionsHtml() {
    const options = ['<option value="">Selecionar</option>'];
    (this.contractResponsaveis || []).forEach((item) => {
      const value = item && item.id !== undefined && item.id !== null ? String(item.id) : '';
      const label = item && item.nome ? String(item.nome) : '';
      if (!value || !label) return;
      options.push(`<option value="${this.escapeHtml(value)}">${this.escapeHtml(label)}</option>`);
    });
    return options.join('');
  }

  getParceiroOptionsHtml(fallbackLead = null) {
    const options = ['<option value="">Selecionar</option>'];
    (this.contractParceiros || []).forEach((item) => {
      const value = item && item.id !== undefined && item.id !== null ? String(item.id) : '';
      const label = item && item.nome ? String(item.nome) : '';
      if (!value || !label) return;
      options.push(`<option value="${this.escapeHtml(value)}">${this.escapeHtml(label)}</option>`);
    });

    const fallbackId = fallbackLead && fallbackLead.id_comercial_parceiro !== undefined && fallbackLead.id_comercial_parceiro !== null
      ? String(fallbackLead.id_comercial_parceiro)
      : '';
    const fallbackLabel = fallbackLead
      ? String(fallbackLead.parceiro || fallbackLead.representante_parceiro_nome || '').trim()
      : '';
    if (fallbackId && fallbackLabel && !(this.contractParceiros || []).some((item) => String(item.id) === fallbackId)) {
      options.push(`<option value="${this.escapeHtml(fallbackId)}">${this.escapeHtml(fallbackLabel)}</option>`);
    }
    return options.join('');
  }

  normalizeContractFieldKey(labelText) {
    const normalized = this.normalizePlain(labelText || '');
    if (normalized === 'parceiro') return 'parceiro';
    if (normalized === 'lead') return 'lead';
    if (normalized === 'produto') return 'produto';
    if (normalized.startsWith('respons')) return 'responsavel';
    if (normalized === 'status') return 'status';
    if (normalized.includes('parcel')) return 'num_parcelas';
    if (normalized.includes('observacao')) return 'observacao';
    if (normalized.includes('data de fechamento')) return 'data_fechamento';
    if (normalized.includes('data de emissao')) return 'data_emissao';
    if (normalized.includes('data de vencimento')) return 'data_vencimento';
    if (normalized.includes('inicio do pagamento')) return 'inicio_pagamento';
    if (normalized.includes('pagamento final')) return 'pagamento_final';
    if (normalized.includes('valor do contrato')) return 'valor_contrato';
    if (normalized.includes('valor bruto')) return 'valor_bruto';
    if (normalized.includes('valor de comissao')) return 'valor_comissao';
    if (normalized.includes('usuarios ativos')) return 'usuarios_ativos';
    if (normalized.includes('licencas')) return 'licencas';
    if (normalized.includes('provedor')) return 'provedor';
    if (normalized.includes('ambiente')) return 'ambiente';
    if (normalized.includes('total de meses')) return 'total_meses';
    if (normalized.includes('numero do pedido')) return 'numero_pedido';
    if (normalized.includes('% (percentual)')) return 'percentual';
    if (normalized.includes('sla')) return 'sla';
    return normalized.replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  parseNumberLoose(value) {
    if (value === null || value === undefined) return null;
    const raw = String(value).trim();
    if (!raw) return null;
    const sanitized = raw
      .replace(/\s+/g, '')
      .replace(/r\$/gi, '')
      .replace(/\./g, '')
      .replace(',', '.')
      .replace(/[^\d.-]/g, '');
    if (!sanitized) return null;
    const num = Number(sanitized);
    return Number.isFinite(num) ? num : null;
  }

  normalizeFieldValue(value) {
    if (value === null || value === undefined) return '';
    return String(value).trim();
  }

  collectContractFormState(panel) {
    if (!panel) return {};
    const state = {};

    const coreFields = Array.from(panel.querySelectorAll('[data-contract-field-key]'));
    coreFields.forEach((field) => {
      const key = field.getAttribute('data-contract-field-key');
      if (!key) return;
      const control = field.querySelector('input, select, textarea');
      if (!control) return;
      state[`field:${key}`] = this.normalizeFieldValue(control.value);
    });

    const parcelaRows = Array.from(panel.querySelectorAll('.contract-parcela-item'));
    parcelaRows.forEach((row, idx) => {
      state[`parcela:${idx}:ref_esperado`] = this.normalizeFieldValue(row.querySelector('[data-parcela-ref-esperado]')?.value);
      state[`parcela:${idx}:ref_real`] = this.normalizeFieldValue(row.querySelector('[data-parcela-ref-real]')?.value);
      state[`parcela:${idx}:valor_esperado`] = this.normalizeFieldValue(row.querySelector('[data-parcela-valor-esperado]')?.value);
      state[`parcela:${idx}:valor_real`] = this.normalizeFieldValue(row.querySelector('[data-parcela-valor-real]')?.value);
    });

    const customRows = Array.from(panel.querySelectorAll('.contract-custom-column-row'));
    customRows.forEach((row, idx) => {
      const inputs = row.querySelectorAll('input');
      state[`custom:${idx}:nome`] = this.normalizeFieldValue(inputs[0]?.value);
      state[`custom:${idx}:valor`] = this.normalizeFieldValue(inputs[1]?.value);
    });

    return state;
  }

  getContractChanges(panel) {
    if (!panel || !this.contractInitialState) return { count: 0, keys: [] };
    const current = this.collectContractFormState(panel);
    const allKeys = new Set([...Object.keys(this.contractInitialState), ...Object.keys(current)]);
    const changedKeys = [];
    allKeys.forEach((key) => {
      const from = this.normalizeFieldValue(this.contractInitialState[key]);
      const to = this.normalizeFieldValue(current[key]);
      if (from !== to) changedKeys.push(key);
    });
    return { count: changedKeys.length, keys: changedKeys };
  }

  refreshContractEditedStyles(panel) {
    if (!panel) return;
    panel.querySelectorAll('.contract-field-edited').forEach((node) => node.classList.remove('contract-field-edited'));
    if (!this.contractInitialState) return;

    const { keys } = this.getContractChanges(panel);
    const changed = new Set(keys);

    const coreFields = Array.from(panel.querySelectorAll('[data-contract-field-key]'));
    coreFields.forEach((field) => {
      const key = field.getAttribute('data-contract-field-key');
      const control = field.querySelector('input, select, textarea');
      if (!key || !control) return;
      if (changed.has(`field:${key}`)) {
        control.classList.add('contract-field-edited');
      }
    });

    const parcelaRows = Array.from(panel.querySelectorAll('.contract-parcela-item'));
    parcelaRows.forEach((row, idx) => {
      const refEsperado = row.querySelector('[data-parcela-ref-esperado]');
      const refReal = row.querySelector('[data-parcela-ref-real]');
      const valorEsperado = row.querySelector('[data-parcela-valor-esperado]');
      const valorReal = row.querySelector('[data-parcela-valor-real]');
      if (refEsperado && changed.has(`parcela:${idx}:ref_esperado`)) refEsperado.classList.add('contract-field-edited');
      if (refReal && changed.has(`parcela:${idx}:ref_real`)) refReal.classList.add('contract-field-edited');
      if (valorEsperado && changed.has(`parcela:${idx}:valor_esperado`)) valorEsperado.classList.add('contract-field-edited');
      if (valorReal && changed.has(`parcela:${idx}:valor_real`)) valorReal.classList.add('contract-field-edited');
    });

    const customRows = Array.from(panel.querySelectorAll('.contract-custom-column-row'));
    customRows.forEach((row, idx) => {
      const inputs = row.querySelectorAll('input');
      const nome = inputs[0];
      const valor = inputs[1];
      if (nome && changed.has(`custom:${idx}:nome`)) nome.classList.add('contract-field-edited');
      if (valor && changed.has(`custom:${idx}:valor`)) valor.classList.add('contract-field-edited');
    });
  }

  bindContractEditListeners(panel) {
    if (!panel || panel.dataset.editTrackingBound === 'true') return;
    const refresh = () => this.refreshContractEditedStyles(panel);
    panel.addEventListener('input', refresh);
    panel.addEventListener('change', refresh);
    panel.dataset.editTrackingBound = 'true';
  }

  showContractConfirmDialog(message) {
    return new Promise((resolve) => {
      const existing = document.querySelector('[data-contract-confirm-modal]');
      if (existing) existing.remove();

      const modal = document.createElement('div');
      modal.className = 'contract-confirm-modal';
      modal.setAttribute('data-contract-confirm-modal', '');
      modal.innerHTML = `
        <div class="contract-confirm-backdrop"></div>
        <div class="contract-confirm-panel" role="dialog" aria-modal="true" aria-label="Confirmar alterações">
          <h4>Confirmar alterações</h4>
          <p>${this.escapeHtml(message || 'Deseja prosseguir?')}</p>
          <div class="contract-confirm-actions">
            <button type="button" class="contract-confirm-btn secondary" data-contract-confirm-cancel>Cancelar</button>
            <button type="button" class="contract-confirm-btn primary" data-contract-confirm-ok>Prosseguir</button>
          </div>
        </div>
      `;

      const cleanup = (result) => {
        modal.classList.remove('open');
        setTimeout(() => modal.remove(), 120);
        resolve(result);
      };

      modal.querySelector('[data-contract-confirm-cancel]')?.addEventListener('click', () => cleanup(false));
      modal.querySelector('[data-contract-confirm-ok]')?.addEventListener('click', () => cleanup(true));
      modal.querySelector('.contract-confirm-backdrop')?.addEventListener('click', () => cleanup(false));

      document.body.appendChild(modal);
      requestAnimationFrame(() => modal.classList.add('open'));
    });
  }

  getContractFieldValueByKey(panel, key) {
    if (!panel || !key) return null;
    const field = panel.querySelector(`[data-contract-field-key="${key}"]`);
    if (!field) return null;
    const control = field.querySelector('input, select, textarea');
    if (!control) return null;
    const value = control.value;
    return value === '' ? null : value;
  }

  collectContractCustomColumns(panel) {
    const rows = Array.from(panel.querySelectorAll('.contract-custom-column-row'));
    return rows
      .map((row) => {
        const inputs = row.querySelectorAll('input');
        return {
          nome: (inputs[0] && inputs[0].value ? inputs[0].value.trim() : ''),
          valor: (inputs[1] && inputs[1].value ? inputs[1].value.trim() : ''),
        };
      })
      .filter((item) => item.nome || item.valor);
  }

  collectContractParcelas(panel) {
    const rows = Array.from(panel.querySelectorAll('.contract-parcela-item'));
    return rows.map((row) => {
      const expectedDate = row.querySelector('[data-parcela-ref-esperado]')?.value || null;
      const realDate = row.querySelector('[data-parcela-ref-real]')?.value || null;
      const expectedValueRaw = row.querySelector('[data-parcela-valor-esperado]')?.value || '';
      const realValueRaw = row.querySelector('[data-parcela-valor-real]')?.value || '';
      return {
        referencia_esperado: expectedDate,
        referencia_real: realDate,
        valor_esperado: this.parseNumberLoose(expectedValueRaw),
        valor_real: this.parseNumberLoose(realValueRaw),
      };
    });
  }

  async saveContractModal() {
    const panel = document.querySelector('[data-contract-create-panel]');
    const lead = this.contractModalLead;
    const model = this.contractModalModel || 'comercial';
    if (!panel || !lead) return;

    const idComercialLead = Number(lead.id_comercial || 0);
    const idSolucao = Number(lead.id_solucao || 0);
    const parceiroRaw = this.getContractFieldValueByKey(panel, 'parceiro');
    const idParceiro = Number(parceiroRaw || lead.id_comercial_parceiro || 0);
    if (!idComercialLead || !idSolucao) {
      if (typeof showToast === 'function') {
        showToast('error', 'Dados incompletos', 'Lead sem IDs obrigatórios para salvar contrato.');
      }
      return;
    }

    const responsavelRaw = this.getContractFieldValueByKey(panel, 'responsavel');
    const statusRaw = this.getContractFieldValueByKey(panel, 'status');
    const parcelasInput = panel.querySelector('[data-contract-parcelas-input]');
    const parcelasCount = Math.max(1, parseInt(parcelasInput?.value || '1', 10) || 1);
    const parcelas = this.collectContractParcelas(panel);
    const receitaAuto = this.computeReceitaFromParcelas(parcelas);
    const customColumns = this.collectContractCustomColumns(panel);
    const requiredChecks = [
      { key: 'parceiro', label: 'Parceiro' },
      { key: 'responsavel', label: 'Responsavel' },
      { key: 'status', label: 'Status' },
      { key: 'data_fechamento', label: 'Data de Fechamento' },
      { key: 'num_parcelas', label: 'Numero de Parcelas' },
    ];
    const missing = requiredChecks
      .map((item) => {
        if (item.key === 'num_parcelas') {
          return parcelasCount > 0 ? null : item.label;
        }
        const value = this.getContractFieldValueByKey(panel, item.key);
        if (!value) return item.label;
        if (item.key === 'status' && this.normalizePlain(value) === 'selecionar') return item.label;
        return null;
      })
      .filter(Boolean);
    if (missing.length > 0) {
      if (typeof showToast === 'function') {
        showToast('warning', 'Campos obrigatorios', `Preencha: ${missing.join(', ')}.`);
      }
      return;
    }

    const infosJson = {
      modelo_contrato: model,
      campos: {},
      colunas_personalizadas: customColumns,
    };

    Array.from(panel.querySelectorAll('[data-contract-field-key]')).forEach((field) => {
      const key = field.getAttribute('data-contract-field-key');
      if (!key || ['parceiro', 'lead', 'produto', 'responsavel', 'status', 'num_parcelas'].includes(key)) return;
      const control = field.querySelector('input, select, textarea');
      if (!control) return;
      const value = control.value;
      infosJson.campos[key] = value === '' ? null : value;
    });
    infosJson.campos.receita = receitaAuto;
    infosJson.campos.coluna_fixa_1 = receitaAuto;

    const payload = {
      id_contrato: this.contractModalExisting?.id_contrato || null,
      id_comercial_lead: idComercialLead,
      id_solucao: idSolucao,
      id_comercial_parceiro: idParceiro,
      id_responsavel: responsavelRaw ? Number(responsavelRaw) : null,
      status: statusRaw || null,
      num_parcelas: parcelasCount,
      infos_json: infosJson,
      parcelas: parcelas.map((item) => ({
        referencia_esperado: item.referencia_esperado,
        referencia_real: item.referencia_real,
        valor_esperado: item.valor_esperado,
        valor_real: item.valor_real,
      })),
    };

    if (this.contractModalExisting && this.contractModalExisting.id_contrato) {
      const { count } = this.getContractChanges(panel);
      const ok = await this.showContractConfirmDialog(`Você fez ${count} alterações. Deseja prosseguir?`);
      if (!ok) return;
    }

    const saveButton = panel.querySelector('.contract-btn-primary');
    if (saveButton) {
      saveButton.disabled = true;
      saveButton.textContent = 'Salvando...';
    }

    try {
      const response = await fetch('/portfolio/api/contratos-financeiro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok || result.ok === false) {
        throw new Error(result.detail || 'Falha ao salvar contrato.');
      }
      if (typeof showToast === 'function') {
        showToast('success', 'Contrato salvo', 'Contrato e parcelas gravados no banco.');
      }
      await this.ensureContractStatusForLead(lead, { force: true });
      this.renderKanban();
      this.closeContractModal();
    } catch (error) {
      if (typeof showToast === 'function') {
        showToast('error', 'Erro ao salvar', error.message || 'Não foi possível salvar o contrato.');
      }
    } finally {
      if (saveButton) {
        saveButton.disabled = false;
        saveButton.textContent = 'Salvar Contrato';
      }
    }
  }

  enhanceContractModal(model) {
    const panel = document.querySelector('[data-contract-create-panel]');
    if (!panel) return;
    this.bindContractEditListeners(panel);
    Promise.all([
      this.ensureContractResponsaveisLoaded(),
      this.ensureContractParceirosLoaded(),
    ]).finally(() => {
      this.applyContractModalEnhancements(panel, model);
      this.applyExistingContractToModal(this.contractModalExisting);
    });
    this.applyContractModalEnhancements(panel, model);
    this.applyExistingContractToModal(this.contractModalExisting);
  }

  applyContractModalEnhancements(panel, model) {
    const modelSwitcher = panel.querySelector('.contract-model-switch');
    if (modelSwitcher) modelSwitcher.style.display = 'none';

    const productValue = this.getProductByModel(model);
    const fieldLabels = Array.from(panel.querySelectorAll('.contract-field'));
    panel.querySelectorAll('.contract-grid > div').forEach((node) => {
      if (!node.classList.length && node.children.length === 0 && !String(node.textContent || '').trim()) {
        node.remove();
      }
    });

    fieldLabels.forEach((field) => {
      const labelNode = field.querySelector('span');
      const normalized = this.normalizePlain(labelNode ? labelNode.textContent : '');
      if (normalized.includes('receita')) {
        field.setAttribute('data-contract-receita-auto', '');
        const control = field.querySelector('input, textarea');
        if (control) {
          control.readOnly = true;
        }
      }
      const fieldKey = this.normalizeContractFieldKey(labelNode ? labelNode.textContent : '');
      if (fieldKey) field.setAttribute('data-contract-field-key', fieldKey);
      if (labelNode) {
        const cleanText = String(labelNode.textContent || '').replace(/\*/g, '').trim();
        labelNode.textContent = this.isRequiredContractField(fieldKey)
          ? `${cleanText} *`
          : cleanText;
      }
      field.classList.remove('contract-field-wide', 'contract-field-full');

      if (normalized === 'produto') {
        const oldSelect = field.querySelector('select');
        if (oldSelect) oldSelect.remove();
        let input = field.querySelector('input');
        if (!input) {
          input = document.createElement('input');
          field.appendChild(input);
        }
        input.value = productValue;
        input.readOnly = true;
        input.disabled = true;
      }

      if (normalized === 'parceiro') {
        const oldInput = field.querySelector('input');
        if (oldInput) oldInput.remove();
        let select = field.querySelector('select');
        if (!select) {
          select = document.createElement('select');
          field.appendChild(select);
        }
        select.innerHTML = this.getParceiroOptionsHtml(this.contractModalLead);
        const defaultPartnerId = this.contractModalLead && this.contractModalLead.id_comercial_parceiro !== undefined && this.contractModalLead.id_comercial_parceiro !== null
          ? String(this.contractModalLead.id_comercial_parceiro)
          : '';
        if (defaultPartnerId) {
          select.value = defaultPartnerId;
        }
      }

      if (normalized === 'lead') {
        const input = field.querySelector('input');
        if (input) {
          input.readOnly = true;
          input.disabled = true;
        }
      }

      if (normalized.startsWith('respons')) {
        const oldInput = field.querySelector('input');
        if (oldInput) oldInput.remove();
        let select = field.querySelector('select');
        if (!select) {
          select = document.createElement('select');
          field.appendChild(select);
        }
        select.innerHTML = this.getResponsavelOptionsHtml();
      }

      const pairLabels = [
        'parceiro',
        'lead',
        'data de emissao',
        'data de vencimento',
        'inicio do pagamento',
        'pagamento final',
        'numero da nf (1)',
        'numero da nf (2)',
        'numero de parcelas',
        'observacao',
      ];
      if (pairLabels.some((value) => normalized.includes(value))) {
        field.classList.add('contract-field-wide');
      }

      if (normalized.includes('numero de parcelas')) {
        field.classList.remove('contract-field-wide');
        field.classList.add('contract-field-full');
      }

      if (normalized.includes('observacao')) {
        field.classList.add('contract-field-full');
      }

      const input = field.querySelector('input');
      const textarea = field.querySelector('textarea');
      const labelText = this.normalizePlain(labelNode ? labelNode.textContent : '');
      if (input) {
        const placeholder = this.normalizePlain(input.placeholder || '');
        if (placeholder && placeholder === labelText) {
          input.placeholder = '';
        }
      }
      if (textarea) {
        const placeholder = this.normalizePlain(textarea.placeholder || '');
        if (placeholder && placeholder === labelText) {
          textarea.placeholder = '';
        }
      }
    });

    let parcelField = fieldLabels.find((field) => {
      const node = field.querySelector('span');
      const normalized = this.normalizePlain(node ? node.textContent : '');
      return normalized.includes('parcel');
    });

    if (!parcelField) {
      const grid = panel.querySelector('.contract-grid');
      if (grid) {
        const wrap = document.createElement('label');
        wrap.className = 'contract-field';
        wrap.innerHTML = '<span>Numero de Parcelas</span><input type="number" min="1" value="1" />';
        grid.appendChild(wrap);
        parcelField = wrap;
      }
    }

    if (parcelField) {
      const parcelInput = parcelField.querySelector('input');
      if (parcelInput) {
        parcelInput.type = 'number';
        parcelInput.min = '1';
        parcelInput.value = parcelInput.value || '1';
        parcelInput.setAttribute('data-contract-parcelas-input', '');
        parcelInput.oninput = () => this.updateParcelasPanel();
      }
    }

    this.ensureCustomColumnsSection(panel);
    this.ensureParcelasPanel(panel);
    this.updateParcelasPanel();
    this.syncReceitaFromParcelas(panel);
  }

  isRequiredContractField(fieldKey) {
    return ['responsavel', 'status', 'data_fechamento', 'num_parcelas'].includes(fieldKey || '');
  }

  ensureCustomColumnsSection(panel) {
    let section = panel.querySelector('[data-contract-custom-section]');
    if (section) return;
    section = document.createElement('div');
    section.className = 'contract-custom-columns';
    section.setAttribute('data-contract-custom-section', '');
    section.innerHTML = `
      <div class="contract-custom-columns-head">
        <strong>Colunas Personalizadas</strong>
        <button type="button" onclick="window.leadsManager.addContractCustomColumn()">+ Adicionar</button>
      </div>
      <div class="contract-custom-columns-list" data-contract-custom-columns-list>
        <p class="contract-custom-columns-empty" data-contract-custom-empty>Nenhuma coluna personalizada. Clique em "+ Adicionar" para criar.</p>
      </div>
    `;
    const form = panel.querySelector('.contract-form-body');
    if (form) {
      const parcelaBtn = form.querySelector('.contract-installments-btn');
      if (parcelaBtn) form.insertBefore(section, parcelaBtn);
      else form.appendChild(section);
    }
  }

  addContractCustomColumn() {
    const list = document.querySelector('[data-contract-custom-columns-list]');
    const empty = document.querySelector('[data-contract-custom-empty]');
    if (!list) return;
    this.contractCustomColumnCount += 1;
    if (empty) empty.style.display = 'none';
    const idx = this.contractCustomColumnCount;
    list.insertAdjacentHTML('beforeend', `
      <div class="contract-custom-column-row">
        <input placeholder="Nome da coluna ${idx}" />
        <input placeholder="Valor" />
        <button type="button" class="contract-custom-column-remove" onclick="window.leadsManager.removeContractCustomColumn(this)" aria-label="Excluir coluna">×</button>
      </div>
    `);
  }

  removeContractCustomColumn(button) {
    const row = button ? button.closest('.contract-custom-column-row') : null;
    if (!row) return;
    row.remove();

    const list = document.querySelector('[data-contract-custom-columns-list]');
    const empty = document.querySelector('[data-contract-custom-empty]');
    if (!list || !empty) return;
    const hasRows = list.querySelectorAll('.contract-custom-column-row').length > 0;
    empty.style.display = hasRows ? 'none' : '';
  }

  ensureParcelasPanel(panel) {
    const button = panel.querySelector('.contract-installments-btn');
    if (!button) return;
    if (!button.hasAttribute('data-contract-parcelas-btn')) {
      button.setAttribute('data-contract-parcelas-btn', '');
      button.onclick = null;
      button.innerHTML = '<i data-lucide="file-text"></i><span data-contract-parcelas-label>Parcelas do Contrato (1)</span>';
      lucide.createIcons();
    }

    let wrap = panel.querySelector('[data-contract-parcelas-wrap]');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.className = 'contract-parcelas-wrap';
      wrap.setAttribute('data-contract-parcelas-wrap', '');
      wrap.innerHTML = '<div class="contract-parcelas-grid" data-contract-parcelas-grid></div>';
      button.insertAdjacentElement('afterend', wrap);
    }
    wrap.classList.add('open');
  }

  updateParcelasPanel() {
    const panel = document.querySelector('[data-contract-create-panel]');
    if (!panel) return;
    const input = panel.querySelector('[data-contract-parcelas-input]');
    const label = panel.querySelector('[data-contract-parcelas-label]');
    const grid = panel.querySelector('[data-contract-parcelas-grid]');
    if (!input || !label || !grid) return;
    const countRaw = parseInt(input.value || '1', 10);
    const count = Number.isFinite(countRaw) && countRaw > 0 ? countRaw : 1;
    input.value = String(count);
    label.textContent = `Parcelas do Contrato (${count})`;
    grid.innerHTML = `
      <div class="contract-parcelas-head">
        <span>Parcela</span>
        <span>Data Esperada</span>
        <span>Data Real</span>
        <span>Valor Esperado</span>
        <span>Valor Real</span>
      </div>
      ${Array.from({ length: count }).map((_, i) => `
        <div class="contract-parcela-item">
          <div class="contract-parcela-index">${i + 1}</div>
          <input type="date" data-parcela-ref-esperado />
          <input type="date" data-parcela-ref-real />
          <input data-parcela-valor-esperado />
          <input data-parcela-valor-real />
        </div>
      `).join('')}
    `;
    grid.querySelectorAll('[data-parcela-valor-esperado], [data-parcela-valor-real]').forEach((input) => {
      input.addEventListener('input', () => this.syncReceitaFromParcelas(panel));
      input.addEventListener('change', () => this.syncReceitaFromParcelas(panel));
    });
    this.syncReceitaFromParcelas(panel);
    this.refreshContractEditedStyles(panel);
  }

  computeReceitaFromParcelas(parcelas) {
    return (parcelas || []).reduce((sum, item) => {
      const esperado = this.parseNumberLoose(item?.valor_esperado);
      const real = this.parseNumberLoose(item?.valor_real);
      return sum + (esperado === null ? (real || 0) : esperado);
    }, 0);
  }

  syncReceitaFromParcelas(panel) {
    if (!panel) return;
    const parcelas = this.collectContractParcelas(panel);
    const receita = this.computeReceitaFromParcelas(parcelas);
    const receitaFmt = Number(receita || 0).toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    ['receita', 'coluna_fixa_1'].forEach((key) => {
      const field = panel.querySelector(`[data-contract-field-key="${key}"]`);
      if (!field) return;
      const control = field.querySelector('input, textarea');
      if (!control) return;
      control.value = receitaFmt;
      control.readOnly = true;
    });
  }

  applyExistingContractToModal(existingContrato) {
    if (!existingContrato) return;
    const panel = document.querySelector('[data-contract-create-panel]');
    if (!panel) return;

    const infos = existingContrato.infos_json || {};
    const campos = infos.campos || {};
    const parcelas = Array.isArray(existingContrato.parcelas) ? existingContrato.parcelas : [];

    // campos básicos em colunas próprias
    const statusField = panel.querySelector('[data-contract-field-key="status"] select');
    if (statusField && existingContrato.status) {
      statusField.value = String(existingContrato.status);
    }
    const parceiroField = panel.querySelector('[data-contract-field-key="parceiro"] select');
    if (parceiroField && existingContrato.id_comercial_parceiro !== null && existingContrato.id_comercial_parceiro !== undefined) {
      parceiroField.value = String(existingContrato.id_comercial_parceiro);
    }
    const respField = panel.querySelector('[data-contract-field-key="responsavel"] select');
    if (respField && existingContrato.id_responsavel !== null && existingContrato.id_responsavel !== undefined) {
      respField.value = String(existingContrato.id_responsavel);
    }

    // campos dinâmicos do JSON
    Object.entries(campos).forEach(([key, value]) => {
      const field = panel.querySelector(`[data-contract-field-key="${key}"]`);
      if (!field) return;
      const control = field.querySelector('input, select, textarea');
      if (!control) return;
      control.value = value === null || value === undefined ? '' : String(value);
    });

    // colunas personalizadas
    const customList = panel.querySelector('[data-contract-custom-columns-list]');
    const customEmpty = panel.querySelector('[data-contract-custom-empty]');
    const customColumns = Array.isArray(infos.colunas_personalizadas) ? infos.colunas_personalizadas : [];
    if (customList) {
      customList.innerHTML = '';
      customColumns.forEach((col, idx) => {
        const nome = col && col.nome ? this.escapeHtml(String(col.nome)) : '';
        const valor = col && col.valor ? this.escapeHtml(String(col.valor)) : '';
        customList.insertAdjacentHTML('beforeend', `
          <div class="contract-custom-column-row">
            <input placeholder="Nome da coluna ${idx + 1}" value="${nome}" />
            <input placeholder="Valor" value="${valor}" />
            <button type="button" class="contract-custom-column-remove" onclick="window.leadsManager.removeContractCustomColumn(this)" aria-label="Excluir coluna">×</button>
          </div>
        `);
      });
      if (customEmpty) customEmpty.style.display = customColumns.length > 0 ? 'none' : '';
      this.contractCustomColumnCount = customColumns.length;
    }

    // parcelas
    const parcelasInput = panel.querySelector('[data-contract-parcelas-input]');
    const parcelasCount = Math.max(1, parcelas.length || Number(existingContrato.num_colunas || 0) || 1);
    if (parcelasInput) {
      parcelasInput.value = String(parcelasCount);
      this.updateParcelasPanel();
    }

    const rows = Array.from(panel.querySelectorAll('.contract-parcela-item'));
    rows.forEach((row, idx) => {
      const parcela = parcelas[idx] || {};
      const refEsperado = row.querySelector('[data-parcela-ref-esperado]');
      const refReal = row.querySelector('[data-parcela-ref-real]');
      const valorEsperado = row.querySelector('[data-parcela-valor-esperado]');
      const valorReal = row.querySelector('[data-parcela-valor-real]');
      if (refEsperado) refEsperado.value = parcela.referencia_esperado || '';
      if (refReal) refReal.value = parcela.referencia_real || '';
      if (valorEsperado) valorEsperado.value = parcela.valor_esperado === null || parcela.valor_esperado === undefined ? '' : String(parcela.valor_esperado);
      if (valorReal) valorReal.value = parcela.valor_real === null || parcela.valor_real === undefined ? '' : String(parcela.valor_real);
    });
    this.syncReceitaFromParcelas(panel);

    this.contractInitialState = this.collectContractFormState(panel);
    this.refreshContractEditedStyles(panel);
  }

  async ensureContractResponsaveisLoaded() {
    if (this.contractResponsaveisLoaded) return;
    this.contractResponsaveisLoaded = true;
    try {
      const response = await fetch('/portfolio/api/comerciais');
      if (!response.ok) {
        this.contractResponsaveis = [];
        return;
      }
      const payload = await response.json();
      const comerciais = Array.isArray(payload.comerciais) ? payload.comerciais : [];
      this.contractResponsaveis = comerciais
        .map((item) => ({
          id: item && item.id_col !== undefined && item.id_col !== null ? item.id_col : null,
          nome: item && item.nome ? String(item.nome).trim() : '',
        }))
        .filter((item) => item.id !== null && item.nome);
    } catch (_error) {
      this.contractResponsaveis = [];
    }
  }

  async ensureContractParceirosLoaded() {
    if (this.contractParceirosLoaded) return;
    this.contractParceirosLoaded = true;
    try {
      const response = await fetch('/portfolio/api/parceiros');
      if (!response.ok) {
        this.contractParceiros = [];
        return;
      }
      const payload = await response.json();
      const parceiros = Array.isArray(payload.parceiros) ? payload.parceiros : [];
      this.contractParceiros = parceiros
        .map((item) => ({
          id: item && item.id !== undefined && item.id !== null ? item.id : null,
          nome: item && item.nome ? String(item.nome).trim() : '',
        }))
        .filter((item) => item.id !== null && item.nome);
    } catch (_error) {
      this.contractParceiros = [];
    }
  }

  buildContractModalContent(model, lead) {
    const partner = this.escapeHtml(String(lead.parceiro || lead.representante_parceiro_nome || 'Parceiro'));
    const leadName = this.escapeHtml(String(lead.name || lead.nome_fantasia || 'Lead'));
    const isEdit = Boolean(this.contractModalExisting && this.contractModalExisting.id_contrato);
    return `
      <div class="contract-modal-header">
        <div>
          <h3>${isEdit ? 'Contrato Financeiro' : 'Cadastrar Novo Contrato'}</h3>
          <p>${isEdit ? 'Visualize e edite os dados do contrato.' : 'Selecione o modelo e preencha os dados do contrato.'}</p>
        </div>
        <button type="button" class="contract-modal-close" onclick="window.leadsManager.closeContractModal()">×</button>
      </div>

      <div class="contract-model-switch">
        <button type="button" class="contract-model-btn ${model === 'cloud' ? 'active' : ''}" onclick="window.leadsManager.switchContractModel('cloud')">
          <strong>Cloud</strong>
          <small>Cloud Computing</small>
        </button>
        <button type="button" class="contract-model-btn ${model === 'comercial' ? 'active' : ''}" onclick="window.leadsManager.switchContractModel('comercial')">
          <strong>Comercial</strong>
          <small>Cyber, Consulting, etc.</small>
        </button>
        <button type="button" class="contract-model-btn ${model === 'outro' ? 'active' : ''}" onclick="window.leadsManager.switchContractModel('outro')">
          <strong>Outro</strong>
          <small>Modelo personalizável</small>
        </button>
      </div>

      <form class="contract-form-body">
        ${this.buildContractFieldsByModel(model, partner, leadName)}
        <button type="button" class="contract-installments-btn">
          <i data-lucide="file-text"></i>
          Gerenciar Parcelas (1)
        </button>
      </form>

      <div class="contract-modal-footer">
        <button type="button" class="contract-btn contract-btn-secondary" onclick="window.leadsManager.closeContractModal()">Cancelar</button>
        <button type="button" class="contract-btn contract-btn-primary" onclick="window.leadsManager.saveContractModal()">${isEdit ? 'Salvar Alterações' : 'Salvar Contrato'}</button>
      </div>
    `;
  }

  buildContractFieldsByModel(model, partner, leadName) {
    const statusSelect = `
      <label class="contract-field">
        <span>Status</span>
        <select>
          <option value="">Selecionar</option>
          <option>Ativo</option>
          <option>Pendente</option>
          <option>Pago</option>
        </select>
      </label>
    `;

    if (model === 'cloud') {
      return `
        <div class="contract-grid contract-grid-3">
          <label class="contract-field"><span>Parceiro</span><input value="${partner}" /></label>
          <label class="contract-field"><span>Lead</span><input value="${leadName}" /></label>
          <div></div>
          <label class="contract-field"><span>Produto</span><input value="Cloud Computing" readonly /></label>
          <label class="contract-field"><span>Responsável</span><input placeholder="Responsável" /></label>
          ${statusSelect}
          <label class="contract-field"><span>Data de Fechamento</span><input type="date" /></label>
          <label class="contract-field"><span>Usuarios Ativos</span><input placeholder="Usuarios Ativos" /></label>
          <label class="contract-field"><span>Provedor</span><input placeholder="Provedor" /></label>
          <label class="contract-field"><span>Valor do Contrato</span><input placeholder="Valor do Contrato" /></label>
          <label class="contract-field"><span>% (Percentual)</span><input placeholder="% (Percentual)" /></label>
          <label class="contract-field"><span>Licencas</span><input placeholder="Licencas" /></label>
          <label class="contract-field"><span>SLA</span><input placeholder="SLA" /></label>
        </div>
      `;
    }

    if (model === 'outro') {
      return `
        <div class="contract-grid contract-grid-3">
          <label class="contract-field"><span>Parceiro</span><input value="${partner}" /></label>
          <label class="contract-field"><span>Lead</span><input value="${leadName}" /></label>
          <div></div>
          <label class="contract-field"><span>Produto</span><input placeholder="Produto" /></label>
          <label class="contract-field"><span>Responsável</span><input placeholder="Responsável" /></label>
          ${statusSelect}
          <label class="contract-field"><span>Data de Fechamento</span><input type="date" /></label>
          <label class="contract-field"><span>Valor da Fatura</span><input placeholder="Valor da Fatura" /></label>
          <label class="contract-field"><span>Número de Parcelas</span><input placeholder="Número de Parcelas" /></label>
        </div>
        <div class="contract-custom-columns">
          <div class="contract-custom-columns-head">
            <strong>Colunas Personalizadas</strong>
            <button type="button">+ Adicionar</button>
          </div>
          <p>Nenhuma coluna personalizada. Clique em "+ Adicionar" para criar.</p>
        </div>
      `;
    }

    return `
      <div class="contract-grid contract-grid-3">
        <label class="contract-field"><span>Parceiro</span><input value="${partner}" /></label>
        <label class="contract-field"><span>Lead</span><input value="${leadName}" /></label>
        <div></div>
        <label class="contract-field"><span>Produto</span><select><option>Selecionar</option></select></label>
        <label class="contract-field"><span>Responsável</span><input placeholder="Responsável" /></label>
        ${statusSelect}
        <label class="contract-field"><span>Data de Fechamento</span><input type="date" /></label>
        <label class="contract-field"><span>Provedor</span><input placeholder="Provedor" /></label>
        <label class="contract-field"><span>Valor Bruto</span><input placeholder="Valor Bruto" /></label>
        <label class="contract-field"><span>Valor de Comissao</span><input placeholder="Valor de Comissao" /></label>
        <label class="contract-field"><span>Valor da Fatura</span><input placeholder="Valor da Fatura" /></label>
        <label class="contract-field"><span>Início do Pagamento</span><input type="date" /></label>
        <label class="contract-field"><span>Pagamento Final</span><input type="date" /></label>
        <label class="contract-field"><span>Número de Parcelas</span><input placeholder="Número de Parcelas" /></label>
        <label class="contract-field contract-field-span-2"><span>Observação</span><textarea placeholder="Observações..."></textarea></label>
      </div>
    `;
  }

  escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  renderCard(lead, etapa) {
    const isSuccess = this.isSuccessEtapa(etapa);
    const encodedLeadId = encodeURIComponent(String(lead.id ?? ''));
    const contractKey = this.buildContractKeyFromLead(lead);
    const contractState = contractKey ? this.contractStateByKey[contractKey] : null;
    const hasContrato = Boolean(contractState && contractState.exists);
    return `
      <button class="kanban-card" data-lead-id="${this.escapeHtml(String(lead.id || ''))}" draggable="true">
        <div class="kanban-card-header">
          <h4 class="kanban-card-name">${lead.name}</h4>
          ${isSuccess ? `
            <span
              class="kanban-card-success-alert ${hasContrato ? 'is-saved' : ''}"
              title="${hasContrato ? 'Contrato salvo - clique para ver/editar' : 'Cadastrar no financeiro'}"
              aria-label="${hasContrato ? 'Contrato salvo - clique para ver/editar' : 'Cadastrar no financeiro'}"
              onclick="window.leadsManager.openSuccessCadastro(event, '${encodedLeadId}')"
            >${hasContrato ? '✓' : '!'}</span>
          ` : ''}
        </div>
        ${lead.company ? `
          <div class="kanban-card-company">
            <i data-lucide="building-2"></i>
            <span>${lead.company}</span>
          </div>
        ` : ''}
        <div class="kanban-card-footer">
          <div class="kanban-card-owner-line">
            <i data-lucide="user"></i>
            <span>${lead.colab_comercial_nome || '-'}</span>
          </div>
          <div class="kanban-card-date">
            <i data-lucide="calendar"></i>
            <span>${this.formatDate(lead.lastAction)}</span>
          </div>
        </div>
        ${lead.tags && lead.tags.length > 0 ? `
          <div class="kanban-card-tags">
            ${lead.tags.map(tag => `<span class="kanban-card-tag">${tag}</span>`).join('')}
          </div>
        ` : ''}
      </button>
    `;
  }

  openSlideOver(leadId) {
    const lead = this.leads.find(l => l.id === leadId);
    if (!lead) return;
    this.slideOver.open(lead, this.leads, this.solucoes);
  }

  closeSlideOver() {
    if (this.slideOver) this.slideOver.close();
  }

  getOrderedEtapas(etapas, includeInactive) {
    const list = Array.isArray(etapas) ? etapas : [];
    const normalized = list.map((etapa, index) => {
      const rawActive = etapa && Object.prototype.hasOwnProperty.call(etapa, 'ativo') ? etapa.ativo : null;
      const isActive = this.parseActiveFlag(rawActive, true);
      const rawOrder = etapa ? (etapa.ordem_id ?? etapa.order ?? etapa.ordem) : null;
      const parsedOrder = parseInt(rawOrder, 10);
      const order = Number.isFinite(parsedOrder) ? parsedOrder : index + 1;
      return { ...etapa, __order: order, __active: isActive };
    });
    const filtered = includeInactive ? normalized : normalized.filter((etapa) => etapa.__active);
    const sorted = filtered.sort((a, b) => a.__order - b.__order);
    return sorted.map(({ __order, __active, ...rest }) => rest);
  }

  parseActiveFlag(value, defaultValue = true) {
    if (value === null || value === undefined) return defaultValue;
    if (typeof value === 'boolean') return value;
    if (typeof value === 'number') return value === 1;
    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase();
      if (['1', 'true', 't', 'sim', 'yes', 'y'].includes(normalized)) return true;
      if (['0', 'false', 'f', 'nao', 'no', 'n'].includes(normalized)) return false;
    }
    return Boolean(value);
  }

  getSolucaoBadgeColor(color) {
    if (color && color.startsWith('#')) {
      return color;
    }
    const colorMap = {
      'analytics': 'hsl(14 100% 82%)',
      'cloud': 'hsl(24 100% 85%)',
      'cyber': 'hsl(357 62% 75%)',
      'consulting': 'hsl(268 7% 44%)',
      'primary': 'hsl(357 62% 75%)',
      'comercial': 'hsl(347 26% 61%)',
      'indicador': 'hsl(142 76% 36%)'
    };
    return colorMap[color] || 'hsl(357 62% 75%)';
  }

  formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(value);
  }

  formatCurrencyFull(value) {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  }

  formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  }

  formatDateFull(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
}

window.leadsManager = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.kanban-container')) {
    window.leadsManager = new LeadsManager();
  }
});

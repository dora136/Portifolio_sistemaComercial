// Soluções (Solutions Catalog) Module - Master-Detail Layout
class SolucoesManager {
  constructor() {
    this.solucoes = [];
    this.filteredSolucoes = [];
    this.selectedSolucao = null;
    this.canManage = window.CAN_MANAGE_SOLUCOES === true;
    this.leadSlideOver = null;
    this.draggingEtapa = null;
    this.init();
  }

  init() {
    if (window.SOLUCOES_DATA) {
      this.solucoes = window.SOLUCOES_DATA;
      this.filteredSolucoes = [...this.solucoes];
      this.render();

      // Select first solution by default
      if (this.solucoes.length> 0) {
        this.selectSolucao(this.solucoes[0].id);
      }
    }

    // Setup search
    const searchInput = document.getElementById('solucaoSearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterSolucoes(e.target.value);
      });
    }

    this.bindCreateHandlers();

    // Inicializa o slide-over de leads independente
    this.leadSlideOver = new LeadSlideOver();
  }

  filterSolucoes(query) {
    query = query.toLowerCase().trim();

    if (!query) {
      this.filteredSolucoes = [...this.solucoes];
    } else {
      this.filteredSolucoes = this.solucoes.filter(solucao => {
        const name = (solucao.name || '').toLowerCase();
        const category = (solucao.category || '').toLowerCase();
        const description = (solucao.description || '').toLowerCase();
        return (
          name.includes(query) ||
          category.includes(query) ||
          description.includes(query)
        );
      });
    }

    this.renderGrid();

    // If selected solution is not in filtered list, clear selection
    if (this.selectedSolucao && !this.filteredSolucoes.find(s => s.id === this.selectedSolucao.id)) {
      this.selectedSolucao = null;
      this.renderDetail();
    }
  }

  render() {
    this.renderGrid();
    this.renderDetail();
  }

  renderGrid() {
    const container = document.querySelector('.solucoes-grid');
    if (!container) return;

    if (this.filteredSolucoes.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 4rem; text-align: center; color: hsl(var(--muted-foreground));">
          <i data-lucide="search" style="width: 48px; height: 48px; margin-bottom: 1rem;"></i>
          <p class="text-sm">Nenhuma solução encontrada</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const html = this.filteredSolucoes.map(solucao => {
      const isSelected = this.selectedSolucao && String(this.selectedSolucao.id) === String(solucao.id);
      const accentVar = solucao.accentVar || 'primary';
      const accentStyle = this.getAccentStyle(accentVar);
      return `
        <button class="solucao-card ${isSelected ? 'selected' : ''}" style="${accentStyle}" onclick="window.solucoesManager.selectSolucao('${solucao.id}')">
          <div class="solucao-card-header">
            <div class="solucao-card-icon">
              <i data-lucide="${solucao.icon}"></i>
            </div>
            <div class="solucao-card-info">
              <h3 class="solucao-card-title">${solucao.name}</h3>
              <span class="solucao-card-category badge">${solucao.category}</span>
            </div>
          </div>
          <div class="solucao-card-footer">
            <span class="solucao-partners-count">
              <i data-lucide="users"></i>
              ${solucao.partnersCount} Parceiros | ${(solucao.leads || []).length} Leads
            </span>
          </div>
        </button>
      `;
    }).join('');

    container.innerHTML = html;
    lucide.createIcons();
  }

  selectSolucao(solucaoId) {
    this.selectedSolucao = this.solucoes.find(s => String(s.id) === String(solucaoId));
    this.renderGrid(); // Re-render to update selected state
    this.renderDetail();
  }

  renderDetail() {
    const container = document.querySelector('.detail-panel');
    if (!container) return;

    if (!this.selectedSolucao) {
      container.classList.remove('solucao-accented');
      container.style.removeProperty('--solucao-accent');
      container.style.removeProperty('--solucao-accent-soft');
      container.style.removeProperty('--solucao-accent-soft-strong');
      container.style.removeProperty('--solucao-accent-border');
      container.innerHTML = `
        <div class="empty-state">
          <i data-lucide="layers"></i>
          <h3>Selecione uma solução</h3>
          <p>Escolha uma solução na lista para ver os detalhes</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const solucao = this.selectedSolucao;
    const registroInfo = Array.isArray(solucao.registroInfo) ? solucao.registroInfo : [];
    const leadsList = Array.isArray(solucao.leads) ? solucao.leads : [];
    const previewEtapas = this.getOrderedEtapas(solucao.kanbanEtapas || [], false);
    const editorEtapas = this.getOrderedEtapas(solucao.kanbanEtapas || [], true);
    const registroInfoLabels = {
      string: 'Texto',
      number: 'Número',
      date: 'Data',
      bool: 'Booleano'
    };

    const accentVar = solucao.accentVar || 'primary';
    const accentStyle = this.getAccentStyle(accentVar);
    this.applyAccentStyle(container, accentVar);
    container.classList.add('solucao-accented');

    container.innerHTML = `
      <div class="fade-in" style="${accentStyle}">
        <!-- Header -->
        <div class="detail-header">
          <div class="detail-title-row">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <div class="solucao-icon-large">
                <i data-lucide="${solucao.icon}"></i>
              </div>
              <div>
                <h1 class="detail-title">${solucao.name}</h1>
                <p class="detail-subtitle">${solucao.category}</p>
              </div>
            </div>
            ${this.canManage ? `
              <button class="solucao-edit-btn" type="button">
                <i data-lucide="pencil"></i>
                Editar
              </button>
            ` : ''}
          </div>
        </div>

        <div class="detail-cards">
          <!-- About Card -->
          <div class="card solucao-detail-card">
            <div class="card-header">
              <i data-lucide="info"></i>
              <h3 class="card-title">Sobre a Solução</h3>
            </div>
            <div class="card-content">
              <p style="color: hsl(var(--foreground)); line-height: 1.6;">
                ${solucao.description}
              </p>
            </div>
          </div>

          <!-- Quick Stats -->
          <div class="card solucao-detail-card">
            <div class="card-header">
              <i data-lucide="bar-chart-3"></i>
              <h3 class="card-title">Estatísticas</h3>
            </div>
            <div class="card-content">
              <div class="solucao-stats-grid">
                <div class="solucao-stats-main">
                  <div class="solucao-stat-card">
                    <i data-lucide="banknote"></i>
                    <div class="stat-value">${this.formatCurrency(solucao.avgTicket)}</div>
                    <div class="stat-label">Ticket Médio</div>
                  </div>
                  <div class="solucao-stat-card">
                    <i data-lucide="timer"></i>
                    <div class="stat-value">${solucao.avgImplementation}</div>
                    <div class="stat-label">Implementação</div>
                  </div>
                </div>
                <div class="solucao-stats-side">
                  <div class="solucao-stat-card solucao-stat-card-action" data-solucao-partners-open style="cursor: pointer;">
                    <i data-lucide="handshake"></i>
                    <div class="stat-value">${solucao.partnersCount}</div>
                    <div class="stat-label">Parceiros</div>
                    <span class="stat-action-link">Ver lista</span>
                  </div>
                  <div class="solucao-stat-card solucao-stat-card-action" data-solucao-leads-open style="cursor: pointer;">
                    <i data-lucide="users"></i>
                    <div class="stat-value">${leadsList.length}</div>
                    <div class="stat-label">Leads</div>
                    <span class="stat-action-link">Ver lista</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Applications Card -->
          <div class="card solucao-detail-card">
            <div class="card-header">
              <i data-lucide="target"></i>
              <h3 class="card-title">Aplicações Básicas</h3>
            </div>
            <div class="card-content">
              <ul class="solucao-applications-list">
                ${solucao.applications.map(app => `
                  <li>
                    <i data-lucide="check-circle"></i>
                    <span>${app}</span>
                  </li>
                `).join('')}
              </ul>
            </div>
          </div>

          <div class="solucao-dual-grid">
            <!-- Registro Info Card -->
            <div class="card solucao-detail-card">
              <div class="card-header">
                <i data-lucide="list-checks"></i>
                <h3 class="card-title">Informações do Registro</h3>
              </div>
              <div class="card-content">
                ${registroInfo.length> 0 ? `
                  <div class="registro-info-list registro-info-vertical">
                    ${registroInfo.map((field) => `
                      <div class="registro-info-item">
                        <div class="registro-info-main">
                          <span class="registro-info-name">${field.name || 'Campo'}</span>
                        </div>
                        <span class="registro-info-type registro-type-${field.type || 'string'}">
                          ${registroInfoLabels[field.type] || 'Texto'}
                        </span>
                      </div>
                    `).join('')}
                  </div>
                ` : `
                  <p class="registro-info-empty">Nenhum campo configurado para esta solução.</p>
                `}
              </div>
            </div>

            <!-- Kanban Preview Card -->
            <div class="card solucao-detail-card">
              <div class="card-header">
                <i data-lucide="columns"></i>
                <h3 class="card-title">Pipeline do Kanban</h3>
              </div>
              <div class="card-content">
                <div class="kanban-preview">
                  <div class="kanban-preview-stages kanban-stages-vertical">
                    ${(previewEtapas || []).map(etapa => `
                      <div class="kanban-preview-stage">
                        <span class="kanban-preview-stage-dot" style="background-color: ${etapa.color_HEX || '#626D84'};"></span>
                        <span class="kanban-preview-stage-name">${etapa.nome_etapa}</span>
                      </div>
                    `).join('')}
                  </div>
                  ${(previewEtapas.length === 0) ? `
                    <p style="color: hsl(var(--muted-foreground)); font-size: 0.875rem;">
                      Nenhuma etapa configurada. Clique em Editar para adicionar etapas.
                    </p>
                  ` : ''}
                </div>
              </div>
            </div>
          </div>
        </div>

        ${this.canManage ? `
          <div class="solucao-edit-modal" data-solucao-edit-modal>
            <div class="solucao-edit-backdrop" data-solucao-edit-close></div>
            <div class="solucao-edit-panel">
              <div class="solucao-edit-header">
                <div>
                  <h3>Editar Solucao</h3>
                  <p>Atualize os dados basicos desta solucao.</p>
                </div>
                <button class="solucao-edit-close" type="button" data-solucao-edit-close>
                  <i data-lucide="x"></i>
                </button>
              </div>
              <form class="solucao-edit-form">
                <div class="solucao-tabs" data-solucao-tabs>
                  <div class="solucao-tabs-header">
                    <button type="button" class="solucao-tab active" data-solucao-tab="caracteristicas">Caracteristicas</button>
                    <button type="button" class="solucao-tab" data-solucao-tab="cadastro">Novo Parceiro</button>
                    <button type="button" class="solucao-tab" data-solucao-tab="campos">Campos</button>
                    <button type="button" class="solucao-tab" data-solucao-tab="kanban">Kanban</button>
                  </div>
                  <div class="solucao-tabs-body">
                    <div class="solucao-tab-panel active" data-solucao-panel="caracteristicas">
                      <label>
                        Tipo da solucao
                        <input type="text" name="tipo_solucao" value="${solucao.category || ""}" />
                      </label>
                      <label>
                        Icone (nome do Icone Lucide)
                        <input type="text" name="icon_id" value="${solucao.icon || "component"}" placeholder="component" />
                        <small style="display: block; margin-top: 0.25rem; color: hsl(var(--muted-foreground));">
                          Busque Icones em: <a href="https://lucide.dev/" target="_blank" rel="noopener" style="color: hsl(var(--primary)); text-decoration: underline;">lucide.dev</a>
                        </small>
                      </label>
                      <label>
                        Cor (hex ou nome da variavel)
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                          <input type="color" name="color_picker" value="${this.resolveColorForPicker(solucao.accentVar)}" style="width: 60px; height: 40px; border-radius: 0.375rem; border: 1px solid hsl(var(--border)); cursor: pointer;" />
                          <input type="text" name="color_id" value="${solucao.accentVar || "#5D8AA8"}" placeholder="#5D8AA8 ou primary" style="flex: 1;" />
                        </div>
                        <small style="display: block; margin-top: 0.25rem; color: hsl(var(--muted-foreground));">
                          Use hex (#5D8AA8) ou nome de variavel (primary, cloud, cyber, etc.)
                        </small>
                      </label>
                    </div>
                    <div class="solucao-tab-panel" data-solucao-panel="cadastro">
                      <label>
                        Descricao
                        <textarea name="descricao" rows="4">${solucao.description || ""}</textarea>
                      </label>
                      <label>
                        Aplicacoes basicas (uma por linha)
                        <textarea name="aplicacoes" rows="6">${(solucao.applications || []).join('\n')}</textarea>
                      </label>
                    </div>
                    <div class="solucao-tab-panel" data-solucao-panel="campos">
                      <div class="registro-editor">
                        <label style="margin-bottom: 0.5rem; display: block;">
                          <strong>Campos do Registro</strong>
                        </label>
                        <p style="color: hsl(var(--muted-foreground)); font-size: 0.875rem; margin: 0 0 0.75rem;">
                          Defina os campos do registro (nome e tipo) que serao usados no preenchimento do lead.
                        </p>
                        <div class="registro-fields" data-registro-fields>
                          ${registroInfo.map((field, index) => `
                            <div class="registro-field-row" data-registro-index="${index}" data-registro-value="${field.value ?? ""}">
                              <input type="text" name="registro_nome_${index}" value="${field.name || ""}" placeholder="Nome do campo" />
                              <select name="registro_tipo_${index}">
                                <option value="string" ${field.type === "string" ? "selected" : ""}>String</option>
                                <option value="number" ${field.type === "number" ? "selected" : ""}>Numero</option>
                                <option value="date" ${field.type === "date" ? "selected" : ""}>Data</option>
                                <option value="bool" ${field.type === "bool" ? "selected" : ""}>Booleano</option>
                              </select>
                              <button type="button" class="registro-field-remove" onclick="window.solucoesManager.removeRegistroField(this)">x</button>
                            </div>
                          `).join('')}
                        </div>
                        <button type="button" class="registro-add-field" onclick="window.solucoesManager.addRegistroField()">
                          <i data-lucide="plus" style="width: 14px; height: 14px;"></i>
                          Adicionar Campo
                        </button>
                      </div>
                    </div>
                    <div class="solucao-tab-panel" data-solucao-panel="kanban">
                      <!-- Kanban Editor -->
                      ${String(solucao.id) === "1" ? `
                        <div class="kanban-editor">
                          <label style="margin-bottom: 0.5rem; display: block;">
                            <strong>Etapas do Kanban</strong>
                          </label>
                          <p style="color: hsl(var(--muted-foreground)); font-size: 0.875rem; margin: 0;">
                            A etapa do Kanban desta solucao e gerenciada via API.
                          </p>
                        </div>
                      ` : `
                        <div class="kanban-editor">
                          <label style="margin-bottom: 0.5rem; display: block;">
                            <strong>Etapas do Kanban</strong>
                          </label>
                          <div class="kanban-etapas-list" data-kanban-etapas>
                            ${(editorEtapas || []).map((etapa, index) => {
                              const etapaId = etapa.id ?? index + 1;
                              const isActive = this.parseActiveFlag(etapa.ativo, true);
                              const isSuccess = Boolean(etapa.sucesso);
                              const isLost = Boolean(etapa.perdido);
                              const rowClass = isActive ? '' : ' is-inactive';
                              const toggleLabel = isActive ? 'Desativar' : 'Ativar';
                              const disabledAttr = isActive ? '' : 'disabled';
                              return `
                              <div class="kanban-etapa-item${rowClass}" data-etapa-index="${index}" data-etapa-id="${etapaId}" data-etapa-ativo="${isActive ? 1 : 0}">
                                <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
                                <input type="color" class="kanban-etapa-color" name="etapa_color_${index}" value="${etapa.color_HEX || "#626D84"}" ${disabledAttr} />
                                <input type="text" name="etapa_nome_${index}" value="${etapa.nome_etapa || ""}" placeholder="Nome da etapa" style="flex: 1;" ${disabledAttr} />
                                <label class="kanban-etapa-flag">
                                  <input type="checkbox" class="kanban-etapa-success" ${isSuccess ? 'checked' : ''} ${disabledAttr} />
                                  <span>Sucesso</span>
                                </label>
                                <label class="kanban-etapa-flag">
                                  <input type="checkbox" class="kanban-etapa-lost" ${isLost ? 'checked' : ''} ${disabledAttr} />
                                  <span>Perdido</span>
                                </label>
                                <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">${toggleLabel}</button>
                              </div>
                              `;
                            }).join('')}
                          </div>
                          <button type="button" class="kanban-add-etapa" onclick="window.solucoesManager.addEtapa()" style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: hsl(var(--primary)); color: white; border: none; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                            <i data-lucide="plus" style="width: 14px; height: 14px;"></i>
                            Adicionar Etapa
                          </button>
                        </div>
                      `}
                    </div>
                  </div>
                </div>

                <div class="solucao-edit-error" role="alert"></div>
                <div class="solucao-edit-actions">
                  <button type="button" class="solucao-edit-delete">Apagar</button>
                  <button type="button" class="solucao-edit-cancel" data-solucao-edit-close>Cancelar</button>
                  <button type="submit" class="solucao-edit-save">Salvar</button>
                </div>
              </form>
            </div>
          </div>

          <div class="solucao-confirm-modal" data-solucao-confirm-modal>
            <div class="solucao-confirm-backdrop" data-solucao-confirm-close></div>
            <div class="solucao-confirm-panel">
              <div class="solucao-confirm-header">
                <div class="solucao-confirm-icon">
                  <i data-lucide="alert-triangle"></i>
                </div>
                <div>
                  <h3>Confirmar exclusao</h3>
                  <p>Esta acao remove a solucao e nao pode ser desfeita.</p>
                </div>
              </div>
              <div class="solucao-confirm-actions">
                <button type="button" class="solucao-confirm-cancel" data-solucao-confirm-close>Cancelar</button>
                <button type="button" class="solucao-confirm-delete">Apagar</button>
              </div>
            </div>
          </div>
        ` : ''}

        <div class="solucao-edit-modal" data-solucao-partners-modal>
          <div class="solucao-edit-backdrop" data-solucao-partners-close></div>
          <div class="solucao-edit-panel">
            <div class="solucao-edit-header">
              <div>
                <h3>Parceiros da Solução</h3>
                <p>Lista completa de quem oferece esta solução.</p>
              </div>
              <button class="solucao-edit-close" type="button" data-solucao-partners-close>
                <i data-lucide="x"></i>
              </button>
            </div>
            <div class="solucao-list-modal-body">
              ${solucao.partners.length> 0 ? `
                <div class="solucao-partners-list">
                  ${solucao.partners.map((partner, index) => `
                    <div class="solucao-partner-item">
                      <span class="partner-number">${index + 1}</span>
                      <span class="partner-name">${partner}</span>
                    </div>
                  `).join('')}
                </div>
              ` : `
                <div class="solucao-list-empty">Nenhum parceiro cadastrado.</div>
              `}
            </div>
          </div>
        </div>

        <div class="solucao-edit-modal" data-solucao-leads-modal>
          <div class="solucao-edit-backdrop" data-solucao-leads-close></div>
          <div class="solucao-edit-panel">
            <div class="solucao-edit-header">
              <div>
                <h3>Leads da Solução</h3>
                <p>Lista de leads vinculados a esta solução.</p>
              </div>
              <button class="solucao-edit-close" type="button" data-solucao-leads-close>
                <i data-lucide="x"></i>
              </button>
            </div>
            <div class="solucao-list-modal-body">
              ${leadsList.length> 0 ? `
                <div class="solucao-partners-list">
                  ${leadsList.map((lead) => `
                    <div class="solucao-partner-item" style="cursor: pointer;" onclick="window.solucoesManager.openLeadSlideOver(${lead.id_comercial})">
                      <span class="partner-number">${lead.id_comercial}</span>
                      <span class="partner-name">${lead.name}</span>
                    </div>
                  `).join('')}
                </div>
              ` : `
                <div class="solucao-list-empty">Nenhum lead cadastrado.</div>
              `}
            </div>
          </div>
        </div>
      </div>
    `;

    lucide.createIcons();
    this.bindEditHandlers(container, solucao);
    this.bindInfoModals(container);
  }

  bindCreateHandlers() {
    if (!this.canManage) {
      return;
    }
    const addButton = document.querySelector('.btn-add-new');
    if (!addButton) return;

    addButton.addEventListener('click', () => {
      const modal = this.ensureCreateModal();
      modal.classList.add('open');
      const errorBox = modal.querySelector('.solucao-edit-error');
      if (errorBox) {
        errorBox.textContent = '';
      }
    });
  }

  ensureCreateModal() {
    let modal = document.querySelector('[data-solucao-create-modal]');
    if (modal) return modal;

    const wrapper = document.createElement('div');
    wrapper.className = 'solucao-edit-modal';
    wrapper.setAttribute('data-solucao-create-modal', '');
    wrapper.innerHTML = `
      <div class="solucao-edit-backdrop" data-solucao-create-close></div>
      <div class="solucao-edit-panel">
        <div class="solucao-edit-header">
          <div>
            <h3>Nova Solução</h3>
            <p>Preencha os dados básicos para cadastrar.</p>
          </div>
          <button class="solucao-edit-close" type="button" data-solucao-create-close>
            <i data-lucide="x"></i>
          </button>
        </div>
                <form class="solucao-edit-form">
          <div class="solucao-tabs" data-solucao-tabs>
            <div class="solucao-tabs-header">
              <button type="button" class="solucao-tab active" data-solucao-tab="caracteristicas">Caracteristicas</button>
              <button type="button" class="solucao-tab" data-solucao-tab="cadastro">Novo Parceiro</button>
              <button type="button" class="solucao-tab" data-solucao-tab="campos">Campos</button>
              <button type="button" class="solucao-tab" data-solucao-tab="kanban">Kanban</button>
            </div>
            <div class="solucao-tabs-body">
              <div class="solucao-tab-panel active" data-solucao-panel="caracteristicas">
                <label>
                  Nome da solucao
                  <input type="text" name="nome_solucao" required />
                </label>
                <label>
                  Tipo da solucao
                  <input type="text" name="tipo_solucao" />
                </label>
                <label>
                  Icone (nome do Icone Lucide)
                  <input type="text" name="icon_id" value="component" placeholder="component" />
                  <small style="display: block; margin-top: 0.25rem; color: hsl(var(--muted-foreground));">
                    Busque Icones em: <a href="https://lucide.dev/" target="_blank" rel="noopener" style="color: hsl(var(--primary)); text-decoration: underline;">lucide.dev</a>
                  </small>
                </label>
                <label>
                  Cor (hex ou nome da variavel)
                  <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <input type="color" name="color_picker" value="#5D8AA8" style="width: 60px; height: 40px; border-radius: 0.375rem; border: 1px solid hsl(var(--border)); cursor: pointer;" />
                    <input type="text" name="color_id" value="#5D8AA8" placeholder="#5D8AA8 ou primary" style="flex: 1;" />
                  </div>
                  <small style="display: block; margin-top: 0.25rem; color: hsl(var(--muted-foreground));">
                    Use hex (#5D8AA8) ou nome de variavel (primary, cloud, cyber, etc.)
                  </small>
                </label>
              </div>
              <div class="solucao-tab-panel" data-solucao-panel="cadastro">
                <label>
                  Descricao
                  <textarea name="descricao" rows="4"></textarea>
                </label>
                <label>
                  Aplicacoes basicas (uma por linha)
                  <textarea name="aplicacoes" rows="6"></textarea>
                </label>
              </div>
              <div class="solucao-tab-panel" data-solucao-panel="campos">
                <div class="registro-editor">
                  <label style="margin-bottom: 0.5rem; display: block;">
                    <strong>Campos do Registro</strong>
                  </label>
                  <p style="color: hsl(var(--muted-foreground)); font-size: 0.875rem; margin: 0 0 0.75rem;">
                    Defina os campos do registro (nome e tipo) que serao usados no preenchimento do lead.
                  </p>
                  <div class="registro-fields" data-registro-fields></div>
                  <button type="button" class="registro-add-field" onclick="window.solucoesManager.addRegistroField()">
                    <i data-lucide="plus" style="width: 14px; height: 14px;"></i>
                    Adicionar Campo
                  </button>
                </div>
              </div>
              <div class="solucao-tab-panel" data-solucao-panel="kanban">
                <!-- Kanban Editor para criacao -->
                <div class="kanban-editor">
                  <label style="margin-bottom: 0.5rem; display: block;">
                    <strong>Etapas do Kanban</strong>
                  </label>
                  <div class="kanban-etapas-list" data-kanban-etapas>
                    <div class="kanban-etapa-item" data-etapa-index="0" data-etapa-id="1" data-etapa-ativo="1">
                      <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
                      <input type="color" class="kanban-etapa-color" name="etapa_color_0" value="#626D84" />
                      <input type="text" name="etapa_nome_0" value="Triagem" placeholder="Nome da etapa" style="flex: 1;" />
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-success" />
                        <span>Sucesso</span>
                      </label>
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-lost" />
                        <span>Perdido</span>
                      </label>
                      <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">Desativar</button>
                    </div>
                    <div class="kanban-etapa-item" data-etapa-index="1" data-etapa-id="2" data-etapa-ativo="1">
                      <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
                      <input type="color" class="kanban-etapa-color" name="etapa_color_1" value="#2964D9" />
                      <input type="text" name="etapa_nome_1" value="Reuniao" placeholder="Nome da etapa" style="flex: 1;" />
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-success" />
                        <span>Sucesso</span>
                      </label>
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-lost" />
                        <span>Perdido</span>
                      </label>
                      <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">Desativar</button>
                    </div>
                    <div class="kanban-etapa-item" data-etapa-index="2" data-etapa-id="3" data-etapa-ativo="1">
                      <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
                      <input type="color" class="kanban-etapa-color" name="etapa_color_2" value="#F59F0A" />
                      <input type="text" name="etapa_nome_2" value="Proposta" placeholder="Nome da etapa" style="flex: 1;" />
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-success" />
                        <span>Sucesso</span>
                      </label>
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-lost" />
                        <span>Perdido</span>
                      </label>
                      <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">Desativar</button>
                    </div>
                    <div class="kanban-etapa-item" data-etapa-index="3" data-etapa-id="4" data-etapa-ativo="1">
                      <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
                      <input type="color" class="kanban-etapa-color" name="etapa_color_3" value="#16A249" />
                      <input type="text" name="etapa_nome_3" value="Fechamento" placeholder="Nome da etapa" style="flex: 1;" />
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-success" />
                        <span>Sucesso</span>
                      </label>
                      <label class="kanban-etapa-flag">
                        <input type="checkbox" class="kanban-etapa-lost" />
                        <span>Perdido</span>
                      </label>
                      <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">Desativar</button>
                    </div>
                  </div>
                  <button type="button" class="kanban-add-etapa" onclick="window.solucoesManager.addEtapa()" style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: hsl(var(--primary)); color: white; border: none; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                    <i data-lucide="plus" style="width: 14px; height: 14px;"></i>
                    Adicionar Etapa
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="solucao-edit-error" role="alert"></div>
          <div class="solucao-edit-actions">
            <button type="button" class="solucao-edit-cancel" data-solucao-create-close>Cancelar</button>
            <button type="submit" class="solucao-edit-save">Salvar</button>
          </div>
        </form>
      </div>
    `;

    document.body.appendChild(wrapper);
    lucide.createIcons();
    this.setupSolucaoTabs(wrapper);
    this.setupKanbanSorting(wrapper);

    const closeButtons = wrapper.querySelectorAll('[data-solucao-create-close]');
    closeButtons.forEach((button) => {
      button.addEventListener('click', () => {
        wrapper.classList.remove('open');
      });
    });

    const form = wrapper.querySelector('.solucao-edit-form');
    const errorBox = wrapper.querySelector('.solucao-edit-error');

    // Sincroniza color picker com campo de texto
    const colorPicker = form.querySelector('input[name="color_picker"]');
    const colorText = form.querySelector('input[name="color_id"]');

    if (colorPicker && colorText) {
      colorPicker.addEventListener('input', (e) => {
        colorText.value = e.target.value;
      });

      colorText.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        // Se for um hex válido, atualiza o color picker
        if (value.match(/^#[0-9A-Fa-f]{6}$/)) {
          colorPicker.value = value;
        }
      });
    }

    if (form) {
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const nomeSolucao = form.elements.nome_solucao.value.trim();
        const tipoSolucao = form.elements.tipo_solucao.value.trim();
        const descricao = form.elements.descricao.value.trim();
        const iconId = form.elements.icon_id.value.trim() || 'component';
        const colorId = form.elements.color_id.value.trim() || '#5D8AA8';
        const aplicacoesRaw = form.elements.aplicacoes.value
          .split('\n')
          .map(line => line.trim())
          .filter(Boolean);

        // Coleta as etapas do kanban
        const kanbanEtapas = this.collectKanbanEtapas(form);
        const registroInfo = this.collectRegistroInfo(form);

        try {
          const response = await fetch('/portfolio/solucoes', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              nome_solucao: nomeSolucao,
              tipo_solucao: tipoSolucao || null,
              descricao: descricao || null,
              icon_id: iconId,
              color_id: colorId,
              aplicacoes_basicas: aplicacoesRaw,
              registro_info: registroInfo,
              kanban_etapas: kanbanEtapas.length> 0 ? kanbanEtapas : null
            })
          });

          if (!response.ok) {
            throw new Error('Erro ao salvar');
          }

          window.location.reload();
        } catch (error) {
          if (errorBox) {
            errorBox.textContent = 'Nao foi possivel salvar. Tente novamente.';
          }
        }
      });
    }

    return wrapper;
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

  getAccentStyle(accentVar) {
    if (!accentVar) {
      accentVar = 'primary';
    }

    if (accentVar.startsWith('#')) {
      const soft = this.hexToRgba(accentVar, 0.12);
      const softStrong = this.hexToRgba(accentVar, 0.06);
      const border = this.hexToRgba(accentVar, 0.3);
      return `--solucao-accent: ${accentVar}; --solucao-accent-soft: ${soft}; --solucao-accent-soft-strong: ${softStrong}; --solucao-accent-border: ${border};`;
    }

    return `--solucao-accent: hsl(var(--${accentVar})); --solucao-accent-soft: hsl(var(--${accentVar}) / 0.12); --solucao-accent-soft-strong: hsl(var(--${accentVar}) / 0.06); --solucao-accent-border: hsl(var(--${accentVar}) / 0.3);`;
  }

  applyAccentStyle(element, accentVar) {
    if (!element) return;
    if (!accentVar) {
      accentVar = 'primary';
    }

    if (accentVar.startsWith('#')) {
      element.style.setProperty('--solucao-accent', accentVar);
      element.style.setProperty('--solucao-accent-soft', this.hexToRgba(accentVar, 0.12));
      element.style.setProperty('--solucao-accent-soft-strong', this.hexToRgba(accentVar, 0.06));
      element.style.setProperty('--solucao-accent-border', this.hexToRgba(accentVar, 0.3));
      return;
    }

    element.style.setProperty('--solucao-accent', `hsl(var(--${accentVar}))`);
    element.style.setProperty('--solucao-accent-soft', `hsl(var(--${accentVar}) / 0.12)`);
    element.style.setProperty('--solucao-accent-soft-strong', `hsl(var(--${accentVar}) / 0.06)`);
    element.style.setProperty('--solucao-accent-border', `hsl(var(--${accentVar}) / 0.3)`);
  }

  resolveColorForPicker(accentVar) {
    if (!accentVar) return '#5D8AA8';
    if (accentVar.startsWith('#')) return accentVar;
    return '#5D8AA8';
  }

  setupSolucaoTabs(modal) {
    if (!modal) return;
    const tabButtons = modal.querySelectorAll('[data-solucao-tab]');
    const panels = modal.querySelectorAll('[data-solucao-panel]');
    if (!tabButtons.length || !panels.length) return;

    const activateTab = (tabId) => {
      tabButtons.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.solucaoTab === tabId);
      });
      panels.forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.solucaoPanel === tabId);
      });
    };

    tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => activateTab(btn.dataset.solucaoTab));
    });

    const initial = tabButtons[0]?.dataset.solucaoTab;
    if (initial) activateTab(initial);
  }

  setupKanbanColorSwatches(modal) {
    if (!modal) return;
    const inputs = modal.querySelectorAll('.kanban-etapa-color');
    inputs.forEach((input) => {
      if (input.dataset.colorReady === '1') return;
      input.dataset.colorReady = '1';
      const applyColor = () => {
        input.style.backgroundColor = input.value;
      };
      input.addEventListener('input', applyColor);
      input.addEventListener('change', applyColor);
      applyColor();
    });
  }

  setupKanbanSorting(modal) {
    if (!modal) return;
    const lists = modal.querySelectorAll('[data-kanban-etapas]');
    lists.forEach((list) => {
      if (list.dataset.sortingReady === '1') return;
      list.dataset.sortingReady = '1';

      list.addEventListener('dragstart', (event) => {
        const handle = event.target.closest('.kanban-etapa-handle');
        if (!handle) return;
        const item = handle.closest('.kanban-etapa-item');
        if (!item) return;
        this.draggingEtapa = item;
        item.classList.add('dragging');
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = 'move';
          event.dataTransfer.setData('text/plain', '');
          try {
            event.dataTransfer.setDragImage(item, 16, 16);
          } catch (err) {
            // ignore if unsupported
          }
        }
      });

      list.addEventListener('dragend', () => {
        if (this.draggingEtapa) {
          this.draggingEtapa.classList.remove('dragging');
        }
        this.draggingEtapa = null;
        this.renumberEtapas(list);
      });

      list.addEventListener('dragover', (event) => {
        if (!this.draggingEtapa) return;
        event.preventDefault();
        const afterElement = this.getDragAfterElement(list, event.clientY);
        if (afterElement == null) {
          list.appendChild(this.draggingEtapa);
        } else {
          list.insertBefore(this.draggingEtapa, afterElement);
        }
      });

      list.addEventListener('drop', (event) => {
        event.preventDefault();
        if (this.draggingEtapa) {
          this.draggingEtapa.classList.remove('dragging');
        }
        this.draggingEtapa = null;
        this.renumberEtapas(list);
      });
    });

    this.setupKanbanColorSwatches(modal);
    this.setupKanbanFlags(modal);
  }

  getDragAfterElement(container, y) {
    const items = [...container.querySelectorAll('.kanban-etapa-item:not(.dragging)')];
    let closest = { offset: Number.NEGATIVE_INFINITY, element: null };
    items.forEach((item) => {
      const box = item.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset> closest.offset) {
        closest = { offset, element: item };
      }
    });
    return closest.element;
  }

  setupKanbanFlags(modal) {
    if (!modal) return;
    const lists = modal.querySelectorAll('[data-kanban-etapas]');
    lists.forEach((list) => {
      if (list.dataset.flagsReady === '1') return;
      list.dataset.flagsReady = '1';
      list.addEventListener('change', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLInputElement)) return;
        if (target.classList.contains('kanban-etapa-success')) {
          if (target.checked) {
            const lost = target.closest('.kanban-etapa-item')?.querySelector('.kanban-etapa-lost');
            if (lost) lost.checked = false;
          }
        }
        if (target.classList.contains('kanban-etapa-lost')) {
          if (target.checked) {
            const success = target.closest('.kanban-etapa-item')?.querySelector('.kanban-etapa-success');
            if (success) success.checked = false;
          }
        }
      });
    });
  }

  hexToRgba(hex, alpha) {
    let value = hex.replace('#', '').trim();
    if (value.length === 3) {
      value = value.split('').map((ch) => ch + ch).join('');
    }
    const intValue = parseInt(value, 16);
    const r = (intValue>> 16) & 255;
    const g = (intValue>> 8) & 255;
    const b = intValue & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  bindEditHandlers(container, solucao) {
    const openButton = container.querySelector('.solucao-edit-btn');
    const modal = container.querySelector('[data-solucao-edit-modal]');
    if (!openButton || !modal) return;

    const closeButtons = modal.querySelectorAll('[data-solucao-edit-close]');
    const form = modal.querySelector('.solucao-edit-form');
    const errorBox = modal.querySelector('.solucao-edit-error');

    const openModal = () => {
      modal.classList.add('open');
    };

    const closeModal = () => {
      modal.classList.remove('open');
      if (errorBox) {
        errorBox.textContent = '';
      }
    };

    openButton.addEventListener('click', openModal);
    closeButtons.forEach((button) => {
      button.addEventListener('click', closeModal);
    });

    if (!form) return;
    this.setupSolucaoTabs(modal);
    this.setupKanbanSorting(modal);

    // Sincroniza color picker com campo de texto no modal de edição
    const colorPicker = form.querySelector('input[name="color_picker"]');
    const colorText = form.querySelector('input[name="color_id"]');
    if (colorPicker && colorText) {
      colorPicker.addEventListener('input', (e) => {
        colorText.value = e.target.value;
      });
      colorText.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (value.match(/^#[0-9A-Fa-f]{6}$/)) {
          colorPicker.value = value;
        }
      });
    }

    const deleteButton = modal.querySelector('.solucao-edit-delete');
    const confirmModal = container.querySelector('[data-solucao-confirm-modal]');
    if (deleteButton && confirmModal) {
      const confirmDelete = confirmModal.querySelector('.solucao-confirm-delete');
      const confirmCloseButtons = confirmModal.querySelectorAll('[data-solucao-confirm-close]');

      const openConfirm = () => {
        confirmModal.classList.add('open');
      };

      const closeConfirm = () => {
        confirmModal.classList.remove('open');
      };

      deleteButton.addEventListener('click', openConfirm);
      confirmCloseButtons.forEach((button) => {
        button.addEventListener('click', closeConfirm);
      });

      if (confirmDelete) {
        confirmDelete.addEventListener('click', async () => {
          try {
            const response = await fetch(`/portfolio/solucoes/${solucao.id}`, {
              method: 'DELETE'
            });

            if (response.status === 409) {
              throw new Error('Vinculos ativos');
            }

            if (!response.ok) {
              throw new Error('Erro ao apagar');
            }

            window.location.reload();
          } catch (error) {
            closeConfirm();
            if (errorBox) {
              errorBox.textContent = error.message === 'Vinculos ativos'
                ? 'Nao foi possivel apagar: existem parceiros ativos vinculados.'
                : 'Nao foi possivel apagar. Tente novamente.';
            }
          }
        });
      }
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const tipoSolucao = form.elements.tipo_solucao.value.trim();
      const iconId = form.elements.icon_id.value.trim() || 'component';
      const colorId = form.elements.color_id.value.trim() || '#5D8AA8';
      const descricao = form.elements.descricao.value.trim();
      const aplicacoesRaw = form.elements.aplicacoes.value
        .split('\n')
        .map(line => line.trim())
        .filter(Boolean);

      // Coleta as etapas do kanban
      const isCrmKanban = String(solucao.id) === '1';
      const kanbanEtapas = isCrmKanban
        ? null
        : this.collectKanbanEtapas(form);
      const registroInfo = this.collectRegistroInfo(form);

      try {
        const payload = {
          tipo_solucao: tipoSolucao || null,
          descricao: descricao || null,
          icon_id: iconId,
          color_id: colorId,
          aplicacoes_basicas: aplicacoesRaw,
          registro_info: registroInfo
        };
        if (!isCrmKanban) {
          payload.kanban_etapas = kanbanEtapas;
        }

        const response = await fetch(`/portfolio/solucoes/${solucao.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error('Erro ao salvar');
        }

        solucao.category = tipoSolucao || solucao.category;
        solucao.description = descricao;
        solucao.icon = iconId;
        solucao.accentVar = colorId;
        solucao.applications = aplicacoesRaw;
        solucao.registroInfo = registroInfo;
        if (!isCrmKanban) {
          solucao.kanbanEtapas = kanbanEtapas;
        }
        this.renderGrid();
        this.renderDetail();
        closeModal();
      } catch (error) {
        if (errorBox) {
          errorBox.textContent = 'Nao foi possivel salvar. Tente novamente.';
        }
      }
    });
  }

  collectKanbanEtapas(form) {
    const etapasContainer = form.querySelector('[data-kanban-etapas]');
    if (!etapasContainer) return [];

    const etapaItems = etapasContainer.querySelectorAll('.kanban-etapa-item');
    const etapas = [];

    etapaItems.forEach((item, index) => {
      const colorInput = item.querySelector('input[type="color"]');
      const nomeInput = item.querySelector('input[type="text"]');
      const successInput = item.querySelector('.kanban-etapa-success');
      const lostInput = item.querySelector('.kanban-etapa-lost');
      const nome = nomeInput ? nomeInput.value.trim() : '';
      if (!nome) return;
      const etapaId = parseInt(item.dataset.etapaId, 10);
      const id = Number.isFinite(etapaId) ? etapaId : index + 1;
      const ativo = item.dataset.etapaAtivo === '0' ? 0 : 1;
      const ordem_id = index + 1;
      etapas.push({
        id,
        nome_etapa: nome,
        color_HEX: colorInput ? colorInput.value : '#626D84',
        ativo,
        ordem_id,
        sucesso: successInput && successInput.checked ? 1 : 0,
        perdido: lostInput && lostInput.checked ? 1 : 0
      });
    });

    return etapas;
  }

  bindInfoModals(container) {
    const partnersOpen = container.querySelector('[data-solucao-partners-open]');
    const partnersModal = container.querySelector('[data-solucao-partners-modal]');
    const leadsOpen = container.querySelector('[data-solucao-leads-open]');
    const leadsModal = container.querySelector('[data-solucao-leads-modal]');

    if (partnersOpen && partnersModal) {
      const closeButtons = partnersModal.querySelectorAll('[data-solucao-partners-close]');
      partnersOpen.addEventListener('click', () => partnersModal.classList.add('open'));
      closeButtons.forEach((btn) => {
        btn.addEventListener('click', () => partnersModal.classList.remove('open'));
      });
    }

    if (leadsOpen && leadsModal) {
      const closeButtons = leadsModal.querySelectorAll('[data-solucao-leads-close]');
      leadsOpen.addEventListener('click', () => leadsModal.classList.add('open'));
      closeButtons.forEach((btn) => {
        btn.addEventListener('click', () => leadsModal.classList.remove('open'));
      });
    }
  }

  collectRegistroInfo(form) {
    const container = form.querySelector('[data-registro-fields]');
    if (!container) return [];

    const rows = container.querySelectorAll('.registro-field-row');
    const allowedTypes = new Set(['string', 'number', 'date', 'bool']);
    const fields = [];

    rows.forEach((row) => {
      const nameInput = row.querySelector('input[type="text"]');
      const typeSelect = row.querySelector('select');
      const name = nameInput ? nameInput.value.trim() : '';
      if (!name) return;
      const rawType = typeSelect ? typeSelect.value : 'string';
      const type = allowedTypes.has(rawType) ? rawType : 'string';
      const value = row.dataset.registroValue ? row.dataset.registroValue : null;
      fields.push({ name, type, value });
    });

    return fields;
  }

  addEtapa() {
    const modal = document.querySelector('[data-solucao-edit-modal].open') || document.querySelector('[data-solucao-create-modal].open');
    if (!modal) return;

    const etapasContainer = modal.querySelector('[data-kanban-etapas]');
    if (!etapasContainer) return;

    const existingItems = etapasContainer.querySelectorAll('.kanban-etapa-item');
    const newIndex = existingItems.length;
    const existingIds = Array.from(existingItems)
      .map((item) => parseInt(item.dataset.etapaId, 10))
      .filter((value) => Number.isFinite(value));
    const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : newIndex + 1;

    const newItem = document.createElement('div');
    newItem.className = 'kanban-etapa-item';
    newItem.setAttribute('data-etapa-index', newIndex);
    newItem.setAttribute('data-etapa-id', newId);
    newItem.setAttribute('data-etapa-ativo', '1');
    newItem.innerHTML = `
      <span class="kanban-etapa-handle" draggable="true" title="Arrastar"><i data-lucide="grip-vertical"></i></span>
      <input type="color" class="kanban-etapa-color" name="etapa_color_${newIndex}" value="#626D84" />
      <input type="text" name="etapa_nome_${newIndex}" value="" placeholder="Nome da etapa" style="flex: 1;" />
      <label class="kanban-etapa-flag">
        <input type="checkbox" class="kanban-etapa-success" />
        <span>Sucesso</span>
      </label>
      <label class="kanban-etapa-flag">
        <input type="checkbox" class="kanban-etapa-lost" />
        <span>Perdido</span>
      </label>
      <button type="button" class="kanban-etapa-toggle" onclick="window.solucoesManager.toggleEtapa(this)">Desativar</button>
    `;

    etapasContainer.appendChild(newItem);
    lucide.createIcons();
    this.renumberEtapas(etapasContainer);
    this.setupKanbanColorSwatches(modal);
    this.setupKanbanFlags(modal);
  }

  addRegistroField() {
    const modal = document.querySelector('[data-solucao-edit-modal].open') || document.querySelector('[data-solucao-create-modal].open');
    if (!modal) return;

    const container = modal.querySelector('[data-registro-fields]');
    if (!container) return;

    const newIndex = container.querySelectorAll('.registro-field-row').length;
    const row = document.createElement('div');
    row.className = 'registro-field-row';
    row.setAttribute('data-registro-index', newIndex);
    row.dataset.registroValue = '';
    row.innerHTML = `
      <input type="text" name="registro_nome_${newIndex}" value="" placeholder="Nome do campo" />
      <select name="registro_tipo_${newIndex}">
        <option value="string">String</option>
        <option value="number">Numero</option>
        <option value="date">Data</option>
        <option value="bool">Booleano</option>
      </select>
      <button type="button" class="registro-field-remove" onclick="window.solucoesManager.removeRegistroField(this)">x</button>
    `;
    container.appendChild(row);
  }

  toggleEtapa(button) {
    const item = button.closest('.kanban-etapa-item');
    if (!item) return;
    const isInactive = item.classList.contains('is-inactive');
    const nextActive = isInactive;
    item.classList.toggle('is-inactive', !nextActive);
    item.dataset.etapaAtivo = nextActive ? '1' : '0';

    const inputs = item.querySelectorAll('input[type="text"], input[type="color"], input[type="checkbox"]');
    inputs.forEach((input) => {
      input.disabled = !nextActive;
    });

    button.textContent = nextActive ? 'Desativar' : 'Ativar';
    this.setupKanbanColorSwatches(item);
  }

  removeEtapa(button) {
    this.toggleEtapa(button);
  }

  renumberEtapas(container) {
    if (!container) return;
    const items = container.querySelectorAll('.kanban-etapa-item');
    items.forEach((item, index) => {
      item.dataset.etapaIndex = index;
      item.dataset.etapaOrdem = index + 1;
      const colorInput = item.querySelector('input[type="color"]');
      const nameInput = item.querySelector('input[type="text"]');
      if (colorInput) colorInput.name = `etapa_color_${index}`;
      if (nameInput) nameInput.name = `etapa_nome_${index}`;
    });
  }

  removeRegistroField(button) {
    const item = button.closest('.registro-field-row');
    if (item) {
      item.remove();
    }
  }

  formatCurrency(value) {
    if (value === null || value === undefined) {
      return '-';
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed === '' || trimmed === '-') {
        return '-';
      }
      const parsed = Number(trimmed);
      if (!Number.isFinite(parsed)) {
        return '-';
      }
      value = parsed;
    }
    if (!Number.isFinite(value)) {
      return '-';
    }

    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      notation: 'compact',
      maximumFractionDigits: 0
    }).format(value);
  }

  async openLeadSlideOver(idComercial) {
    try {
      const response = await fetch(`/portfolio/api/leads/comercial/${idComercial}`);
      if (!response.ok) throw new Error('Erro ao buscar lead');
      const data = await response.json();
      const leads = data.leads || [];
      const solucoes = data.solucoes || [];

      if (leads.length === 0) return;

      this.leadSlideOver.open(leads[0], leads, solucoes);
    } catch (error) {
      console.error('Erro ao abrir lead:', error);
    }
  }
}

window.solucoesManager = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.solucoes-layout')) {
    window.solucoesManager = new SolucoesManager();
  }
});

/**
 * LeadSlideOver - Reusable slide-over component for viewing/editing lead details.
 *
 * Used by: leads.js, partners.js, solucoes.js, partner-acompanhamento.js
 *
 * Usage:
 *   const slideOver = new LeadSlideOver({ onSave, onDelete, canDelete });
 *   slideOver.open(lead, leads, solucoes);
 */
class LeadSlideOver {
  constructor(options = {}) {
    this.options = options;
    this.lead = null;
    this.leads = [];
    this.solucoes = [];
    this.selectedEtapaId = null;
    this.comerciais = null;
    this.el = null;
    this._buildDOM();
  }

  /* ------------------------------------------------------------------ */
  /*  DOM creation                                                       */
  /* ------------------------------------------------------------------ */

  _buildDOM() {
    this.el = document.createElement('div');
    this.el.className = 'slide-over';
    this.el.innerHTML = `
      <div class="slide-over-backdrop" data-lead-slideover-close></div>
      <div class="slide-over-panel">
        <div class="slide-over-header">
          <div class="slide-over-title">
            <h2 data-lead-name></h2>
            <p data-lead-subtitle></p>
          </div>
          <button class="slide-over-close" data-lead-slideover-close>
            <i data-lucide="x"></i>
          </button>
        </div>
        <div class="slide-over-content" data-lead-content></div>
        <div class="slide-over-footer" data-lead-footer></div>
      </div>
    `;
    document.body.appendChild(this.el);

    // Close on backdrop / close-button click
    this.el.querySelectorAll('[data-lead-slideover-close]').forEach((btn) => {
      btn.addEventListener('click', () => this.close());
    });
  }

  /* ------------------------------------------------------------------ */
  /*  Public API                                                         */
  /* ------------------------------------------------------------------ */

  open(lead, leads, solucoes) {
    if (!lead) return;
    this.lead = lead;
    this.leads = Array.isArray(leads) ? leads : [];
    this.solucoes = Array.isArray(solucoes) ? solucoes : [];
    this.selectedEtapaId = Number(lead.id_etapa || 0);
    this._render();
    this._loadComerciais();
    requestAnimationFrame(() => this.el.classList.add('open'));
  }

  close() {
    this.el.classList.remove('open');
  }

  /* ------------------------------------------------------------------ */
  /*  Helpers                                                            */
  /* ------------------------------------------------------------------ */

  _escapeHtml(str) {
    const text = String(str ?? '');
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  _getSolucao(lead) {
    const id = String(lead?.id_solucao ?? '');
    return this.solucoes.find((s) => String(s.id) === id) || null;
  }

  _getEtapas(solucao) {
    const raw = solucao && Array.isArray(solucao.etapas) && solucao.etapas.length > 0
      ? solucao.etapas
      : [
          { id: 1, nome_etapa: 'Triagem', color_HEX: '#626D84', ativo: 1, ordem_id: 1 },
          { id: 2, nome_etapa: 'Reuniao', color_HEX: '#2964D9', ativo: 1, ordem_id: 2 },
          { id: 3, nome_etapa: 'Proposta', color_HEX: '#F59F0A', ativo: 1, ordem_id: 3 },
          { id: 4, nome_etapa: 'Fechamento', color_HEX: '#16A249', ativo: 1, ordem_id: 4 },
        ];
    return raw
      .filter((e) => {
        const a = e && Object.prototype.hasOwnProperty.call(e, 'ativo') ? e.ativo : 1;
        return Number(a) === 1 || a === true || a === 'true';
      })
      .sort((a, b) => (Number(a.ordem_id ?? 999)) - (Number(b.ordem_id ?? 999)));
  }

  _getInfoFields(lead, solucao) {
    if (Array.isArray(lead.informacoes) && lead.informacoes.length > 0) {
      return lead.informacoes;
    }
    if (solucao && Array.isArray(solucao.registroInfo) && solucao.registroInfo.length > 0) {
      return solucao.registroInfo.map((f) => ({
        name: f.name || '',
        type: f.type || 'string',
        value: f.value ?? '',
      }));
    }
    return [];
  }

  /* ------------------------------------------------------------------ */
  /*  Render                                                             */
  /* ------------------------------------------------------------------ */

  _render() {
    const lead = this.lead;
    if (!lead) return;

    const solucao = this._getSolucao(lead);
    const etapas = this._getEtapas(solucao);
    const infoFields = this._getInfoFields(lead, solucao);

    // Header
    this.el.querySelector('[data-lead-name]').textContent = lead.name || 'Lead';
    const subtitleParts = [
      lead.company || lead.razao_social || '',
      lead.cnpj ? `CNPJ: ${lead.cnpj}` : '',
    ].filter(Boolean);
    this.el.querySelector('[data-lead-subtitle]').textContent = subtitleParts.join(' | ') || '-';

    // Content
    const content = this.el.querySelector('[data-lead-content]');
    content.innerHTML = '';

    // Solution badge
    if (solucao) {
      content.innerHTML += `
        <div class="slide-over-section">
          <div class="slide-over-tags">
            <span class="slide-over-tag">${this._escapeHtml(solucao.name || 'Solucao')}</span>
          </div>
        </div>
      `;
    }

    // Leads tabs (when multiple leads for the same comercial across solutions)
    const relatedLeads = this.leads.filter((l) =>
      String(l.id_comercial) === String(lead.id_comercial) && String(l.id) !== String(lead.id)
    );
    if (relatedLeads.length > 0) {
      const allLeads = [lead, ...relatedLeads];
      content.innerHTML += `
        <div class="slide-over-section">
          <h3 class="slide-over-section-title">Solucoes Vinculadas</h3>
          <div class="lead-info-tabs">
            <div class="lead-info-tabs-header">
              ${allLeads.map((l) => {
                const sol = this._getSolucao(l);
                const isActive = String(l.id) === String(lead.id);
                const color = sol?.accentColor || sol?.color || '';
                const style = color
                  ? `--tab-accent: ${color}; --tab-accent-foreground: #fff;`
                  : '';
                return `<button class="lead-info-tab ${isActive ? 'active' : ''}"
                          data-switch-lead-id="${this._escapeHtml(String(l.id))}"
                          style="${style}">
                  ${this._escapeHtml(sol?.name || 'Solucao')}
                </button>`;
              }).join('')}
            </div>
          </div>
        </div>
      `;
    }

    // Kanban stage pills
    content.innerHTML += `
      <div class="slide-over-section">
        <h3 class="slide-over-section-title">Estagio</h3>
        <div class="slide-over-tags" data-etapa-pills>
          ${etapas.map((etapa) => {
            const isActive = Number(etapa.id) === Number(this.selectedEtapaId);
            const bg = isActive ? (etapa.color_HEX || '#626D84') : 'transparent';
            const color = isActive ? '#fff' : 'hsl(var(--foreground))';
            const border = isActive ? 'transparent' : 'hsl(var(--border))';
            return `<button class="lead-info-tab ${isActive ? 'active' : ''}"
                      data-select-etapa="${etapa.id}"
                      style="--tab-accent: ${etapa.color_HEX || '#626D84'}; --tab-accent-foreground: #fff;">
              ${this._escapeHtml(etapa.nome_etapa)}
            </button>`;
          }).join('')}
        </div>
      </div>
    `;

    // General info
    content.innerHTML += `
      <div class="slide-over-section">
        <h3 class="slide-over-section-title">Informacoes Gerais</h3>
        <div class="slide-over-info-grid">
          <div class="slide-over-info-item">
            <i data-lucide="building-2"></i>
            <div class="slide-over-info-content">
              <div class="slide-over-info-label">Empresa</div>
              <div class="slide-over-info-value">${this._escapeHtml(lead.company || lead.razao_social || '-')}</div>
            </div>
          </div>
          <div class="slide-over-info-item">
            <i data-lucide="badge-check"></i>
            <div class="slide-over-info-content">
              <div class="slide-over-info-label">CNPJ</div>
              <div class="slide-over-info-value">${this._escapeHtml(lead.cnpj || '-')}</div>
            </div>
          </div>
          <div class="slide-over-info-item">
            <i data-lucide="user-check"></i>
            <div class="slide-over-info-content">
              <div class="slide-over-info-label">Responsavel Comercial</div>
              <select class="slide-over-info-select" data-lead-colab-comercial>
                <option value="">Carregando...</option>
              </select>
            </div>
          </div>
          ${lead.representante_parceiro_nome ? `
          <div class="slide-over-info-item">
            <i data-lucide="handshake"></i>
            <div class="slide-over-info-content">
              <div class="slide-over-info-label">Parceiro</div>
              <div class="slide-over-info-value">${this._escapeHtml(lead.representante_parceiro_nome)}</div>
            </div>
          </div>
          ` : ''}
        </div>
      </div>
    `;

    // Dynamic info fields
    if (infoFields.length > 0) {
      content.innerHTML += `
        <div class="slide-over-section">
          <h3 class="slide-over-section-title">Campos da Solucao</h3>
          <div class="lead-info-tabs">
            <div class="lead-info-tabs-body">
              <div class="lead-info-panel active" data-info-fields>
                ${infoFields.map((field, index) => {
                  const inputType = field.type === 'number' ? 'number' : 'text';
                  const isCheckbox = field.type === 'checkbox' || field.type === 'boolean';
                  if (isCheckbox) {
                    const checked = field.value === true || field.value === 'true' || field.value === 1 || field.value === '1';
                    return `
                      <div class="lead-info-field" data-info-index="${index}">
                        <span>${this._escapeHtml(field.name || 'Campo')}</span>
                        <input type="checkbox" data-info-name="${this._escapeHtml(field.name)}" data-info-type="${field.type || 'string'}" ${checked ? 'checked' : ''} />
                      </div>
                    `;
                  }
                  return `
                    <div class="lead-info-field" data-info-index="${index}">
                      <span>${this._escapeHtml(field.name || 'Campo')}</span>
                      <input type="${inputType}" data-info-name="${this._escapeHtml(field.name)}" data-info-type="${field.type || 'string'}" value="${this._escapeHtml(field.value ?? '')}" />
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // Footer
    const footer = this.el.querySelector('[data-lead-footer]');
    footer.innerHTML = `
      <button class="slide-over-btn slide-over-btn-primary" data-lead-save>Salvar</button>
      ${this.options.canDelete ? `
        <button class="slide-over-btn slide-over-btn-danger" data-lead-delete>Excluir</button>
      ` : ''}
      <button class="slide-over-btn slide-over-btn-secondary" data-lead-slideover-close>Fechar</button>
    `;

    this._bindEvents();
    this._initIcons();
  }

  /* ------------------------------------------------------------------ */
  /*  Events                                                             */
  /* ------------------------------------------------------------------ */

  _bindEvents() {
    // Close buttons (footer)
    this.el.querySelectorAll('[data-lead-slideover-close]').forEach((btn) => {
      btn.addEventListener('click', () => this.close());
    });

    // Stage pills
    this.el.querySelectorAll('[data-select-etapa]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.selectedEtapaId = Number(btn.getAttribute('data-select-etapa'));
        this._render();
        this._loadComerciais();
      });
    });

    // Solution tabs (switch lead)
    this.el.querySelectorAll('[data-switch-lead-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-switch-lead-id');
        const targetLead = this.leads.find((l) => String(l.id) === targetId);
        if (targetLead) {
          this.lead = targetLead;
          this.selectedEtapaId = Number(targetLead.id_etapa || 0);
          this._render();
          this._loadComerciais();
        }
      });
    });

    // Save
    const saveBtn = this.el.querySelector('[data-lead-save]');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this._save());
    }

    // Delete
    const deleteBtn = this.el.querySelector('[data-lead-delete]');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => this._delete());
    }

    // Track field changes
    this.el.querySelectorAll('[data-info-fields] input').forEach((input) => {
      input.addEventListener('input', () => {
        const field = input.closest('.lead-info-field');
        if (field) field.classList.add('field-changed');
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /*  Lucide icons                                                       */
  /* ------------------------------------------------------------------ */

  _initIcons() {
    try {
      if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
      }
    } catch (_) { /* noop */ }
  }

  /* ------------------------------------------------------------------ */
  /*  Load comerciais (responsavel dropdown)                             */
  /* ------------------------------------------------------------------ */

  async _loadComerciais() {
    if (Array.isArray(this.comerciais)) {
      this._populateComerciaisSelect();
      return;
    }
    try {
      const response = await fetch('/portfolio/api/comerciais');
      if (!response.ok) throw new Error(`Erro ${response.status}`);
      const payload = await response.json();
      this.comerciais = Array.isArray(payload?.comerciais) ? payload.comerciais : [];
    } catch (_) {
      this.comerciais = [];
    }
    this._populateComerciaisSelect();
  }

  _populateComerciaisSelect() {
    const select = this.el.querySelector('[data-lead-colab-comercial]');
    if (!select) return;

    const currentValue = this.lead?.id_colab_comercial != null
      ? String(this.lead.id_colab_comercial)
      : '';

    select.innerHTML = '<option value="">-- Nenhum --</option>';
    (this.comerciais || []).forEach((c) => {
      const id = c.id != null ? String(c.id) : '';
      const nome = c.nome || c.name || '';
      if (!id || !nome) return;
      const selected = id === currentValue ? 'selected' : '';
      select.innerHTML += `<option value="${this._escapeHtml(id)}" ${selected}>${this._escapeHtml(nome)}</option>`;
    });
  }

  /* ------------------------------------------------------------------ */
  /*  Collect info fields                                                */
  /* ------------------------------------------------------------------ */

  _collectInfoFields() {
    const fields = [];
    this.el.querySelectorAll('[data-info-fields] input').forEach((input) => {
      const name = input.getAttribute('data-info-name') || '';
      const type = input.getAttribute('data-info-type') || 'string';
      let value;
      if (input.type === 'checkbox') {
        value = input.checked;
      } else if (type === 'number') {
        value = input.value !== '' ? Number(input.value) : null;
      } else {
        value = input.value;
      }
      fields.push({ name, type, value });
    });
    return fields;
  }

  /* ------------------------------------------------------------------ */
  /*  Save                                                               */
  /* ------------------------------------------------------------------ */

  async _save() {
    const lead = this.lead;
    if (!lead) return;

    const saveBtn = this.el.querySelector('[data-lead-save]');
    if (saveBtn) saveBtn.disabled = true;

    const colabSelect = this.el.querySelector('[data-lead-colab-comercial]');
    const colabValue = colabSelect ? colabSelect.value : null;
    const id_colab_comercial = colabValue && String(colabValue).trim() !== ''
      ? String(colabValue)
      : null;

    const informacoes = this._collectInfoFields();

    const payload = {
      id_comercial: Number(lead.id_comercial),
      id_colab_comercial,
      solucoes: [
        {
          id_solucao: Number(lead.id_solucao),
          id_etapa_kanban: Number(this.selectedEtapaId),
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
        let detail = err?.detail || '';
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

      // Update lead object in-place so parent has fresh data
      lead.id_etapa = Number(this.selectedEtapaId);
      lead.id_colab_comercial = id_colab_comercial;
      lead.informacoes = informacoes;

      const solucao = this._getSolucao(lead);
      const etapas = this._getEtapas(solucao);
      const etapa = etapas.find((e) => Number(e.id) === Number(this.selectedEtapaId));
      if (etapa) lead.stage = etapa.nome_etapa;

      // Update colab name from select text
      if (colabSelect && colabSelect.selectedIndex >= 0) {
        const selectedOption = colabSelect.options[colabSelect.selectedIndex];
        if (selectedOption && selectedOption.value) {
          lead.colab_comercial_nome = selectedOption.textContent.trim();
        } else {
          lead.colab_comercial_nome = null;
        }
      }

      this.close();
      this._initIcons();

      if (typeof this.options.onSave === 'function') {
        this.options.onSave(lead);
      }
    } catch (error) {
      const message = error?.message || 'Nao foi possivel salvar o lead.';
      window.alert(message);
    } finally {
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Delete                                                             */
  /* ------------------------------------------------------------------ */

  async _delete() {
    const lead = this.lead;
    if (!lead) return;

    const confirmed = window.confirm(
      `Tem certeza que deseja excluir "${lead.name || 'este lead'}" desta solucao?`
    );
    if (!confirmed) return;

    const deleteBtn = this.el.querySelector('[data-lead-delete]');
    if (deleteBtn) deleteBtn.disabled = true;

    try {
      const idComercial = encodeURIComponent(String(lead.id_comercial));
      const idSolucao = encodeURIComponent(String(lead.id_solucao));
      const response = await fetch(`/portfolio/api/leads/${idComercial}/${idSolucao}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err?.detail || `Erro ${response.status}`);
      }

      this.close();

      if (typeof this.options.onDelete === 'function') {
        this.options.onDelete(lead);
      }
    } catch (error) {
      const message = error?.message || 'Nao foi possivel excluir o lead.';
      window.alert(message);
    } finally {
      if (deleteBtn) deleteBtn.disabled = false;
    }
  }
}

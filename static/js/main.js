// NovaCRM - Main JavaScript
console.log('NovaCRM - Initializing...');

// ========================================
// Sidebar Manager
// ========================================
class SidebarManager {
  constructor() {
    this.sidebar = document.querySelector('.sidebar');
    this.toggleBtn = document.querySelector('.toggle-btn');
    this.isCollapsed = false;

    this.init();
  }

  init() {
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => this.toggle());
    }

    const saved State = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
      this.collapse();
    }
  }

  toggle() {
    if (this.isCollapsed) {
      this.expand();
    } else {
      this.collapse();
    }
  }

  collapse() {
    document.querySelector('.sidebar')?.classList.add('collapsed');
    this.isCollapsed = true;
    localStorage.setItem('sidebarCollapsed', 'true');

    // Update icon
    const icon = document.querySelector('.toggle-btn i');
    if (icon) {
      icon.setAttribute('data-lucide', 'chevron-right');
      lucide.createIcons();
    }
  }

  expand() {
    document.querySelector('.sidebar')?.classList.remove('collapsed');
    this.isCollapsed = false;
    localStorage.setItem('sidebarCollapsed', 'false');

    // Update icon
    const icon = document.querySelector('.toggle-btn i');
    if (icon) {
      icon.setAttribute('data-lucide', 'chevron-left');
      lucide.createIcons();
    }
  }
}

// Partners Module Manager
class PartnersManager {
  constructor() {
    this.partners = [];
    this.selectedPartner = null;
    this.searchQuery = '';

    this.searchInput = document.getElementById('partner-search');
    this.partnerListEl = document.getElementById('partner-list');
    this.detailPanel = document.getElementById('partner-detail');

    this.init();
  }

  init() {
    // Load partners from window data
    if (window.PARTNERS_DATA) {
      this.partners = window.PARTNERS_DATA;
      this.renderPartnerList();

      // Select first partner by default
      if (this.partners.length > 0) {
        this.selectPartner(this.partners[0]);
      }
    }

    // Setup search
    const searchInput = document.getElementById('partnerSearch');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterPartners(e.target.value);
      });
    }
  }

  renderPartnerList(partners) {
    const partnerList = document.querySelector('.partner-list');
    if (!partnerList) return;

    if (partners.length === 0) {
      partnerList.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: hsl(var(--muted-foreground));">
          <p class="text-sm">Nenhum parceiro encontrado</p>
        </div>
      `;
      return;
    }

    const html = partners.map(partner => `
      <button class="partner-item" data-partner-id="${partner.id}">
        <div class="partner-header">
          <div style="min-width: 0; flex: 1;">
            <div class="partner-name">${partner.name}</div>
            <div class="partner-cnpj">${partner.cnpj}</div>
          </div>
          <span class="badge badge-${partner.status}">
            ${partner.status === 'active' ? 'Ativo' : partner.status === 'pending' ? 'Pendente' : 'Bloqueado'}
          </span>
        </div>
        ${partner.modules.length > 0 ? `
          <div class="module-tags">
            ${partner.modules.map(mod => `
              <span class="badge tag-${mod}">
                🏷️ ${mod === 'comercial' ? 'Comercial' : 'Indicador'}
              </span>
            `).join('')}
          </div>
        ` : ''}
      </button>
    `;
  }).join('');
}

function renderPartnerDetail(partner) {
  if (!partner) {
    return `
      <div class="empty-state">
        <i data-lucide="users" style="width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.5;"></i>
        <h3>Selecione um parceiro</h3>
        <p>Escolha um parceiro na lista para ver os detalhes</p>
      </div>
    `;
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('pt-BR');
  };

  const statusLabels = {
    'active': 'Ativo',
    'pending': 'Pendente',
    'blocked': 'Bloqueado'
  };

  const implantationLabels = {
    'pending': 'Pendente',
    'in_progress': 'Em Progresso',
    'completed': 'Concluído'
  };

  return `
    <div class="detail-panel fade-in">
      <!-- Header -->
      <div class="detail-header">
        <div class="detail-title-row">
          <div>
            <h1 class="detail-title">${partner.name}</h1>
            <p class="detail-subtitle">${partner.cnpj}</p>
          </div>
          <span class="badge badge-${partner.status}">
            ${partner.status === 'active' ? 'Ativo' : partner.status === 'pending' ? 'Pendente' : 'Bloqueado'}
          </span>
        </div>
      </div>

      <div class="detail-cards">
        <!-- Dados Cadastrais -->
        <div class="card">
          <div class="card-header">
            <i data-lucide="building-2" style="width: 16px; height: 16px;"></i>
            <h3 class="card-title">Dados Cadastrais</h3>
          </div>
          <div class="card-content">
            ${partner.address ? `
              <div class="info-row">
                <i data-lucide="map-pin"></i>
                <div>
                  <div class="info-label">Endereço</div>
                  <div class="info-value">${partner.address}</div>
                </div>
              </div>
            ` : ''}
            ${partner.email ? `
              <div class="info-row">
                <i data-lucide="mail" style="width: 16px; height: 16px;"></i>
                <div>
                  <div class="info-label">E-mail</div>
                  <div class="info-value">${partner.email}</div>
                </div>
              </div>
            ` : ''}
            ${partner.phone ? `
              <div class="info-row">
                <i data-lucide="phone" style="width: 16px; height: 16px; color: hsl(var(--muted-foreground)); flex-shrink: 0;"></i>
                <div>
                  <div class="info-label">Telefone</div>
                  <div class="info-value">${partner.phone}</div>
                </div>
              </div>
            ` : ''}
            ${partner.createdAt ? `
              <div class="info-row">
                <i data-lucide="calendar" style="width: 16px; height: 16px; color: hsl(var(--muted-foreground));"></i>
                <div>
                  <div class="info-label">Cadastro</div>
                  <div class="info-value">${this.formatDate(partner.createdAt)}</div>
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        ${partner.modules.includes('comercial') && partner.comercialContract ? `
          <div class="card">
            <div class="card-header">
              <span style="width: 8px; height: 8px; border-radius: 50%; background-color: hsl(var(--comercial));"></span>
              <span class="card-title">Módulo Comercial</span>
            </div>
            <div class="card-content">
              <div>
                <div class="info-label">Valor do Contrato</div>
                <div style="font-size: 1.125rem; font-weight: 600; color: hsl(var(--foreground)); margin-top: 0.25rem;">
                  ${this.formatCurrency(partner.comercialContract.value)}
                </div>
              </div>
              <div>
                <div class="info-label">Período</div>
                <div class="info-value" style="margin-top: 0.25rem;">
                  ${this.formatDate(partner.comercialContract.startDate)} - ${this.formatDate(partner.comercialContract.endDate)}
                </div>
              </div>
              <div>
                <div class="info-label">Implantação</div>
                <div style="margin-top: 0.25rem;">
                  ${this.getImplantationBadge(partner.comercialContract.implantationStatus)}
                </div>
              </div>
            </div>
          </div>
        ` : ''}

        ${partner.modules.includes('indicador') && partner.indicadorData ? `
          <div class="card">
            <div class="card-header">
              <span style="width: 8px; height: 8px; border-radius: 50%; background-color: hsl(var(--indicador));"></span>
              <span class="card-title">Módulo Indicador</span>
            </div>
            <div class="card-content">
              <div>
                <div class="info-label">Leads Gerados</div>
                <div style="font-size: 1.5rem; font-weight: 600; color: hsl(var(--foreground)); margin-top: 0.25rem;">
                  ${partner.indicadorData.leadsGenerated}
                </div>
              </div>
              <div>
                <div class="info-label">Taxa de Conversão</div>
                <div style="font-size: 1.5rem; font-weight: 600; color: hsl(var(--foreground)); margin-top: 0.25rem;">
                  ${partner.indicadorData.conversionRate}%
                </div>
              </div>
            </div>
          </div>
        ` : ''}
      </div>
    `;

    this.detailPanel.innerHTML = html;
    lucide.createIcons();
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  }

  formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  getStatusBadge(status) {
    const labels = {
      active: 'Ativo',
      pending: 'Pendente',
      blocked: 'Bloqueado'
    };
    return `<span class="badge badge-${status}">${labels[status]}</span>`;
  }

  getImplantationBadge(status) {
    const config = {
      pending: { label: 'Pendente', class: 'badge-pending' },
      in_progress: { label: 'Em Progresso', class: 'badge-active' },
      completed: { label: 'Concluído', class: 'badge-active' }
    };
    const { label, class: className } = config[status];
    return `<span class="badge ${className}">${label}</span>`;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('NovaCRM - Initializing...');

  new SidebarManager();
  new ViewManager();
  new NotificationManager();
  new KPIManager();
  new PartnersModule();

  console.log('NovaCRM - Ready!');
});

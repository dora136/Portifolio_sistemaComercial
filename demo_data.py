from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DemoStore:
    comerciais: list[dict[str, Any]]
    solucoes: list[dict[str, Any]]
    parceiros: list[dict[str, Any]]
    parceiros_kanban: list[dict[str, Any]]
    leads: list[dict[str, Any]]
    contratos_entradas: list[dict[str, Any]]
    contratos_saidas: list[dict[str, Any]]


def _default_etapas() -> list[dict[str, Any]]:
    return [
        {"id": 1, "nome_etapa": "Triagem", "color_HEX": "#626D84", "ativo": 1, "ordem_id": 1, "sucesso": 0, "perdido": 0},
        {"id": 2, "nome_etapa": "Reunião", "color_HEX": "#2964D9", "ativo": 1, "ordem_id": 2, "sucesso": 0, "perdido": 0},
        {"id": 3, "nome_etapa": "Proposta", "color_HEX": "#F59F0A", "ativo": 1, "ordem_id": 3, "sucesso": 0, "perdido": 0},
        {"id": 4, "nome_etapa": "Fechamento", "color_HEX": "#16A249", "ativo": 1, "ordem_id": 4, "sucesso": 1, "perdido": 0},
        {"id": 5, "nome_etapa": "Perdido", "color_HEX": "#DC2626", "ativo": 1, "ordem_id": 5, "sucesso": 0, "perdido": 1},
    ]


def _seed_store() -> DemoStore:
    comerciais = [
        {"id_col": 101, "id_crm_colab": "5001", "nome": "Aline Torres", "status": "ativo"},
        {"id_col": 102, "id_crm_colab": "5002", "nome": "Bruno Lima", "status": "ativo"},
        {"id_col": 103, "id_crm_colab": "5003", "nome": "Camila Rocha", "status": "ativo"},
        {"id_col": 104, "id_crm_colab": "5004", "nome": "Diego Prado", "status": "ativo"},
    ]

    solucoes = [
        {
            "id": 1,
            "id_solucao": 1,
            "name": "Cloud Computing",
            "nome_solucao": "Cloud Computing",
            "category": "Tecnologia",
            "tipo_solucao": "Tecnologia",
            "description": "Soluções de infraestrutura em nuvem para empresas de médio e grande porte.",
            "descricao": "Soluções de infraestrutura em nuvem para empresas de médio e grande porte.",
            "applications": ["Migração para nuvem", "Infraestrutura como serviço", "Ambientes híbridos"],
            "aplicacoes_basicas": ["Migração para nuvem", "Infraestrutura como serviço", "Ambientes híbridos"],
            "partnersCount": 3,
            "n_parceiros": 3,
            "icon": "cloud",
            "icon_id": "cloud",
            "color": "cloud",
            "color_id": "cloud",
            "accentVar": "cloud",
            "avgTicket": 350000,
            "avgImplementation": "3 a 5 meses",
            "kanbanEtapas": _default_etapas(),
            "kanban_etapas": _default_etapas(),
            "registroInfo": [{"name": "Servidores", "type": "number"}, {"name": "Provedor cloud", "type": "string"}],
            "registro_info": [{"name": "Servidores", "type": "number"}, {"name": "Provedor cloud", "type": "string"}],
        },
        {
            "id": 2,
            "id_solucao": 2,
            "name": "Data Analytics",
            "nome_solucao": "Data Analytics",
            "category": "Análise",
            "tipo_solucao": "Análise",
            "description": "Plataformas de análise de dados e inteligência de negócios para tomada de decisão.",
            "descricao": "Plataformas de análise de dados e inteligência de negócios para tomada de decisão.",
            "applications": ["Dashboards", "ETL e pipelines", "Machine Learning"],
            "aplicacoes_basicas": ["Dashboards", "ETL e pipelines", "Machine Learning"],
            "partnersCount": 2,
            "n_parceiros": 2,
            "icon": "line-chart",
            "icon_id": "line-chart",
            "color": "analytics",
            "color_id": "analytics",
            "accentVar": "analytics",
            "avgTicket": 275000,
            "avgImplementation": "2 a 4 meses",
            "kanbanEtapas": _default_etapas(),
            "kanban_etapas": _default_etapas(),
            "registroInfo": [{"name": "Volume de dados (GB)", "type": "number"}, {"name": "Plataforma atual", "type": "string"}],
            "registro_info": [{"name": "Volume de dados (GB)", "type": "number"}, {"name": "Plataforma atual", "type": "string"}],
        },
        {
            "id": 3,
            "id_solucao": 3,
            "name": "Cybersecurity",
            "nome_solucao": "Cybersecurity",
            "category": "Segurança",
            "tipo_solucao": "Segurança",
            "description": "Soluções de segurança cibernética para proteção de dados e conformidade regulatória.",
            "descricao": "Soluções de segurança cibernética para proteção de dados e conformidade regulatória.",
            "applications": ["Pentest", "SOC", "Compliance LGPD"],
            "aplicacoes_basicas": ["Pentest", "SOC", "Compliance LGPD"],
            "partnersCount": 2,
            "n_parceiros": 2,
            "icon": "shield",
            "icon_id": "shield",
            "color": "cyber",
            "color_id": "cyber",
            "accentVar": "cyber",
            "avgTicket": 480000,
            "avgImplementation": "4 a 8 meses",
            "kanbanEtapas": _default_etapas(),
            "kanban_etapas": _default_etapas(),
            "registroInfo": [{"name": "Endpoints monitorados", "type": "number"}, {"name": "Framework de compliance", "type": "string"}],
            "registro_info": [{"name": "Endpoints monitorados", "type": "number"}, {"name": "Framework de compliance", "type": "string"}],
        },
        {
            "id": 4,
            "id_solucao": 4,
            "name": "Consulting",
            "nome_solucao": "Consulting",
            "category": "Consultoria",
            "tipo_solucao": "Consultoria",
            "description": "Consultoria técnica em transformação digital, arquitetura e governança de TI.",
            "descricao": "Consultoria técnica em transformação digital, arquitetura e governança de TI.",
            "applications": ["Arquitetura de sistemas", "Governança de TI", "Transformação digital"],
            "aplicacoes_basicas": ["Arquitetura de sistemas", "Governança de TI", "Transformação digital"],
            "partnersCount": 2,
            "n_parceiros": 2,
            "icon": "briefcase",
            "icon_id": "briefcase",
            "color": "consulting",
            "color_id": "consulting",
            "accentVar": "consulting",
            "avgTicket": 160000,
            "avgImplementation": "1 a 3 meses",
            "kanbanEtapas": _default_etapas(),
            "kanban_etapas": _default_etapas(),
            "registroInfo": [{"name": "Colaboradores envolvidos", "type": "number"}, {"name": "Área de atuação", "type": "string"}],
            "registro_info": [{"name": "Colaboradores envolvidos", "type": "number"}, {"name": "Área de atuação", "type": "string"}],
        },
    ]

    parceiros = [
        {
            "id": "201",
            "name": "Aurora Partners",
            "nome": "Aurora Partners",
            "razaoSocial": "Aurora Partners Consultoria Ltda",
            "razao_social": "Aurora Partners Consultoria Ltda",
            "cnpj": "12.345.678/0001-90",
            "status": "active",
            "modules": ["comercial", "indicador"],
            "state": "SP",
            "createdAt": "2026-01-15",
            "email": "contato@aurorapartners.demo",
            "phone": "(11) 98888-1001",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 1, "name": "Cloud Computing", "icon": "cloud", "color": "hsl(24 100% 85%)", "status": "active", "closedLeads": 4},
                {"id_solucao": 2, "name": "Data Analytics", "icon": "line-chart", "color": "hsl(14 100% 82%)", "status": "active", "closedLeads": 2},
            ],
            "indicadorData": {"leadsGenerated": 16, "leadsNegotiation": 6, "leadsClosed": 4, "conversionRate": 25},
        },
        {
            "id": "202",
            "name": "Blue Grid",
            "nome": "Blue Grid",
            "razaoSocial": "Blue Grid Engenharia S.A.",
            "razao_social": "Blue Grid Engenharia S.A.",
            "cnpj": "23.456.789/0001-01",
            "status": "active",
            "modules": ["comercial"],
            "state": "MG",
            "createdAt": "2026-01-30",
            "email": "parcerias@bluegrid.demo",
            "phone": "(31) 97777-1002",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 3, "name": "Cybersecurity", "icon": "shield", "color": "hsl(357 62% 75%)", "status": "active", "closedLeads": 3},
            ],
            "indicadorData": None,
        },
        {
            "id": "203",
            "name": "Croma Engineering",
            "nome": "Croma Engineering",
            "razaoSocial": "Croma Engineering Projetos Ltda",
            "razao_social": "Croma Engineering Projetos Ltda",
            "cnpj": "34.567.890/0001-12",
            "status": "pending",
            "modules": ["indicador"],
            "state": "PR",
            "createdAt": "2026-02-10",
            "email": "comercial@croma.demo",
            "phone": "(41) 96666-1003",
            "folPath": "",
            "comercialSolutions": [],
            "indicadorData": {"leadsGenerated": 8, "leadsNegotiation": 3, "leadsClosed": 1, "conversionRate": 12},
        },
        {
            "id": "204",
            "name": "Delta Comercial Lab",
            "nome": "Delta Comercial Lab",
            "razaoSocial": "Delta Lab Inovação Ltda",
            "razao_social": "Delta Lab Inovação Ltda",
            "cnpj": "45.678.901/0001-23",
            "status": "blocked",
            "modules": [],
            "state": "SC",
            "createdAt": "2025-12-05",
            "email": "oi@deltalab.demo",
            "phone": "(48) 95555-1004",
            "folPath": "",
            "comercialSolutions": [],
            "indicadorData": None,
        },
        {
            "id": "205",
            "name": "TechFlow Solutions",
            "nome": "TechFlow Solutions",
            "razaoSocial": "TechFlow Solutions Tecnologia Ltda",
            "razao_social": "TechFlow Solutions Tecnologia Ltda",
            "cnpj": "56.789.012/0001-34",
            "status": "active",
            "modules": ["comercial", "indicador"],
            "state": "SP",
            "createdAt": "2026-02-20",
            "email": "contato@techflowsolutions.demo",
            "phone": "(11) 94321-2005",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 1, "name": "Cloud Computing", "icon": "cloud", "color": "hsl(24 100% 85%)", "status": "active", "closedLeads": 3},
                {"id_solucao": 2, "name": "Data Analytics", "icon": "line-chart", "color": "hsl(14 100% 82%)", "status": "active", "closedLeads": 1},
            ],
            "indicadorData": {"leadsGenerated": 12, "leadsNegotiation": 5, "leadsClosed": 3, "conversionRate": 25},
        },
        {
            "id": "206",
            "name": "DataBridge Corp",
            "nome": "DataBridge Corp",
            "razaoSocial": "DataBridge Corp Serviços Digitais S.A.",
            "razao_social": "DataBridge Corp Serviços Digitais S.A.",
            "cnpj": "67.890.123/0001-45",
            "status": "active",
            "modules": ["comercial"],
            "state": "RJ",
            "createdAt": "2026-01-25",
            "email": "contato@databridgecorp.demo",
            "phone": "(21) 93456-2006",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 4, "name": "Consulting", "icon": "briefcase", "color": "hsl(268 7% 44%)", "status": "active", "closedLeads": 2},
            ],
            "indicadorData": None,
        },
        {
            "id": "207",
            "name": "SecureNet Brasil",
            "nome": "SecureNet Brasil",
            "razaoSocial": "SecureNet Brasil Segurança da Informação Ltda",
            "razao_social": "SecureNet Brasil Segurança da Informação Ltda",
            "cnpj": "78.901.234/0001-56",
            "status": "pending",
            "modules": ["indicador"],
            "state": "MG",
            "createdAt": "2026-03-05",
            "email": "contato@securenetbrasil.demo",
            "phone": "(31) 92789-2007",
            "folPath": "",
            "comercialSolutions": [],
            "indicadorData": {"leadsGenerated": 5, "leadsNegotiation": 2, "leadsClosed": 0, "conversionRate": 0},
        },
        {
            "id": "208",
            "name": "CloudPeak Tecnologia",
            "nome": "CloudPeak Tecnologia",
            "razaoSocial": "CloudPeak Tecnologia e Inovação Ltda",
            "razao_social": "CloudPeak Tecnologia e Inovação Ltda",
            "cnpj": "89.012.345/0001-67",
            "status": "active",
            "modules": ["comercial", "indicador"],
            "state": "RS",
            "createdAt": "2026-02-01",
            "email": "contato@cloudpeaktec.demo",
            "phone": "(51) 91234-2008",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 1, "name": "Cloud Computing", "icon": "cloud", "color": "hsl(24 100% 85%)", "status": "active", "closedLeads": 2},
                {"id_solucao": 3, "name": "Cybersecurity", "icon": "shield", "color": "hsl(357 62% 75%)", "status": "active", "closedLeads": 1},
            ],
            "indicadorData": {"leadsGenerated": 9, "leadsNegotiation": 4, "leadsClosed": 2, "conversionRate": 22},
        },
        {
            "id": "209",
            "name": "Nexus Digital",
            "nome": "Nexus Digital",
            "razaoSocial": "Nexus Digital Soluções Empresariais Ltda",
            "razao_social": "Nexus Digital Soluções Empresariais Ltda",
            "cnpj": "90.123.456/0001-78",
            "status": "active",
            "modules": ["comercial"],
            "state": "BA",
            "createdAt": "2026-02-15",
            "email": "contato@nexusdigital.demo",
            "phone": "(71) 98765-2009",
            "folPath": "",
            "comercialSolutions": [
                {"id_solucao": 2, "name": "Data Analytics", "icon": "line-chart", "color": "hsl(14 100% 82%)", "status": "active", "closedLeads": 1},
                {"id_solucao": 4, "name": "Consulting", "icon": "briefcase", "color": "hsl(268 7% 44%)", "status": "active", "closedLeads": 0},
            ],
            "indicadorData": None,
        },
    ]

    parceiros_kanban = [
        {"id": "pk1", "id_comercial": 201, "id_solucao": 1, "id_status_kanban": 2, "name": "Aurora Partners", "razao_social": "Aurora Partners Consultoria Ltda", "cnpj": "12.345.678/0001-90", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_colab_comercial": 101, "colab_comercial_nome": "Aline Torres", "value": 420000},
        {"id": "pk2", "id_comercial": 202, "id_solucao": 3, "id_status_kanban": 3, "name": "Blue Grid", "razao_social": "Blue Grid Engenharia S.A.", "cnpj": "23.456.789/0001-01", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_colab_comercial": 102, "colab_comercial_nome": "Bruno Lima", "value": 780000},
        {"id": "pk3", "id_comercial": 203, "id_solucao": 4, "id_status_kanban": 1, "name": "Croma Engineering", "razao_social": "Croma Engineering Projetos Ltda", "cnpj": "34.567.890/0001-12", "id_colab_comercial": "5003", "colab_comercial_nome": "Camila Rocha", "id_colab_comercial": 103, "colab_comercial_nome": "Camila Rocha", "value": 190000},
        {"id": "pk4", "id_comercial": 205, "id_solucao": 1, "id_status_kanban": 2, "name": "TechFlow Solutions", "razao_social": "TechFlow Solutions Tecnologia Ltda", "cnpj": "56.789.012/0001-34", "id_colab_comercial": "5004", "colab_comercial_nome": "Diego Prado", "id_colab_comercial": 104, "colab_comercial_nome": "Diego Prado", "value": 540000},
        {"id": "pk5", "id_comercial": 208, "id_solucao": 3, "id_status_kanban": 3, "name": "CloudPeak Tecnologia", "razao_social": "CloudPeak Tecnologia e Inovação Ltda", "cnpj": "89.012.345/0001-67", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_colab_comercial": 101, "colab_comercial_nome": "Aline Torres", "value": 670000},
        {"id": "pk6", "id_comercial": 209, "id_solucao": 2, "id_status_kanban": 1, "name": "Nexus Digital", "razao_social": "Nexus Digital Soluções Empresariais Ltda", "cnpj": "90.123.456/0001-78", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_colab_comercial": 102, "colab_comercial_nome": "Bruno Lima", "value": 310000},
    ]

    leads = [
        {"id": "l1", "id_comercial": 301, "id_solucao": 1, "id_etapa": 2, "stage": "Reunião", "name": "Clara Martins", "company": "Grupo Horizonte", "nome_fantasia": "Grupo Horizonte", "razao_social": "Grupo Horizonte Indústria Ltda", "cnpj": "11.222.333/0001-44", "comercial_nome": "Aline Torres", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_comercial_parceiro": 201, "parceiro": "Aurora Partners", "representante_parceiro_nome": "Aurora Partners", "value": 380000, "informacoes": [{"name": "Servidores", "type": "number", "value": "45"}], "lastAction": "2026-03-15", "createdAt": "2026-03-02"},
        {"id": "l2", "id_comercial": 302, "id_solucao": 2, "id_etapa": 3, "stage": "Proposta", "name": "Rafael Teixeira", "company": "Nova Log", "nome_fantasia": "Nova Log", "razao_social": "Nova Log Transportes S.A.", "cnpj": "22.333.444/0001-55", "comercial_nome": "Bruno Lima", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_comercial_parceiro": 201, "parceiro": "Aurora Partners", "representante_parceiro_nome": "Aurora Partners", "value": 215000, "informacoes": [{"name": "Volume de dados (GB)", "type": "number", "value": "1200"}], "lastAction": "2026-03-12", "createdAt": "2026-02-26"},
        {"id": "l3", "id_comercial": 303, "id_solucao": 3, "id_etapa": 4, "stage": "Fechamento", "name": "Paula Nunes", "company": "Prisma Alimentos", "nome_fantasia": "Prisma Alimentos", "razao_social": "Prisma Alimentos Processados Ltda", "cnpj": "33.444.555/0001-66", "comercial_nome": "Bruno Lima", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_comercial_parceiro": 202, "parceiro": "Blue Grid", "representante_parceiro_nome": "Blue Grid", "value": 790000, "informacoes": [{"name": "Endpoints monitorados", "type": "number", "value": "650"}], "lastAction": "2026-03-17", "createdAt": "2026-02-20"},
        {"id": "l4", "id_comercial": 304, "id_solucao": 4, "id_etapa": 1, "stage": "Triagem", "name": "Felipe Moraes", "company": "Condomínio Bela Vista", "nome_fantasia": "Condomínio Bela Vista", "razao_social": "Condomínio Bela Vista", "cnpj": "44.555.666/0001-77", "comercial_nome": "Camila Rocha", "id_colab_comercial": "5003", "colab_comercial_nome": "Camila Rocha", "id_comercial_parceiro": 203, "parceiro": "Croma Engineering", "representante_parceiro_nome": "Croma Engineering", "value": 145000, "informacoes": [{"name": "Colaboradores envolvidos", "type": "number", "value": "25"}], "lastAction": "2026-03-10", "createdAt": "2026-03-04"},
        {"id": "l5", "id_comercial": 305, "id_solucao": 1, "id_etapa": 5, "stage": "Perdido", "name": "Juliana Castro", "company": "Tecelagem Prime", "nome_fantasia": "Tecelagem Prime", "razao_social": "Tecelagem Prime Ltda", "cnpj": "55.666.777/0001-88", "comercial_nome": "Diego Prado", "id_colab_comercial": "5004", "colab_comercial_nome": "Diego Prado", "id_comercial_parceiro": 201, "parceiro": "Aurora Partners", "representante_parceiro_nome": "Aurora Partners", "value": 260000, "informacoes": [], "lastAction": "2026-03-08", "createdAt": "2026-02-18"},
        {"id": "l6", "id_comercial": 306, "id_solucao": 2, "id_etapa": 2, "stage": "Reunião", "name": "Marcos Vinicius", "company": "Central Frio", "nome_fantasia": "Central Frio", "razao_social": "Central Frio Refrigeração Ltda", "cnpj": "66.777.888/0001-99", "comercial_nome": "Aline Torres", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_comercial_parceiro": 201, "parceiro": "Aurora Partners", "representante_parceiro_nome": "Aurora Partners", "value": 330000, "informacoes": [], "lastAction": "2026-03-16", "createdAt": "2026-03-01"},
        {"id": "l7", "id_comercial": 307, "id_solucao": 1, "id_etapa": 1, "stage": "Triagem", "name": "Ricardo Gomes", "company": "Grupo Orbital", "nome_fantasia": "Grupo Orbital", "razao_social": "Grupo Orbital Indústria e Comércio Ltda", "cnpj": "77.888.999/0001-10", "comercial_nome": "Camila Rocha", "id_colab_comercial": "5003", "colab_comercial_nome": "Camila Rocha", "id_comercial_parceiro": 205, "parceiro": "TechFlow Solutions", "representante_parceiro_nome": "TechFlow Solutions", "value": 420000, "informacoes": [{"name": "Servidores", "type": "number", "value": "80"}, {"name": "Provedor cloud", "type": "string", "value": "AWS"}], "lastAction": "2026-03-18", "createdAt": "2026-03-10"},
        {"id": "l8", "id_comercial": 308, "id_solucao": 3, "id_etapa": 2, "stage": "Reunião", "name": "Fernanda Alves", "company": "Minerva Tech", "nome_fantasia": "Minerva Tech", "razao_social": "Minerva Tech Soluções em TI S.A.", "cnpj": "88.999.000/0001-21", "comercial_nome": "Diego Prado", "id_colab_comercial": "5004", "colab_comercial_nome": "Diego Prado", "id_comercial_parceiro": 208, "parceiro": "CloudPeak Tecnologia", "representante_parceiro_nome": "CloudPeak Tecnologia", "value": 580000, "informacoes": [{"name": "Endpoints monitorados", "type": "number", "value": "320"}, {"name": "Framework de compliance", "type": "string", "value": "ISO 27001"}], "lastAction": "2026-03-17", "createdAt": "2026-03-05"},
        {"id": "l9", "id_comercial": 309, "id_solucao": 2, "id_etapa": 3, "stage": "Proposta", "name": "André Lacerda", "company": "Zenith Sistemas", "nome_fantasia": "Zenith Sistemas", "razao_social": "Zenith Sistemas de Gestão Ltda", "cnpj": "99.000.111/0001-32", "comercial_nome": "Bruno Lima", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_comercial_parceiro": 209, "parceiro": "Nexus Digital", "representante_parceiro_nome": "Nexus Digital", "value": 295000, "informacoes": [{"name": "Volume de dados (GB)", "type": "number", "value": "850"}, {"name": "Plataforma atual", "type": "string", "value": "SQL Server on-prem"}], "lastAction": "2026-03-16", "createdAt": "2026-02-28"},
        {"id": "l10", "id_comercial": 310, "id_solucao": 4, "id_etapa": 4, "stage": "Fechamento", "name": "Tatiana Ribeiro", "company": "Atlas Logística", "nome_fantasia": "Atlas Logística", "razao_social": "Atlas Logística e Distribuição S.A.", "cnpj": "10.111.222/0001-43", "comercial_nome": "Aline Torres", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_comercial_parceiro": 206, "parceiro": "DataBridge Corp", "representante_parceiro_nome": "DataBridge Corp", "value": 175000, "informacoes": [{"name": "Colaboradores envolvidos", "type": "number", "value": "40"}, {"name": "Área de atuação", "type": "string", "value": "Governança de TI"}], "lastAction": "2026-03-18", "createdAt": "2026-02-15"},
        {"id": "l11", "id_comercial": 311, "id_solucao": 1, "id_etapa": 5, "stage": "Perdido", "name": "Lucas Mendonça", "company": "Vanguard Corp", "nome_fantasia": "Vanguard Corp", "razao_social": "Vanguard Corp Investimentos Ltda", "cnpj": "21.222.333/0001-54", "comercial_nome": "Camila Rocha", "id_colab_comercial": "5003", "colab_comercial_nome": "Camila Rocha", "id_comercial_parceiro": 205, "parceiro": "TechFlow Solutions", "representante_parceiro_nome": "TechFlow Solutions", "value": 310000, "informacoes": [{"name": "Servidores", "type": "number", "value": "30"}], "lastAction": "2026-03-06", "createdAt": "2026-02-10"},
        {"id": "l12", "id_comercial": 312, "id_solucao": 3, "id_etapa": 3, "stage": "Proposta", "name": "Isabela Campos", "company": "Prime Digital", "nome_fantasia": "Prime Digital", "razao_social": "Prime Digital Marketing e Tecnologia Ltda", "cnpj": "32.333.444/0001-65", "comercial_nome": "Bruno Lima", "id_colab_comercial": "5002", "colab_comercial_nome": "Bruno Lima", "id_comercial_parceiro": 202, "parceiro": "Blue Grid", "representante_parceiro_nome": "Blue Grid", "value": 650000, "informacoes": [{"name": "Endpoints monitorados", "type": "number", "value": "500"}, {"name": "Framework de compliance", "type": "string", "value": "LGPD + PCI-DSS"}], "lastAction": "2026-03-14", "createdAt": "2026-02-22"},
        {"id": "l13", "id_comercial": 313, "id_solucao": 2, "id_etapa": 1, "stage": "Triagem", "name": "Gabriel Fonseca", "company": "Horizon Labs", "nome_fantasia": "Horizon Labs", "razao_social": "Horizon Labs Pesquisa e Desenvolvimento Ltda", "cnpj": "43.444.555/0001-76", "comercial_nome": "Diego Prado", "id_colab_comercial": "5004", "colab_comercial_nome": "Diego Prado", "id_comercial_parceiro": 205, "parceiro": "TechFlow Solutions", "representante_parceiro_nome": "TechFlow Solutions", "value": 240000, "informacoes": [{"name": "Volume de dados (GB)", "type": "number", "value": "2400"}], "lastAction": "2026-03-19", "createdAt": "2026-03-12"},
        {"id": "l14", "id_comercial": 314, "id_solucao": 4, "id_etapa": 2, "stage": "Reunião", "name": "Mariana Duarte", "company": "Quantum Analytics", "nome_fantasia": "Quantum Analytics", "razao_social": "Quantum Analytics Consultoria Empresarial S.A.", "cnpj": "54.555.666/0001-87", "comercial_nome": "Aline Torres", "id_colab_comercial": "5001", "colab_comercial_nome": "Aline Torres", "id_comercial_parceiro": 209, "parceiro": "Nexus Digital", "representante_parceiro_nome": "Nexus Digital", "value": 890000, "informacoes": [{"name": "Colaboradores envolvidos", "type": "number", "value": "120"}, {"name": "Área de atuação", "type": "string", "value": "Transformação digital"}], "lastAction": "2026-03-15", "createdAt": "2026-03-03"},
    ]

    contratos_entradas = [
        {
            "id_contrato": 9001, "id_comercial_lead": 301, "id_solucao": 1, "id_comercial_parceiro": 201, "id_responsavel": 101,
            "status": "Pendente", "num_colunas": 3, "lead_nome": "Clara Martins", "lead_razao_social": "Grupo Horizonte Indústria Ltda",
            "lead_cnpj": "11.222.333/0001-44", "lead_email": "contato@grupohorizonte.demo", "lead_telefone": "(11) 97777-4001",
            "parceiro_nome": "Aurora Partners", "nome_solucao": "Cloud Computing", "modelo_contrato": "SaaS License",
            "infos_json": {"campos": {"receita": "380000", "custo": "120000"}}, "campos": {"receita": "380000", "custo": "120000"},
            "parcelas": [
                {"id_financeiro": 1, "referencia_esperado": "2026-04-10", "referencia_real": None, "valor_esperado": 120000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 2, "referencia_esperado": "2026-05-10", "referencia_real": None, "valor_esperado": 130000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 3, "referencia_esperado": "2026-06-10", "referencia_real": None, "valor_esperado": 130000, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9002, "id_comercial_lead": 303, "id_solucao": 3, "id_comercial_parceiro": 202, "id_responsavel": 102,
            "status": "Em dia", "num_colunas": 2, "lead_nome": "Paula Nunes", "lead_razao_social": "Prisma Alimentos Processados Ltda",
            "lead_cnpj": "33.444.555/0001-66", "lead_email": "paula@prismaalimentos.demo", "lead_telefone": "(31) 98888-4002",
            "parceiro_nome": "Blue Grid", "nome_solucao": "Cybersecurity", "modelo_contrato": "Implementation + Support",
            "infos_json": {"campos": {"receita": "790000", "custo": "410000"}}, "campos": {"receita": "790000", "custo": "410000"},
            "parcelas": [
                {"id_financeiro": 4, "referencia_esperado": "2026-03-05", "referencia_real": "2026-03-05", "valor_esperado": 395000, "valor_real": 395000, "status_parcela": 1},
                {"id_financeiro": 5, "referencia_esperado": "2026-04-05", "referencia_real": None, "valor_esperado": 395000, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9003, "id_comercial_lead": 302, "id_solucao": 2, "id_comercial_parceiro": 201, "id_responsavel": 102,
            "status": "Atrasado", "num_colunas": 2, "lead_nome": "Rafael Teixeira", "lead_razao_social": "Nova Log Transportes S.A.",
            "lead_cnpj": "22.333.444/0001-55", "lead_email": "rafael@novalog.demo", "lead_telefone": "(21) 96666-4003",
            "parceiro_nome": "Aurora Partners", "nome_solucao": "Data Analytics", "modelo_contrato": "Migration Fee",
            "infos_json": {"campos": {"receita": "215000", "custo": "80000"}}, "campos": {"receita": "215000", "custo": "80000"},
            "parcelas": [
                {"id_financeiro": 6, "referencia_esperado": "2026-02-15", "referencia_real": None, "valor_esperado": 100000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 7, "referencia_esperado": "2026-03-15", "referencia_real": None, "valor_esperado": 115000, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9004, "id_comercial_lead": 310, "id_solucao": 4, "id_comercial_parceiro": 206, "id_responsavel": 101,
            "status": "Em dia", "num_colunas": 2, "lead_nome": "Tatiana Ribeiro", "lead_razao_social": "Atlas Logística e Distribuição S.A.",
            "lead_cnpj": "10.111.222/0001-43", "lead_email": "tatiana@atlaslogistica.demo", "lead_telefone": "(11) 93456-4010",
            "parceiro_nome": "DataBridge Corp", "nome_solucao": "Consulting", "modelo_contrato": "Consultoria Estratégica",
            "infos_json": {"campos": {"receita": "175000", "custo": "65000"}}, "campos": {"receita": "175000", "custo": "65000"},
            "parcelas": [
                {"id_financeiro": 8, "referencia_esperado": "2026-03-20", "referencia_real": None, "valor_esperado": 87500, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 9, "referencia_esperado": "2026-04-20", "referencia_real": None, "valor_esperado": 87500, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9005, "id_comercial_lead": 308, "id_solucao": 3, "id_comercial_parceiro": 208, "id_responsavel": 104,
            "status": "Pendente", "num_colunas": 3, "lead_nome": "Fernanda Alves", "lead_razao_social": "Minerva Tech Soluções em TI S.A.",
            "lead_cnpj": "88.999.000/0001-21", "lead_email": "fernanda@minervatech.demo", "lead_telefone": "(51) 92345-4011",
            "parceiro_nome": "CloudPeak Tecnologia", "nome_solucao": "Cybersecurity", "modelo_contrato": "SOC + Compliance",
            "infos_json": {"campos": {"receita": "580000", "custo": "290000"}}, "campos": {"receita": "580000", "custo": "290000"},
            "parcelas": [
                {"id_financeiro": 10, "referencia_esperado": "2026-04-01", "referencia_real": None, "valor_esperado": 193000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 11, "referencia_esperado": "2026-05-01", "referencia_real": None, "valor_esperado": 193000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 12, "referencia_esperado": "2026-06-01", "referencia_real": None, "valor_esperado": 194000, "valor_real": None, "status_parcela": 0},
            ],
        },
    ]

    contratos_saidas = [
        {
            "id_contrato": 9101, "id_comercial_lead": 301, "id_solucao": 1, "id_comercial_parceiro": 201, "id_responsavel": 101,
            "status": "Pendente", "num_colunas": 2, "lead_nome": "Clara Martins", "lead_razao_social": "Grupo Horizonte Indústria Ltda",
            "lead_cnpj": "11.222.333/0001-44", "lead_email": "contato@grupohorizonte.demo", "lead_telefone": "(11) 97777-4001",
            "parceiro_nome": "Aurora Partners", "nome_solucao": "Cloud Computing", "modelo_contrato": "Custos operacionais",
            "infos_json": {"campos": {"receita": "120000", "custo": "120000"}}, "campos": {"receita": "120000", "custo": "120000"},
            "parcelas": [
                {"id_financeiro": 101, "referencia_esperado": "2026-04-20", "referencia_real": None, "valor_esperado": 60000, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 102, "referencia_esperado": "2026-05-20", "referencia_real": None, "valor_esperado": 60000, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9102, "id_comercial_lead": 303, "id_solucao": 3, "id_comercial_parceiro": 202, "id_responsavel": 102,
            "status": "Em dia", "num_colunas": 2, "lead_nome": "Paula Nunes", "lead_razao_social": "Prisma Alimentos Processados Ltda",
            "lead_cnpj": "33.444.555/0001-66", "lead_email": "paula@prismaalimentos.demo", "lead_telefone": "(31) 98888-4002",
            "parceiro_nome": "Blue Grid", "nome_solucao": "Cybersecurity", "modelo_contrato": "Custos de implantação",
            "infos_json": {"campos": {"receita": "410000", "custo": "410000"}}, "campos": {"receita": "410000", "custo": "410000"},
            "parcelas": [
                {"id_financeiro": 103, "referencia_esperado": "2026-03-07", "referencia_real": "2026-03-07", "valor_esperado": 205000, "valor_real": 205000, "status_parcela": 1},
                {"id_financeiro": 104, "referencia_esperado": "2026-04-07", "referencia_real": None, "valor_esperado": 205000, "valor_real": None, "status_parcela": 0},
            ],
        },
        {
            "id_contrato": 9103, "id_comercial_lead": 310, "id_solucao": 4, "id_comercial_parceiro": 206, "id_responsavel": 101,
            "status": "Pendente", "num_colunas": 2, "lead_nome": "Tatiana Ribeiro", "lead_razao_social": "Atlas Logística e Distribuição S.A.",
            "lead_cnpj": "10.111.222/0001-43", "lead_email": "tatiana@atlaslogistica.demo", "lead_telefone": "(11) 93456-4010",
            "parceiro_nome": "DataBridge Corp", "nome_solucao": "Consulting", "modelo_contrato": "Custos de consultoria",
            "infos_json": {"campos": {"receita": "65000", "custo": "65000"}}, "campos": {"receita": "65000", "custo": "65000"},
            "parcelas": [
                {"id_financeiro": 105, "referencia_esperado": "2026-04-15", "referencia_real": None, "valor_esperado": 32500, "valor_real": None, "status_parcela": 0},
                {"id_financeiro": 106, "referencia_esperado": "2026-05-15", "referencia_real": None, "valor_esperado": 32500, "valor_real": None, "status_parcela": 0},
            ],
        },
    ]

    return DemoStore(
        comerciais=comerciais,
        solucoes=solucoes,
        parceiros=parceiros,
        parceiros_kanban=parceiros_kanban,
        leads=leads,
        contratos_entradas=contratos_entradas,
        contratos_saidas=contratos_saidas,
    )


STORE = _seed_store()


def _copy(data: Any) -> Any:
    return deepcopy(data)


def list_comerciais() -> list[dict[str, Any]]:
    return _copy(STORE.comerciais)


def get_solucoes(active_only: bool = False) -> list[dict[str, Any]]:
    return _copy(STORE.solucoes)


def get_solucoes_for_frontend() -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "category": item["category"],
            "description": item["description"],
            "applications": _copy(item["applications"]),
            "partnersCount": item["partnersCount"],
            "leads": [lead for lead in list_leads() if int(lead["id_solucao"]) == int(item["id"])],
            "avgTicket": item["avgTicket"],
            "avgImplementation": item["avgImplementation"],
            "icon": item["icon"],
            "color": item["color"],
            "accentVar": item["accentVar"],
            "kanbanEtapas": _copy(item["kanbanEtapas"]),
            "registroInfo": _copy(item["registroInfo"]),
            "etapas": _copy(item["kanbanEtapas"]),
            "partners": [p["name"] for p in STORE.parceiros if any(int(sol.get("id_solucao", 0)) == int(item["id"]) for sol in p.get("comercialSolutions", []))],
        }
        for item in STORE.solucoes
    ]


def list_parceiros() -> list[dict[str, Any]]:
    return _copy(STORE.parceiros)


def list_parceiros_kanban() -> list[dict[str, Any]]:
    return _copy(STORE.parceiros_kanban)


def list_leads() -> list[dict[str, Any]]:
    return _copy(STORE.leads)


def list_leads_by_parceiro(parceiro_id: int) -> list[dict[str, Any]]:
    target = int(parceiro_id)
    return [lead for lead in list_leads() if int(lead.get("id_comercial_parceiro") or 0) == target]


def list_leads_by_comercial(comercial_id: int) -> list[dict[str, Any]]:
    target = int(comercial_id)
    return [lead for lead in list_leads() if int(lead.get("id_comercial") or 0) == target]


def list_contratos_financeiro(tipo: str) -> list[dict[str, Any]]:
    if (tipo or "").strip().lower() == "saidas":
        return _copy(STORE.contratos_saidas)
    return _copy(STORE.contratos_entradas)


def get_contrato_financeiro(id_comercial_lead: int, id_solucao: int, id_comercial_parceiro: int) -> Optional[dict[str, Any]]:
    for contrato in STORE.contratos_entradas + STORE.contratos_saidas:
        if (
            int(contrato.get("id_comercial_lead") or 0) == int(id_comercial_lead)
            and int(contrato.get("id_solucao") or 0) == int(id_solucao)
            and int(contrato.get("id_comercial_parceiro") or 0) == int(id_comercial_parceiro)
        ):
            return _copy(contrato)
    return None


def save_contrato_financeiro(payload: dict[str, Any]) -> dict[str, Any]:
    target_list = STORE.contratos_entradas if str(payload.get("status") or "").lower() != "saida" else STORE.contratos_saidas
    contrato_id = int(payload.get("id_contrato") or 0)
    if contrato_id:
        for idx, item in enumerate(target_list):
            if int(item.get("id_contrato") or 0) == contrato_id:
                current = deepcopy(item)
                current.update(_copy(payload))
                target_list[idx] = current
                return {"saved": True, "id_contrato": contrato_id}
    new_id = max([c.get("id_contrato", 9000) for c in STORE.contratos_entradas + STORE.contratos_saidas] + [9000]) + 1
    novo = _copy(payload)
    novo["id_contrato"] = new_id
    target_list.append(novo)
    return {"saved": True, "id_contrato": new_id}


def update_parcela_status(payload: dict[str, Any]) -> dict[str, Any]:
    id_contrato = int(payload["id_contrato"])
    id_financeiro = int(payload["id_financeiro"])
    for contrato in STORE.contratos_entradas + STORE.contratos_saidas:
        if int(contrato.get("id_contrato") or 0) != id_contrato:
            continue
        for parcela in contrato.get("parcelas", []):
            if int(parcela.get("id_financeiro") or 0) != id_financeiro:
                continue
            parcela["status_parcela"] = 1 if int(payload.get("status_parcela") or 0) == 1 else 0
            if payload.get("referencia_esperado") is not None:
                parcela["referencia_esperado"] = payload.get("referencia_esperado")
            if payload.get("referencia_real") is not None:
                parcela["referencia_real"] = payload.get("referencia_real")
            if payload.get("valor_esperado") is not None:
                parcela["valor_esperado"] = payload.get("valor_esperado")
            if payload.get("valor_real") is not None:
                parcela["valor_real"] = payload.get("valor_real")
            return {"updated": 1}
    raise ValueError("Parcela nao encontrada")


def update_lead(payload: dict[str, Any]) -> int:
    updated = 0
    for sol in payload.get("solucoes", []):
        for lead in STORE.leads:
            if int(lead.get("id_comercial") or 0) == int(payload.get("id_comercial") or 0) and int(lead.get("id_solucao") or 0) == int(sol.get("id_solucao") or 0):
                lead["id_etapa"] = int(sol.get("id_etapa_kanban") or 1)
                lead["id_comercial_parceiro"] = sol.get("id_comercial_parceiro")
                lead["informacoes"] = _copy(sol.get("informacoes") or [])
                lead["id_colab_comercial"] = payload.get("id_colab_comercial")
                if payload.get("id_colab_comercial"):
                    nome = next((c["nome"] for c in STORE.comerciais if str(c["id_crm_colab"]) == str(payload["id_colab_comercial"]) or str(c["id_col"]) == str(payload["id_colab_comercial"])), None)
                    if nome:
                        lead["colab_comercial_nome"] = nome
                etapa_nome = next((e["nome_etapa"] for e in _default_etapas() if int(e["id"]) == int(lead["id_etapa"])), lead.get("stage"))
                lead["stage"] = etapa_nome
                updated += 1
    return updated


def delete_lead(id_comercial: int, id_solucao: int) -> int:
    before = len(STORE.leads)
    STORE.leads = [
        lead for lead in STORE.leads
        if not (int(lead.get("id_comercial") or 0) == int(id_comercial) and int(lead.get("id_solucao") or 0) == int(id_solucao))
    ]
    return before - len(STORE.leads)


def update_parceiro_kanban_status(id_comercial: int, id_solucao: int, id_status_kanban: int) -> int:
    for item in STORE.parceiros_kanban:
        if int(item.get("id_comercial") or 0) == int(id_comercial) and int(item.get("id_solucao") or 0) == int(id_solucao):
            item["id_status_kanban"] = int(id_status_kanban)
            return 1
    return 0


def update_parceiro_responsaveis(id_comercial: int, id_colab_comercial: Optional[int]) -> dict[str, Any]:
    nome_comercial = next((c["nome"] for c in STORE.comerciais if int(c["id_col"]) == int(id_colab_comercial or 0)), None)
    for item in STORE.parceiros_kanban:
        if int(item.get("id_comercial") or 0) == int(id_comercial):
            item["id_colab_comercial"] = id_colab_comercial
            if nome_comercial:
                item["colab_comercial_nome"] = nome_comercial
    return {"updated": 1}


def activate_indicacao(parceiro_id: int) -> dict[str, Any]:
    for partner in STORE.parceiros:
        if int(partner["id"]) == int(parceiro_id):
            if "indicador" not in partner["modules"]:
                partner["modules"].append("indicador")
            if not partner.get("indicadorData"):
                partner["indicadorData"] = {"leadsGenerated": 0, "leadsNegotiation": 0, "leadsClosed": 0, "conversionRate": 0}
            return {"activated": True}
    return {"activated": False}


def activate_comercial(parceiro_id: int, solution_ids: list[int]) -> dict[str, Any]:
    for partner in STORE.parceiros:
        if int(partner["id"]) != int(parceiro_id):
            continue
        if "comercial" not in partner["modules"]:
            partner["modules"].append("comercial")
        known_ids = {int(sol.get("id_solucao") or 0) for sol in partner.get("comercialSolutions", [])}
        for sid in solution_ids:
            if int(sid) in known_ids:
                continue
            sol = next((s for s in STORE.solucoes if int(s["id"]) == int(sid)), None)
            if not sol:
                continue
            partner.setdefault("comercialSolutions", []).append({
                "id_solucao": sol["id"],
                "name": sol["name"],
                "icon": sol["icon"],
                "color": "hsl(var(--primary))",
                "status": "active",
                "closedLeads": 0,
            })
        return {"activated": True}
    return {"activated": False}


def update_parceiro(parceiro_id: int, nome: str, cnpj: Optional[str], razao_social: Optional[str]) -> int:
    for partner in STORE.parceiros:
        if int(partner["id"]) == int(parceiro_id):
            partner["name"] = nome
            partner["nome"] = nome
            if cnpj is not None:
                partner["cnpj"] = cnpj
            if razao_social is not None:
                partner["razaoSocial"] = razao_social
                partner["razao_social"] = razao_social
            return 1
    return 0


def delete_parceiro(parceiro_id: int) -> int:
    before = len(STORE.parceiros)
    STORE.parceiros = [p for p in STORE.parceiros if int(p["id"]) != int(parceiro_id)]
    STORE.parceiros_kanban = [p for p in STORE.parceiros_kanban if int(p.get("id_comercial") or 0) != int(parceiro_id)]
    return before - len(STORE.parceiros)


def parceiro_has_leads(parceiro_id: int) -> bool:
    return any(int(lead.get("id_comercial_parceiro") or 0) == int(parceiro_id) for lead in STORE.leads)


def create_lead(payload: dict[str, Any], logged_user_name: str = "") -> dict[str, Any]:
    lead_type = str(payload.get("lead_type") or "lead").strip().lower()
    solution_ids = [int(sid) for sid in payload.get("solution_ids") or [] if str(sid).strip()]
    if lead_type == "parceiro" and not solution_ids:
        return {"updated": 0, "status": "parceiro_sem_solucao"}
    if lead_type != "parceiro" and not solution_ids:
        return {"updated": 0, "status": "lead_sem_solucao"}

    novo_id_comercial = max([int(lead.get("id_comercial") or 300) for lead in STORE.leads] + [300]) + 1
    nome = str(payload.get("nome") or "Empresa Demo").strip()
    razao_social = str(payload.get("razao_social") or nome).strip()
    cnpj = str(payload.get("cnpj") or "").strip()

    parceiro_id = None
    if lead_type == "parceiro":
        parceiro_id = max([int(p["id"]) for p in STORE.parceiros] + [200]) + 1
        partner = {
            "id": str(parceiro_id),
            "name": nome,
            "nome": nome,
            "razaoSocial": razao_social,
            "razao_social": razao_social,
            "cnpj": cnpj,
            "status": "active",
            "modules": ["comercial"],
            "state": "SP",
            "createdAt": "2026-03-18",
            "email": f"contato{parceiro_id}@demo.local",
            "phone": "(11) 90000-0000",
            "folPath": "",
            "comercialSolutions": [],
            "indicadorData": None,
        }
        STORE.parceiros.append(partner)
        activate_comercial(parceiro_id, solution_ids)

    id_colab_comercial = str(payload.get("id_colab_comercial") or "5001")
    colab_nome = next((c["nome"] for c in STORE.comerciais if str(c["id_col"]) == id_colab_comercial or str(c["id_crm_colab"]) == id_colab_comercial), None) or logged_user_name or "Aline Torres"
    created = 0
    for sid in solution_ids:
        if any(int(lead["id_comercial"]) == novo_id_comercial and int(lead["id_solucao"]) == sid for lead in STORE.leads):
            return {"updated": 0, "status": "lead_duplicado"}
        lead_id = f"l{len(STORE.leads) + 1}"
        STORE.leads.append({
            "id": lead_id,
            "id_comercial": novo_id_comercial,
            "id_solucao": sid,
            "id_etapa": 1,
            "stage": "Triagem",
            "name": nome,
            "company": razao_social,
            "nome_fantasia": nome,
            "razao_social": razao_social,
            "cnpj": cnpj,
            "comercial_nome": colab_nome,
            "id_colab_comercial": id_colab_comercial,
            "colab_comercial_nome": colab_nome,
            "id_comercial_parceiro": parceiro_id,
            "parceiro": nome if parceiro_id else "",
            "representante_parceiro_nome": nome if parceiro_id else "",
            "value": 0,
            "informacoes": [],
            "lastAction": "2026-03-18",
            "createdAt": "2026-03-18",
        })
        created += 1
    return {"updated": created, "status": "created", "id_comercial": novo_id_comercial}

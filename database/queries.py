# SQL queries catalog


class solucao_queries:
    # SQL | Query | Lista de Solucoes
    SQL_LIST_SOLUCOES = """
    SELECT
      tb_portfolio_solucoes.id_solucao,
      nome_solucao,
      tipo_solucao,
      descricao,
      aplicacoes_basicas_json,
      icon_id,
      color_id,
      kanban_json,
      registro_info_json,
      n_parceiros
    FROM tb_portfolio_solucoes
    LEFT JOIN (
      SELECT m2m.id_solucao, COUNT(m2m.id_comercial) AS n_parceiros
      FROM rel_portfolio_entidade_solucao m2m
      INNER JOIN tb_portfolio_entidades c
        ON c.id = m2m.id_comercial
      WHERE m2m.ativo = 1
        AND c.tipo_comercial = 'PARTNER'
      GROUP BY m2m.id_solucao
    ) sql_m2m
      ON sql_m2m.id_solucao = tb_portfolio_solucoes.id_solucao
    """

    # SQL | Query | Lista de Parceiros Ativos
    SQL_CHECK_ACTIVE_PARCEIROS = """
    SELECT 1
    FROM rel_portfolio_entidade_solucao
    WHERE id_solucao = :id_solucao
      AND ativo = 1
    """

    # SQL | Delete | Deletar Solucao
    SQL_DELETE_SOLUCAO = """
    DELETE FROM tb_portfolio_solucoes
    WHERE id_solucao = :id_solucao
    """

    # SQL | Update | Atualiza Solucao
    SQL_UPDATE_SOLUCAO = """
    UPDATE tb_portfolio_solucoes
    SET tipo_solucao = :tipo_solucao,
        descricao = :descricao,
        aplicacoes_basicas_json = :aplicacoes_basicas_json,
        icon_id = :icon_id,
        color_id = :color_id,
        kanban_json = :kanban_json,
        registro_info_json = :registro_info_json
    WHERE id_solucao = :id_solucao
    """

    SQL_UPDATE_SOLUCAO_KANBAN = """
    UPDATE tb_portfolio_solucoes
    SET kanban_json = :kanban_json
    WHERE id_solucao = :id_solucao
    """

    # SQL | Insert | Insere Solucao
    SQL_INSERT_SOLUCAO = """
    INSERT INTO tb_portfolio_solucoes (
        nome_solucao,
        tipo_solucao,
        descricao,
        aplicacoes_basicas_json,
        icon_id,
        color_id,
        kanban_json,
        registro_info_json
    )
    OUTPUT INSERTED.id_solucao
    VALUES (
        :nome_solucao,
        :tipo_solucao,
        :descricao,
        :aplicacoes_basicas_json,
        :icon_id,
        :color_id,
        :kanban_json,
        :registro_info_json
    )
    """

    # SQL | Query | Lista de Solucoes ativas
    SQL_LIST_SOLUCOES_ATIVAS = """
    SELECT
      id_solucao,
      nome_solucao,
      tipo_solucao,
      icon_id,
      color_id,
      kanban_json,
      registro_info_json
    FROM tb_portfolio_solucoes
    """

    # SQL | Query | Busca kanban_json de uma solucao
    SQL_GET_SOLUCAO_KANBAN = """
    SELECT kanban_json
    FROM tb_portfolio_solucoes
    WHERE id_solucao = :id_solucao
    """

    # SQL | Query | Busca registro_info_json de uma solucao
    SQL_GET_SOLUCAO_REGISTRO_INFO = """
    SELECT registro_info_json
    FROM tb_portfolio_solucoes
    WHERE id_solucao = :id_solucao
    """
    # SQL | Query | Lista de parceiros de uma solucao
    SQL_GET_PARCEIROS_BY_SOLUCAO = """
    SELECT
        db_c.id,
        db_c.nome
    FROM rel_portfolio_entidade_solucao m2m
    INNER JOIN tb_portfolio_entidades db_c ON db_c.id = m2m.id_comercial
    WHERE m2m.id_solucao = :id_solucao
        AND m2m.ativo = 1
        AND db_c.tipo_comercial = 'PARTNER'
    ORDER BY db_c.nome
    """

    # SQL | Query | Lista parceiros por solucao (batch)
    SQL_LIST_PARCEIROS_BY_SOLUCOES = """
    SELECT
        db_c.id,
        db_c.nome,
        db_ncs.id_solucao,
        db_ns.nome_solucao
    FROM tb_portfolio_entidades db_c
    LEFT JOIN tb_portfolio_parcerias db_np ON db_np.id_comercial = db_c.id
    INNER JOIN rel_portfolio_entidade_solucao db_ncs ON db_ncs.id_comercial = db_c.id
    LEFT JOIN tb_portfolio_solucoes db_ns ON db_ns.id_solucao = db_ncs.id_solucao
    WHERE db_c.tipo_comercial = 'PARTNER' AND db_ncs.ativo = 1
    """



class parceria_queries:

    # SQL | Query | Lista de parceiros
    SQL_LIST_PARCEIROS = """
    SELECT db_c.id, nome, cnpj, razao_social, estado, id_crm_lead, id_colab_comercial, fol_path, db_c.data_criacao, modulo_comercial, status_comercial, modulo_indicacao, status_indicacao FROM tb_portfolio_entidades db_c
      LEFT JOIN tb_portfolio_parcerias db_np ON db_np.id_comercial = db_c.id
      LEFT JOIN tb_portfolio_estados db_e ON db_e.id = id_estado
    WHERE tipo_comercial = 'PARTNER'
    """


    # SQL | Query | Lista solucoes Comercial de um parceiro
    SQL_GET_COMERCIAL_SOLUTIONS = """
    SELECT
        s.id_solucao,
        s.nome_solucao,
        s.tipo_solucao,
        s.icon_id,
        s.color_id,
        s.kanban_json
    FROM rel_portfolio_entidade_solucao m2m
    INNER JOIN tb_portfolio_solucoes s ON s.id_solucao = m2m.id_solucao
    WHERE m2m.id_comercial = :id_comercial
        AND m2m.ativo = 1
        AND s.id_solucao <> 1
    """

    # SQL | Query | Contagem de leads por solucao de um parceiro
    SQL_COUNT_LEADS_BY_PARCEIRO = """
    SELECT
        nl.id_solucao,
        nl.id_etapa_kanban,
        COUNT(*) AS total
    FROM tb_portfolio_leads nl
    WHERE nl.id_comercial_parceiro = :id_comercial
    GROUP BY nl.id_solucao, nl.id_etapa_kanban
    """


    # SQL | Upsert | Ativa modulo de indicacao na parceria
    SQL_UPSERT_MODULO_INDICACAO = """
    MERGE INTO tb_portfolio_parcerias AS target
    USING (SELECT :id_comercial AS id_comercial) AS source
        ON target.id_comercial = source.id_comercial
    WHEN MATCHED THEN
        UPDATE SET
            modulo_indicacao = 1,
            status_indicacao = 'ativo'
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, modulo_indicacao, status_indicacao)
        VALUES (source.id_comercial, 1, 'ativo');
    """

    # SQL | Upsert | Relacao comercial x solucao (Indicacao)
    SQL_UPSERT_M2M_INDICACAO = """
    MERGE INTO rel_portfolio_entidade_solucao AS target
    USING (SELECT :id_comercial AS id_comercial, :id_solucao AS id_solucao) AS source
        ON target.id_comercial = source.id_comercial
        AND target.id_solucao = source.id_solucao
    WHEN MATCHED THEN
        UPDATE SET
            ativo = 1,
            id_status_kanban = COALESCE(id_status_kanban, 1)
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, id_solucao, ativo, id_status_kanban)
        VALUES (source.id_comercial, source.id_solucao, 1, 1);
    """

    # SQL | Upsert | Ativa modulo comercial na parceria
    SQL_UPSERT_MODULO_COMERCIAL = """
    MERGE INTO tb_portfolio_parcerias AS target
    USING (SELECT :id_comercial AS id_comercial) AS source
        ON target.id_comercial = source.id_comercial
    WHEN MATCHED THEN
        UPDATE SET
            modulo_comercial = 1,
            status_comercial = 'ativo'
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, modulo_comercial, status_comercial)
        VALUES (source.id_comercial, 1, 'ativo');
    """

    # SQL | Update | Atualiza representante Comercial
    SQL_UPDATE_ID_COLAB_COMERCIAL = """
    UPDATE tb_portfolio_parcerias
    SET id_colab_comercial = :id_colab_comercial
    WHERE id_comercial = :id_comercial
    """

    SQL_UPSERT_M2M_SOLUCAO = """
    MERGE INTO rel_portfolio_entidade_solucao AS target
    USING (SELECT :id_comercial AS id_comercial, :id_solucao AS id_solucao) AS source
        ON target.id_comercial = source.id_comercial
        AND target.id_solucao = source.id_solucao
    WHEN MATCHED THEN
        UPDATE SET
            ativo = 1,
            id_status_kanban = COALESCE(id_status_kanban, 1)
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, id_solucao, ativo, id_status_kanban)
        VALUES (source.id_comercial, source.id_solucao, 1, 1);
    """

    SQL_LIST_PARCEIROS_KANBAN = """
    SELECT
        c.id AS id_comercial,
        c.nome,
        c.razao_social,
        c.cnpj,
        m2m.id_solucao,
        m2m.id_status_kanban,
        np.id_colab_comercial,
        c.id_colab_comercial
    FROM rel_portfolio_entidade_solucao m2m
    INNER JOIN tb_portfolio_entidades c ON c.id = m2m.id_comercial
    LEFT JOIN tb_portfolio_parcerias np ON np.id_comercial = c.id
    WHERE c.tipo_comercial = 'PARTNER'
      AND m2m.ativo = 1
      AND m2m.id_status_kanban IS NOT NULL
    """

    SQL_UPDATE_PARCEIRO_KANBAN_STATUS = """
    UPDATE rel_portfolio_entidade_solucao
    SET id_status_kanban = :id_status_kanban
    WHERE id_comercial = :id_comercial
      AND id_solucao = :id_solucao
    """

    SQL_UPSERT_PARCERIA_COLAB_COMERCIAL = """
    MERGE INTO tb_portfolio_parcerias AS target
    USING (SELECT :id_comercial AS id_comercial, :id_colab_comercial AS id_colab_comercial) AS source
        ON target.id_comercial = source.id_comercial
    WHEN MATCHED THEN
        UPDATE SET id_colab_comercial = source.id_colab_comercial
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, id_colab_comercial)
        VALUES (source.id_comercial, source.id_colab_comercial);
    """

    SQL_UPDATE_PARCEIRO_ID_COLAB_COMERCIAL = """
    UPDATE tb_portfolio_entidades
    SET id_colab_comercial = :id_colab_comercial
    WHERE id = :id_comercial
    """

    # SQL | Update | Atualiza dados cadastrais do parceiro
    SQL_UPDATE_PARCEIRO = """
    UPDATE tb_portfolio_entidades
    SET
        nome = :nome,
        cnpj = :cnpj,
        razao_social = :razao_social
    WHERE id = :id_comercial
      AND tipo_comercial = 'PARTNER'
    """

    # SQL | Query | Verifica se parceiro tem leads vinculados
    SQL_CHECK_PARCEIRO_HAS_LEADS = """
    SELECT 1
    FROM tb_portfolio_leads
    WHERE id_comercial_parceiro = :id_comercial
    """

    # SQL | Delete | Remove relacoes M2M do parceiro
    SQL_DELETE_PARCEIRO_M2M = """
    DELETE FROM rel_portfolio_entidade_solucao
    WHERE id_comercial = :id_comercial
    """

    # SQL | Delete | Remove dados de parceria do parceiro
    SQL_DELETE_PARCEIRO_PARCERIA = """
    DELETE FROM tb_portfolio_parcerias
    WHERE id_comercial = :id_comercial
    """

    # SQL | Delete | Remove parceiro da tabela comercial
    SQL_DELETE_PARCEIRO = """
    DELETE FROM tb_portfolio_entidades
    WHERE id = :id_comercial
      AND tipo_comercial = 'PARTNER'
    """


class contrato_financeiro_queries:
    SQL_LIST_CONTRATOS_ENTRADAS = """
    SELECT
      c.id_contrato,
      c.id_comercial_lead,
      c.id_solucao,
      c.id_comercial_parceiro,
      c.id_responsavel,
      c.status,
      c.infos_json,
      c.num_colunas,
      lead.nome AS lead_nome,
      lead.razao_social AS lead_razao_social,
      lead.cnpj AS lead_cnpj,
      NULL AS lead_email,
      NULL AS lead_telefone,
      parceiro.nome AS parceiro_nome,
      s.nome_solucao
    FROM tb_portfolio_contratos c
    LEFT JOIN tb_portfolio_entidades lead
      ON lead.id = c.id_comercial_lead
    LEFT JOIN tb_portfolio_entidades parceiro
      ON parceiro.id = c.id_comercial_parceiro
    LEFT JOIN tb_portfolio_solucoes s
      ON s.id_solucao = c.id_solucao
    WHERE c.id_solucao <> 1
    ORDER BY parceiro.nome, lead.nome, c.id_contrato DESC
    """

    SQL_LIST_CONTRATOS_SAIDAS = """
    SELECT
      c.id_contrato,
      c.id_comercial_lead,
      c.id_solucao,
      c.id_comercial_parceiro,
      c.id_responsavel,
      c.status,
      c.infos_json,
      c.num_colunas,
      lead.nome AS lead_nome,
      lead.razao_social AS lead_razao_social,
      lead.cnpj AS lead_cnpj,
      NULL AS lead_email,
      NULL AS lead_telefone,
      parceiro.nome AS parceiro_nome,
      s.nome_solucao
    FROM tb_portfolio_contratos c
    LEFT JOIN tb_portfolio_entidades lead
      ON lead.id = c.id_comercial_lead
    LEFT JOIN tb_portfolio_entidades parceiro
      ON parceiro.id = c.id_comercial_parceiro
    LEFT JOIN tb_portfolio_solucoes s
      ON s.id_solucao = c.id_solucao
    WHERE c.id_solucao = 1
    ORDER BY parceiro.nome, lead.nome, c.id_contrato DESC
    """

    SQL_SELECT_COMERCIAL_CONTRATO_BY_COMPOSITE = """
    SELECT TOP 1
      id_contrato,
      id_comercial_lead,
      id_solucao,
      id_comercial_parceiro,
      id_responsavel,
      status,
      infos_json,
      num_colunas
    FROM tb_portfolio_contratos
    WHERE id_comercial_lead = :id_comercial_lead
      AND id_solucao = :id_solucao
      AND id_comercial_parceiro = :id_comercial_parceiro
    ORDER BY id_contrato DESC
    """

    SQL_SELECT_PARCELAS_BY_CONTRATO = """
    SELECT
      id_financeiro,
      referencia_esperado,
      referencia_real,
      valor_esperado,
      valor_real,
      status_parcela
    FROM tb_portfolio_parcelas
    WHERE id_contrato = :id_contrato
    ORDER BY id_financeiro
    """

    SQL_UPDATE_STATUS_CONTRATO = """
    UPDATE tb_portfolio_contratos
    SET status = :status
    WHERE id_contrato = :id_contrato
    """

    SQL_UPDATE_COMERCIAL_CONTRATO_BY_ID = """
    UPDATE tb_portfolio_contratos
    SET
      id_comercial_lead = :id_comercial_lead,
      id_solucao = :id_solucao,
      id_comercial_parceiro = :id_comercial_parceiro,
      id_responsavel = :id_responsavel,
      status = :status,
      infos_json = :infos_json,
      num_colunas = :num_colunas
    WHERE id_contrato = :id_contrato
    """

    SQL_INSERT_COMERCIAL_CONTRATO = """
    INSERT INTO tb_portfolio_contratos (
      id_comercial_lead,
      id_solucao,
      id_comercial_parceiro,
      id_responsavel,
      status,
      infos_json,
      num_colunas
    )
    OUTPUT INSERTED.id_contrato
    VALUES (
      :id_comercial_lead,
      :id_solucao,
      :id_comercial_parceiro,
      :id_responsavel,
      :status,
      :infos_json,
      :num_colunas
    )
    """

    # SQL | Delete | Remove parcelas anteriores de um contrato
    SQL_DELETE_PARCELAS_BY_CONTRATO = """
    DELETE FROM tb_portfolio_parcelas
    WHERE id_contrato = :id_contrato
    """

    # SQL | Insert | Insere parcela do contrato
    SQL_INSERT_PARCELA = """
    INSERT INTO tb_portfolio_parcelas (
      id_contrato,
      referencia_esperado,
      referencia_real,
      valor_esperado,
      valor_real,
      status_parcela
    )
    VALUES (
      :id_contrato,
      :referencia_esperado,
      :referencia_real,
      :valor_esperado,
      :valor_real,
      :status_parcela
    )
    """

    SQL_UPDATE_STATUS_PARCELA = """
    UPDATE tb_portfolio_parcelas
    SET
      status_parcela = :status_parcela,
      referencia_real = :referencia_real,
      valor_real = :valor_real
    WHERE id_contrato = :id_contrato
      AND id_financeiro = :id_financeiro
    """

    SQL_UPDATE_PARCELA_FULL = """
    UPDATE tb_portfolio_parcelas
    SET
      status_parcela = :status_parcela,
      referencia_esperado = :referencia_esperado,
      referencia_real = :referencia_real,
      valor_esperado = :valor_esperado,
      valor_real = :valor_real
    WHERE id_contrato = :id_contrato
      AND id_financeiro = :id_financeiro
    """

    SQL_SELECT_PARCELA_BY_ID = """
    SELECT
      id_financeiro,
      id_contrato,
      referencia_esperado,
      referencia_real,
      valor_esperado,
      valor_real,
      status_parcela
    FROM tb_portfolio_parcelas
    WHERE id_contrato = :id_contrato
      AND id_financeiro = :id_financeiro
    """

class lead_queries:
    # SQL | Query | Busca lead comercial por CNPJ
    SQL_SELECT_COMERCIAL_BY_CNPJ = """
    SELECT TOP 1 id, nome, id_crm_lead, id_crm_emp, cnpj
    FROM tb_portfolio_entidades
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(COALESCE(cnpj, ''))), '.', ''), '/', ''), '-', ''), ' ', '') = :cnpj
    ORDER BY id DESC
    """

    # SQL | Query | Busca lead comercial por ID
    SQL_SELECT_COMERCIAL_BY_ID = """
    SELECT id, nome, id_crm_lead, id_crm_emp, cnpj
    FROM tb_portfolio_entidades
    WHERE id = :id_comercial
    """

    # SQL | Insert | Insere lead comercial
    SQL_INSERT_COMERCIAL = """
    INSERT INTO tb_portfolio_entidades (
        nome,
        tipo_comercial,
        cnpj,
        razao_social,
        segmento,
        id_colab_comercial,
        origem
    )
    OUTPUT INSERTED.id
    VALUES (
        :nome,
        :tipo_comercial,
        :cnpj,
        :razao_social,
        :segmento,
        :id_colab_comercial,
        :origem
    )
    """

    # SQL | Update | Atualiza lead comercial
    SQL_UPDATE_LEAD_COMERCIAL = """
    UPDATE tb_portfolio_entidades
    SET
        nome = COALESCE(:nome, nome),
        razao_social = COALESCE(:razao_social, razao_social),
        cnpj = COALESCE(:cnpj, cnpj),
        id_crm_lead = COALESCE(:id_crm_lead, id_crm_lead)
    WHERE id = :id_comercial
    """

    # SQL | Update | Atualiza identificador externo da entidade
    SQL_UPDATE_ID_CRM_EMP = """
    UPDATE tb_portfolio_entidades
    SET id_crm_emp = COALESCE(:id_crm_emp, id_crm_emp)
    WHERE id = :id_comercial
    """

    # SQL | Update | Atualiza comercial responsavel
    SQL_UPDATE_ID_COLAB_COMERCIAL = """
    UPDATE tb_portfolio_entidades
    SET id_colab_comercial = :id_colab_comercial
    WHERE id = :id_comercial
    """

    # SQL | Query | Busca etapa atual do lead por solucao
    SQL_GET_COMERCIAL_LEAD_STAGE = """
    SELECT id_etapa_kanban
    FROM tb_portfolio_leads
    WHERE id_comercial = :id_comercial
      AND id_solucao = :id_solucao
    """

    # SQL | Query | Lista leads do Comercial com fase do kanban
    SQL_LIST_COMERCIAL_LEADS = """
    SELECT
        nl.id_comercial,
        nl.id_solucao,
        nl.id_etapa_kanban,
        nl.informacoes_json,
        nl.id_colab_comercial,
        nl.id_comercial_parceiro,
        db_c.nome,
        db_c_p.nome as nome_parceiro,
        db_c.razao_social,
        db_c.cnpj,
        db_c.id_colab_comercial
    FROM tb_portfolio_leads nl
    INNER JOIN tb_portfolio_entidades db_c ON db_c.id = nl.id_comercial
    LEFT JOIN tb_portfolio_entidades db_c_p ON db_c_p.id = nl.id_comercial_parceiro
    """

    # SQL | Query | Lista leads do Comercial filtrados por parceiro
    SQL_LIST_COMERCIAL_LEADS_BY_PARCEIRO = """
    SELECT
        nl.id_comercial,
        nl.id_solucao,
        nl.id_etapa_kanban,
        nl.informacoes_json,
        nl.id_colab_comercial,
        nl.id_comercial_parceiro,
        db_c.nome,
        db_c_p.nome as nome_parceiro,
        db_c.razao_social,
        db_c.cnpj,
        db_c.id_colab_comercial
    FROM tb_portfolio_leads nl
    INNER JOIN tb_portfolio_entidades db_c ON db_c.id = nl.id_comercial
    LEFT JOIN tb_portfolio_entidades db_c_p ON db_c_p.id = nl.id_comercial_parceiro
    WHERE nl.id_comercial_parceiro = :id_comercial_parceiro
    """

    # SQL | Query | Lista leads do Comercial filtrados por id_comercial
    SQL_LIST_COMERCIAL_LEADS_BY_COMERCIAL = """
    SELECT
        nl.id_comercial,
        nl.id_solucao,
        nl.id_etapa_kanban,
        nl.informacoes_json,
        nl.id_colab_comercial,
        nl.id_comercial_parceiro,
        db_c.nome,
        db_c_p.nome as nome_parceiro,
        db_c.razao_social,
        db_c.cnpj,
        db_c.id_colab_comercial
    FROM tb_portfolio_leads nl
    INNER JOIN tb_portfolio_entidades db_c ON db_c.id = nl.id_comercial
    LEFT JOIN tb_portfolio_entidades db_c_p ON db_c_p.id = nl.id_comercial_parceiro
    WHERE nl.id_comercial = :id_comercial
    """

    # SQL | Query | Lista leads por solucao
    SQL_GET_LEADS_BY_SOLUCAO = """
    SELECT
        nl.id_comercial,
        db_c.nome,
        db_c.razao_social
    FROM tb_portfolio_leads nl
    INNER JOIN tb_portfolio_entidades db_c ON db_c.id = nl.id_comercial
    WHERE nl.id_solucao = :id_solucao
    ORDER BY db_c.nome
    """

    # SQL | Query | Lista solucoes ja vinculadas a um lead
    SQL_LIST_LEAD_SOLUCOES = """
    SELECT id_solucao
    FROM tb_portfolio_leads
    WHERE id_comercial = :id_comercial
    """

    # SQL | Insert | Vincula lead a solucoes no Comercial
    SQL_INSERT_COMERCIAL_LEAD = """
    INSERT INTO tb_portfolio_leads (id_comercial, id_solucao)
    VALUES (:id_comercial, :id_solucao)
    """

    # SQL | Insert | Vincula lead a solucoes no Comercial com fase kanban
    SQL_INSERT_COMERCIAL_LEAD_WITH_PHASE = """
    INSERT INTO tb_portfolio_leads (id_comercial, id_solucao, id_etapa_kanban, informacoes_json, id_colab_comercial, data_criacao)
    VALUES (:id_comercial, :id_solucao, :id_etapa_kanban, :informacoes_json, :id_colab_comercial, GETDATE())
    """

    # SQL | Update | Atualiza lead do Comercial (fase, parceiro, informacoes)
    SQL_UPDATE_COMERCIAL_LEAD = """
    UPDATE tb_portfolio_leads
    SET id_etapa_kanban = :id_etapa_kanban,
        id_comercial_parceiro = :id_comercial_parceiro,
        informacoes_json = :informacoes_json,
        id_colab_comercial = :id_colab_comercial
    WHERE id_comercial = :id_comercial
      AND id_solucao = :id_solucao
    """

    # SQL | Update | Atualiza parceiro vinculado no lead Comercial
    SQL_UPDATE_COMERCIAL_LEAD_PARCEIRO = """
    UPDATE tb_portfolio_leads
    SET id_comercial_parceiro = :id_comercial_parceiro
    WHERE id_comercial = :id_comercial
      AND id_solucao = :id_solucao
    """

    # SQL | Delete | Remove lead do Comercial por solucao
    SQL_DELETE_COMERCIAL_LEAD = """
    DELETE FROM tb_portfolio_leads
    WHERE id_comercial = :id_comercial
      AND id_solucao = :id_solucao
    """

    # SQL | Upsert | Relacao comercial x solucao (generico)
    SQL_UPSERT_M2M_SOLUCAO = """
    MERGE INTO rel_portfolio_entidade_solucao AS target
    USING (SELECT :id_comercial AS id_comercial, :id_solucao AS id_solucao) AS source
        ON target.id_comercial = source.id_comercial
        AND target.id_solucao = source.id_solucao
    WHEN MATCHED THEN
        UPDATE SET
            ativo = 1,
            id_status_kanban = COALESCE(id_status_kanban, 1)
    WHEN NOT MATCHED THEN
        INSERT (id_comercial, id_solucao, ativo, id_status_kanban)
        VALUES (source.id_comercial, source.id_solucao, 1, 1);
    """


class colaborador_queries:
    # SQL | Query | Busca usuario pelo identificador externo
    SQL_GET_COLABORADOR_BY_CRM_ID = """
    SELECT id_col, nome, id_crm_colab
    FROM tb_portfolio_usuarios
    WHERE id_crm_colab = :id_crm_colab
    """

    # SQL | Query | Busca colaborador pelo id_col
    SQL_GET_COLABORADOR_BY_ID_COL = """
    SELECT id_col, nome, id_crm_colab
    FROM tb_portfolio_usuarios
    WHERE id_col = :id_col
    """

    # SQL | Query | Busca colaborador pelo nome
    SQL_GET_COLABORADOR_BY_NOME = """
    SELECT TOP 1 id_col, nome, id_crm_colab
    FROM tb_portfolio_usuarios
    WHERE UPPER(LTRIM(RTRIM(nome))) = UPPER(LTRIM(RTRIM(:nome)))
    ORDER BY id_col
    """

    # SQL | Query | Lista colaboradores ativos do comercial
    SQL_LIST_COMERCIAIS_ATIVOS = """
    SELECT id_col, nome, id_crm_colab
    FROM tb_portfolio_usuarios
    WHERE status = 'Ativo' AND area = 'Comercial'
    ORDER BY nome
    """

    SQL_LIST_COMERCIAIS_EXCETO_IA = """
    SELECT id_col, nome, id_crm_colab, status
    FROM tb_portfolio_usuarios
    WHERE area = 'Comercial' AND COALESCE(status, '') <> 'IA'
    ORDER BY nome
    """

--
-- PostgreSQL database dump
--

\restrict HXRn8Z1fS4bGP8Q689A0J85TCgpNL2qQJ7npCyhiCtPcURwaOmUCZznf0SnqgJe

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: fn_audit_log(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_audit_log() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_user_id uuid;
    v_pk text;
BEGIN
    v_user_id := NULLIF(current_setting('app.user_id', true), '')::uuid;

    IF TG_OP = 'INSERT' THEN
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'I', v_pk, v_user_id, NULL, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'U', v_pk, v_user_id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_pk := to_jsonb(OLD) ->> TG_ARGV[0];
        INSERT INTO audit_log (table_name, operation, row_pk, changed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, 'D', v_pk, v_user_id, to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;


--
-- Name: fn_best_run_id(uuid, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_best_run_id(p_experiment_id uuid, p_metric_key text, p_scope text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_goal text;
    v_run_id uuid;
BEGIN
    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE key = p_metric_key;

    IF v_goal IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT rmv.run_id
    INTO v_run_id
    FROM run_metric_values rmv
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    JOIN runs r ON r.run_id = rmv.run_id
    WHERE r.experiment_id = p_experiment_id
      AND md.key = p_metric_key
      AND rmv.scope = p_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT 1;

    RETURN v_run_id;
END;
$$;


--
-- Name: fn_experiment_leaderboard(uuid, text, text, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_experiment_leaderboard(p_experiment_id uuid, p_metric_key text, p_scope text, p_limit integer) RETURNS TABLE(run_id uuid, run_name text, metric_value double precision, started_at timestamp with time zone, status text)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_goal text;
BEGIN
    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE key = p_metric_key;

    IF v_goal IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT r.run_id, r.run_name, rmv.value, r.started_at, r.status
    FROM runs r
    JOIN run_metric_values rmv ON rmv.run_id = r.run_id
    JOIN metric_definitions md ON md.metric_id = rmv.metric_id
    WHERE r.experiment_id = p_experiment_id
      AND md.key = p_metric_key
      AND rmv.scope = p_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT p_limit;
END;
$$;


--
-- Name: fn_update_project_metric_summary(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.fn_update_project_metric_summary() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_metric_id uuid;
    v_scope text;
    v_project_id uuid;
    v_goal text;
    v_best_run_id uuid;
    v_best_value double precision;
    v_sample_size integer;
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.step IS NOT NULL THEN
            RETURN OLD;
        END IF;
        v_metric_id := OLD.metric_id;
        v_scope := OLD.scope;
        SELECT e.project_id
        INTO v_project_id
        FROM runs r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE r.run_id = OLD.run_id;
    ELSE
        IF NEW.step IS NOT NULL THEN
            RETURN NEW;
        END IF;
        v_metric_id := NEW.metric_id;
        v_scope := NEW.scope;
        SELECT e.project_id
        INTO v_project_id
        FROM runs r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE r.run_id = NEW.run_id;
    END IF;

    IF v_project_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT goal
    INTO v_goal
    FROM metric_definitions
    WHERE metric_id = v_metric_id;

    IF v_goal IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*)
    INTO v_sample_size
    FROM run_metric_values rmv
    JOIN runs r ON r.run_id = rmv.run_id
    JOIN experiments e ON e.experiment_id = r.experiment_id
    WHERE e.project_id = v_project_id
      AND rmv.metric_id = v_metric_id
      AND rmv.scope = v_scope
      AND rmv.step IS NULL;

    IF v_sample_size = 0 THEN
        DELETE FROM project_metric_summary
        WHERE project_id = v_project_id
          AND metric_id = v_metric_id
          AND scope = v_scope;
        RETURN NULL;
    END IF;

    SELECT rmv.run_id, rmv.value
    INTO v_best_run_id, v_best_value
    FROM run_metric_values rmv
    JOIN runs r ON r.run_id = rmv.run_id
    JOIN experiments e ON e.experiment_id = r.experiment_id
    WHERE e.project_id = v_project_id
      AND rmv.metric_id = v_metric_id
      AND rmv.scope = v_scope
      AND rmv.step IS NULL
    ORDER BY
      CASE WHEN v_goal = 'min' THEN rmv.value END ASC,
      CASE WHEN v_goal = 'max' THEN rmv.value END DESC,
      CASE WHEN v_goal = 'last' THEN rmv.recorded_at END DESC
    LIMIT 1;

    INSERT INTO project_metric_summary (
        project_id,
        metric_id,
        scope,
        best_value,
        best_run_id,
        updated_at,
        sample_size
    ) VALUES (
        v_project_id,
        v_metric_id,
        v_scope,
        v_best_value,
        v_best_run_id,
        now(),
        v_sample_size
    )
    ON CONFLICT (project_id, metric_id, scope) DO UPDATE SET
        best_value = EXCLUDED.best_value,
        best_run_id = EXCLUDED.best_run_id,
        updated_at = EXCLUDED.updated_at,
        sample_size = EXCLUDED.sample_size;

    RETURN NULL;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifacts (
    artifact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    artifact_type text NOT NULL,
    uri text NOT NULL,
    checksum text,
    size_bytes bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_artifacts_size CHECK (((size_bytes IS NULL) OR (size_bytes >= 0))),
    CONSTRAINT ck_artifacts_type CHECK ((artifact_type = ANY (ARRAY['model'::text, 'plot'::text, 'log'::text, 'report'::text, 'dataset-sample'::text, 'other'::text])))
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    audit_id bigint NOT NULL,
    table_name text NOT NULL,
    operation text NOT NULL,
    row_pk text NOT NULL,
    changed_by uuid,
    changed_at timestamp with time zone DEFAULT now() NOT NULL,
    old_data jsonb,
    new_data jsonb,
    CONSTRAINT ck_audit_operation CHECK ((operation = ANY (ARRAY['I'::text, 'U'::text, 'D'::text])))
);


--
-- Name: audit_log_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_audit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_audit_id_seq OWNED BY public.audit_log.audit_id;


--
-- Name: batch_import_errors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.batch_import_errors (
    error_id bigint NOT NULL,
    job_id uuid NOT NULL,
    row_number integer,
    raw_row jsonb,
    error_message text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: batch_import_errors_error_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.batch_import_errors_error_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: batch_import_errors_error_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.batch_import_errors_error_id_seq OWNED BY public.batch_import_errors.error_id;


--
-- Name: batch_import_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.batch_import_jobs (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_type text NOT NULL,
    status text NOT NULL,
    source_format text NOT NULL,
    source_uri text NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    created_by uuid,
    stats_json jsonb,
    CONSTRAINT ck_jobs_format CHECK ((source_format = ANY (ARRAY['csv'::text, 'json'::text]))),
    CONSTRAINT ck_jobs_status CHECK ((status = ANY (ARRAY['created'::text, 'running'::text, 'finished'::text, 'failed'::text]))),
    CONSTRAINT ck_jobs_type CHECK ((job_type = ANY (ARRAY['users'::text, 'datasets'::text, 'runs'::text, 'metrics'::text, 'artifacts'::text])))
);


--
-- Name: dataset_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_versions (
    dataset_version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    dataset_id uuid NOT NULL,
    version_label text NOT NULL,
    storage_uri text NOT NULL,
    content_hash text NOT NULL,
    row_count bigint,
    size_bytes bigint,
    schema_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_dv_row CHECK (((row_count IS NULL) OR (row_count >= 0))),
    CONSTRAINT ck_dv_size CHECK (((size_bytes IS NULL) OR (size_bytes >= 0)))
);


--
-- Name: datasets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.datasets (
    dataset_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    name text NOT NULL,
    task_type text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_datasets_task_type CHECK ((task_type = ANY (ARRAY['classification'::text, 'regression'::text, 'ranking'::text, 'segmentation'::text, 'nlp'::text, 'other'::text])))
);


--
-- Name: experiments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.experiments (
    experiment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    name text NOT NULL,
    objective text,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: metric_definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metric_definitions (
    metric_id uuid DEFAULT gen_random_uuid() NOT NULL,
    key text NOT NULL,
    display_name text NOT NULL,
    unit text,
    goal text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_metric_goal CHECK ((goal = ANY (ARRAY['min'::text, 'max'::text, 'last'::text])))
);


--
-- Name: ml_projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ml_projects (
    project_id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    name text NOT NULL,
    description text,
    status text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_projects_status CHECK ((status = ANY (ARRAY['active'::text, 'archived'::text])))
);


--
-- Name: org_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_members (
    org_member_id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role text NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_org_members_role CHECK ((role = ANY (ARRAY['owner'::text, 'admin'::text, 'member'::text, 'viewer'::text])))
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    org_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid NOT NULL
);


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_members (
    project_member_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role text NOT NULL,
    added_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_members_role CHECK ((role = ANY (ARRAY['admin'::text, 'editor'::text, 'viewer'::text])))
);


--
-- Name: project_metric_summary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_metric_summary (
    project_id uuid NOT NULL,
    metric_id uuid NOT NULL,
    scope text NOT NULL,
    best_value double precision,
    best_run_id uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    sample_size integer,
    CONSTRAINT ck_pms_scope CHECK ((scope = ANY (ARRAY['train'::text, 'val'::text, 'test'::text])))
);


--
-- Name: run_artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.run_artifacts (
    run_artifact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    run_id uuid NOT NULL,
    artifact_id uuid NOT NULL,
    alias text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: run_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.run_configs (
    run_id uuid NOT NULL,
    params_json jsonb NOT NULL,
    env_json jsonb,
    command_line text,
    seed integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: run_metric_values; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.run_metric_values (
    run_metric_value_id uuid DEFAULT gen_random_uuid() NOT NULL,
    run_id uuid NOT NULL,
    metric_id uuid NOT NULL,
    scope text NOT NULL,
    step integer,
    value double precision NOT NULL,
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_rmv_scope CHECK ((scope = ANY (ARRAY['train'::text, 'val'::text, 'test'::text]))),
    CONSTRAINT ck_rmv_step CHECK (((step IS NULL) OR (step >= 0)))
);


--
-- Name: runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.runs (
    run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    experiment_id uuid NOT NULL,
    dataset_version_id uuid NOT NULL,
    run_name text,
    status text NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    created_by uuid,
    git_commit text,
    notes text,
    CONSTRAINT ck_runs_status CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'finished'::text, 'failed'::text, 'killed'::text])))
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text NOT NULL,
    full_name text NOT NULL,
    password_hash text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: v_best_runs_per_experiment; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_best_runs_per_experiment AS
 SELECT experiment_id,
    run_id,
    run_name,
    metric_value,
    started_at,
    status
   FROM ( SELECT r.experiment_id,
            r.run_id,
            r.run_name,
            rmv.value AS metric_value,
            r.started_at,
            r.status,
            row_number() OVER (PARTITION BY r.experiment_id ORDER BY
                CASE
                    WHEN (md.goal = 'min'::text) THEN rmv.value
                    ELSE NULL::double precision
                END,
                CASE
                    WHEN (md.goal = 'max'::text) THEN rmv.value
                    ELSE NULL::double precision
                END DESC,
                CASE
                    WHEN (md.goal = 'last'::text) THEN rmv.recorded_at
                    ELSE NULL::timestamp with time zone
                END DESC) AS rn
           FROM ((public.runs r
             JOIN public.run_metric_values rmv ON (((rmv.run_id = r.run_id) AND (rmv.step IS NULL))))
             JOIN public.metric_definitions md ON ((md.metric_id = rmv.metric_id)))
          WHERE (md.key = 'accuracy'::text)) ranked
  WHERE (rn = 1);


--
-- Name: v_project_quality_dashboard; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_project_quality_dashboard AS
 SELECT p.project_id,
    p.name AS project_name,
    count(DISTINCT e.experiment_id) AS experiments_count,
    count(DISTINCT r.run_id) AS runs_count,
    COALESCE(round(((100.0 * (sum(
        CASE
            WHEN (r.status = 'finished'::text) THEN 1
            ELSE 0
        END))::numeric) / (NULLIF(count(r.run_id), 0))::numeric), 2), (0)::numeric) AS success_rate_pct,
    percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY ((EXTRACT(epoch FROM (r.finished_at - r.started_at)))::double precision)) FILTER (WHERE ((r.finished_at IS NOT NULL) AND (r.started_at IS NOT NULL))) AS median_train_seconds,
    pms.best_value AS best_metric_value,
    pms.best_run_id
   FROM ((((public.ml_projects p
     LEFT JOIN public.experiments e ON ((e.project_id = p.project_id)))
     LEFT JOIN public.runs r ON ((r.experiment_id = e.experiment_id)))
     LEFT JOIN public.metric_definitions md ON ((md.key = 'accuracy'::text)))
     LEFT JOIN public.project_metric_summary pms ON (((pms.project_id = p.project_id) AND (pms.metric_id = md.metric_id) AND (pms.scope = 'val'::text))))
  GROUP BY p.project_id, p.name, pms.best_value, pms.best_run_id;


--
-- Name: v_runs_with_final_metrics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_runs_with_final_metrics AS
 SELECT r.run_id,
    r.experiment_id,
    r.dataset_version_id,
    r.run_name,
    r.status,
    r.started_at,
    r.finished_at,
    r.created_by,
    r.git_commit,
    r.notes,
    jsonb_object_agg(md.key, rmv.value) FILTER (WHERE (rmv.step IS NULL)) AS final_metrics
   FROM ((public.runs r
     LEFT JOIN public.run_metric_values rmv ON (((rmv.run_id = r.run_id) AND (rmv.step IS NULL))))
     LEFT JOIN public.metric_definitions md ON ((md.metric_id = rmv.metric_id)))
  GROUP BY r.run_id, r.experiment_id, r.dataset_version_id, r.run_name, r.status, r.started_at, r.finished_at, r.created_by, r.git_commit, r.notes;


--
-- Name: audit_log audit_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN audit_id SET DEFAULT nextval('public.audit_log_audit_id_seq'::regclass);


--
-- Name: batch_import_errors error_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_import_errors ALTER COLUMN error_id SET DEFAULT nextval('public.batch_import_errors_error_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: artifacts artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_pkey PRIMARY KEY (artifact_id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (audit_id);


--
-- Name: batch_import_errors batch_import_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_import_errors
    ADD CONSTRAINT batch_import_errors_pkey PRIMARY KEY (error_id);


--
-- Name: batch_import_jobs batch_import_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_import_jobs
    ADD CONSTRAINT batch_import_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: dataset_versions dataset_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_versions
    ADD CONSTRAINT dataset_versions_pkey PRIMARY KEY (dataset_version_id);


--
-- Name: datasets datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_pkey PRIMARY KEY (dataset_id);


--
-- Name: experiments experiments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiments
    ADD CONSTRAINT experiments_pkey PRIMARY KEY (experiment_id);


--
-- Name: metric_definitions metric_definitions_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric_definitions
    ADD CONSTRAINT metric_definitions_key_key UNIQUE (key);


--
-- Name: metric_definitions metric_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric_definitions
    ADD CONSTRAINT metric_definitions_pkey PRIMARY KEY (metric_id);


--
-- Name: ml_projects ml_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_projects
    ADD CONSTRAINT ml_projects_pkey PRIMARY KEY (project_id);


--
-- Name: org_members org_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_pkey PRIMARY KEY (org_member_id);


--
-- Name: organizations organizations_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_name_key UNIQUE (name);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (org_id);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (project_member_id);


--
-- Name: project_metric_summary project_metric_summary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_metric_summary
    ADD CONSTRAINT project_metric_summary_pkey PRIMARY KEY (project_id, metric_id, scope);


--
-- Name: run_artifacts run_artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_artifacts
    ADD CONSTRAINT run_artifacts_pkey PRIMARY KEY (run_artifact_id);


--
-- Name: run_configs run_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_configs
    ADD CONSTRAINT run_configs_pkey PRIMARY KEY (run_id);


--
-- Name: run_metric_values run_metric_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_metric_values
    ADD CONSTRAINT run_metric_values_pkey PRIMARY KEY (run_metric_value_id);


--
-- Name: runs runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_pkey PRIMARY KEY (run_id);


--
-- Name: datasets uq_datasets_project_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT uq_datasets_project_name UNIQUE (project_id, name);


--
-- Name: dataset_versions uq_dv_dataset_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_versions
    ADD CONSTRAINT uq_dv_dataset_hash UNIQUE (dataset_id, content_hash);


--
-- Name: dataset_versions uq_dv_dataset_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_versions
    ADD CONSTRAINT uq_dv_dataset_version UNIQUE (dataset_id, version_label);


--
-- Name: experiments uq_experiments_project_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiments
    ADD CONSTRAINT uq_experiments_project_name UNIQUE (project_id, name);


--
-- Name: org_members uq_org_members_org_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT uq_org_members_org_user UNIQUE (org_id, user_id);


--
-- Name: project_members uq_project_members_project_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT uq_project_members_project_user UNIQUE (project_id, user_id);


--
-- Name: ml_projects uq_projects_org_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_projects
    ADD CONSTRAINT uq_projects_org_name UNIQUE (org_id, name);


--
-- Name: run_artifacts uq_run_artifacts_alias; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_artifacts
    ADD CONSTRAINT uq_run_artifacts_alias UNIQUE (run_id, alias);


--
-- Name: run_artifacts uq_run_artifacts_run_artifact; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_artifacts
    ADD CONSTRAINT uq_run_artifacts_run_artifact UNIQUE (run_id, artifact_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_artifacts_project_type_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_project_type_created ON public.artifacts USING btree (project_id, artifact_type, created_at);


--
-- Name: ix_dataset_versions_content_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dataset_versions_content_hash ON public.dataset_versions USING btree (content_hash);


--
-- Name: ix_dataset_versions_dataset_label; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dataset_versions_dataset_label ON public.dataset_versions USING btree (dataset_id, version_label);


--
-- Name: ix_experiments_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_experiments_project_id ON public.experiments USING btree (project_id);


--
-- Name: ix_rmv_final_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rmv_final_metric ON public.run_metric_values USING btree (metric_id, scope, value) WHERE (step IS NULL);


--
-- Name: ix_rmv_run_metric_scope_step; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rmv_run_metric_scope_step ON public.run_metric_values USING btree (run_id, metric_id, scope, step);


--
-- Name: ix_run_artifacts_artifact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_run_artifacts_artifact_id ON public.run_artifacts USING btree (artifact_id);


--
-- Name: ix_run_artifacts_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_run_artifacts_run_id ON public.run_artifacts USING btree (run_id);


--
-- Name: ix_runs_dataset_version_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_runs_dataset_version_id ON public.runs USING btree (dataset_version_id);


--
-- Name: ix_runs_experiment_status_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_runs_experiment_status_started ON public.runs USING btree (experiment_id, status, started_at);


--
-- Name: artifacts trg_audit_artifacts; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_artifacts AFTER INSERT OR DELETE OR UPDATE ON public.artifacts FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('artifact_id');


--
-- Name: dataset_versions trg_audit_dataset_versions; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_dataset_versions AFTER INSERT OR DELETE OR UPDATE ON public.dataset_versions FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('dataset_version_id');


--
-- Name: datasets trg_audit_datasets; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_datasets AFTER INSERT OR DELETE OR UPDATE ON public.datasets FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('dataset_id');


--
-- Name: experiments trg_audit_experiments; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_experiments AFTER INSERT OR DELETE OR UPDATE ON public.experiments FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('experiment_id');


--
-- Name: metric_definitions trg_audit_metric_definitions; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_metric_definitions AFTER INSERT OR DELETE OR UPDATE ON public.metric_definitions FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('metric_id');


--
-- Name: ml_projects trg_audit_ml_projects; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_ml_projects AFTER INSERT OR DELETE OR UPDATE ON public.ml_projects FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('project_id');


--
-- Name: run_configs trg_audit_run_configs; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_run_configs AFTER INSERT OR DELETE OR UPDATE ON public.run_configs FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('run_id');


--
-- Name: runs trg_audit_runs; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_runs AFTER INSERT OR DELETE OR UPDATE ON public.runs FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('run_id');


--
-- Name: users trg_audit_users; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_users AFTER INSERT OR DELETE OR UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log('user_id');


--
-- Name: run_metric_values trg_project_metric_summary; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_project_metric_summary AFTER INSERT OR DELETE OR UPDATE ON public.run_metric_values FOR EACH ROW EXECUTE FUNCTION public.fn_update_project_metric_summary();


--
-- Name: artifacts artifacts_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.ml_projects(project_id) ON DELETE CASCADE;


--
-- Name: batch_import_errors batch_import_errors_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_import_errors
    ADD CONSTRAINT batch_import_errors_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.batch_import_jobs(job_id) ON DELETE CASCADE;


--
-- Name: batch_import_jobs batch_import_jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_import_jobs
    ADD CONSTRAINT batch_import_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- Name: dataset_versions dataset_versions_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_versions
    ADD CONSTRAINT dataset_versions_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(dataset_id) ON DELETE CASCADE;


--
-- Name: datasets datasets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.ml_projects(project_id) ON DELETE CASCADE;


--
-- Name: experiments experiments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiments
    ADD CONSTRAINT experiments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id) ON UPDATE CASCADE;


--
-- Name: experiments experiments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.experiments
    ADD CONSTRAINT experiments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.ml_projects(project_id) ON DELETE CASCADE;


--
-- Name: ml_projects ml_projects_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ml_projects
    ADD CONSTRAINT ml_projects_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(org_id) ON DELETE CASCADE;


--
-- Name: org_members org_members_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(org_id) ON DELETE CASCADE;


--
-- Name: org_members org_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: organizations organizations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id) ON UPDATE CASCADE;


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.ml_projects(project_id) ON DELETE CASCADE;


--
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: project_metric_summary project_metric_summary_best_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_metric_summary
    ADD CONSTRAINT project_metric_summary_best_run_id_fkey FOREIGN KEY (best_run_id) REFERENCES public.runs(run_id) ON DELETE SET NULL;


--
-- Name: project_metric_summary project_metric_summary_metric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_metric_summary
    ADD CONSTRAINT project_metric_summary_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.metric_definitions(metric_id) ON DELETE CASCADE;


--
-- Name: project_metric_summary project_metric_summary_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_metric_summary
    ADD CONSTRAINT project_metric_summary_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.ml_projects(project_id) ON DELETE CASCADE;


--
-- Name: run_artifacts run_artifacts_artifact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_artifacts
    ADD CONSTRAINT run_artifacts_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES public.artifacts(artifact_id) ON DELETE CASCADE;


--
-- Name: run_artifacts run_artifacts_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_artifacts
    ADD CONSTRAINT run_artifacts_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.runs(run_id) ON DELETE CASCADE;


--
-- Name: run_configs run_configs_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_configs
    ADD CONSTRAINT run_configs_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.runs(run_id) ON DELETE CASCADE;


--
-- Name: run_metric_values run_metric_values_metric_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_metric_values
    ADD CONSTRAINT run_metric_values_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES public.metric_definitions(metric_id) ON DELETE CASCADE;


--
-- Name: run_metric_values run_metric_values_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.run_metric_values
    ADD CONSTRAINT run_metric_values_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.runs(run_id) ON DELETE CASCADE;


--
-- Name: runs runs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- Name: runs runs_dataset_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_dataset_version_id_fkey FOREIGN KEY (dataset_version_id) REFERENCES public.dataset_versions(dataset_version_id) ON UPDATE CASCADE;


--
-- Name: runs runs_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_experiment_id_fkey FOREIGN KEY (experiment_id) REFERENCES public.experiments(experiment_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict HXRn8Z1fS4bGP8Q689A0J85TCgpNL2qQJ7npCyhiCtPcURwaOmUCZznf0SnqgJe


--
-- PostgreSQL database dump
--

-- Dumped from database version 12.0
-- Dumped by pg_dump version 12.0

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
-- Name: catalogs_update_stat(); Type: FUNCTION; Schema: public; Owner: blog
--

CREATE FUNCTION public.catalogs_update_stat() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    update cache_flag set time_flag = current_timestamp where cache_name = 'catalog';
    return new;
end;$$;


ALTER FUNCTION public.catalogs_update_stat() OWNER TO blog;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: author_operation; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.author_operation (
    author_id integer NOT NULL,
    operate character varying(32) NOT NULL,
    remote_ip character varying(18) NOT NULL,
    operate_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    info text,
    data bytea
);


ALTER TABLE public.author_operation OWNER TO blog;

--
-- Name: authors; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.authors (
    id integer NOT NULL,
    email character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    hashed_password character varying(100) NOT NULL,
    activate_key character varying(32) DEFAULT 'KEY'::character varying NOT NULL,
    activate_state boolean DEFAULT false,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    settings text DEFAULT '{"default-editor": "kind-editor"}'::text NOT NULL,
    quota integer DEFAULT 50 NOT NULL,
    portrait text,
    description text,
    ident character(32)
);


ALTER TABLE public.authors OWNER TO blog;

--
-- Name: authors_id_seq; Type: SEQUENCE; Schema: public; Owner: blog
--

CREATE SEQUENCE public.authors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.authors_id_seq OWNER TO blog;

--
-- Name: authors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: blog
--

ALTER SEQUENCE public.authors_id_seq OWNED BY public.authors.id;


--
-- Name: cache_flag; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.cache_flag (
    cache_name character varying(32) NOT NULL,
    time_flag timestamp without time zone NOT NULL,
    int_flag integer NOT NULL,
    author_id integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.cache_flag OWNER TO blog;

--
-- Name: catalogs; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.catalogs (
    cat_id integer NOT NULL,
    cat_name character varying(64) NOT NULL,
    author_id integer NOT NULL,
    parent_id integer NOT NULL,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.catalogs OWNER TO blog;

--
-- Name: entries; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.entries (
    id integer NOT NULL,
    author_id integer NOT NULL,
    slug character varying(100) NOT NULL,
    title character varying(512) NOT NULL,
    markdown text NOT NULL,
    html text NOT NULL,
    published timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    is_public boolean DEFAULT true NOT NULL,
    is_encrypt boolean DEFAULT false NOT NULL,
    search_tags character varying(256),
    cat_id integer DEFAULT 12 NOT NULL,
    editor character varying(32) DEFAULT 'kind-editor'::character varying NOT NULL,
    size integer DEFAULT 280 NOT NULL,
    attach_size integer DEFAULT 0 NOT NULL,
    state integer DEFAULT 1 NOT NULL,
    attach_cnt integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.entries OWNER TO blog;

--
-- Name: entries_id_seq; Type: SEQUENCE; Schema: public; Owner: blog
--

CREATE SEQUENCE public.entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.entries_id_seq OWNER TO blog;

--
-- Name: entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: blog
--

ALTER SEQUENCE public.entries_id_seq OWNED BY public.entries.id;


--
-- Name: entries_statistic; Type: TABLE; Schema: public; Owner: blog
--

CREATE TABLE public.entries_statistic (
    author_id integer NOT NULL,
    cat_id integer NOT NULL,
    parent_id integer NOT NULL,
    entries_cnt integer DEFAULT 0
);


ALTER TABLE public.entries_statistic OWNER TO blog;

--
-- Name: authors id; Type: DEFAULT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.authors ALTER COLUMN id SET DEFAULT nextval('public.authors_id_seq'::regclass);


--
-- Name: entries id; Type: DEFAULT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries ALTER COLUMN id SET DEFAULT nextval('public.entries_id_seq'::regclass);


--
-- Name: authors authors_email_key; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT authors_email_key UNIQUE (email);


--
-- Name: authors authors_pkey; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT authors_pkey PRIMARY KEY (id);


--
-- Name: cache_flag cache_flag_pkey; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.cache_flag
    ADD CONSTRAINT cache_flag_pkey PRIMARY KEY (author_id, cache_name);


--
-- Name: catalogs catalogs_pkey; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.catalogs
    ADD CONSTRAINT catalogs_pkey PRIMARY KEY (author_id, cat_id);


--
-- Name: entries entries_pkey; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries
    ADD CONSTRAINT entries_pkey PRIMARY KEY (id);


--
-- Name: entries entries_slug_key; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries
    ADD CONSTRAINT entries_slug_key UNIQUE (slug);


--
-- Name: entries_statistic entries_statistic_pk; Type: CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries_statistic
    ADD CONSTRAINT entries_statistic_pk PRIMARY KEY (author_id, cat_id);


--
-- Name: author_operation_idx; Type: INDEX; Schema: public; Owner: blog
--

CREATE INDEX author_operation_idx ON public.author_operation USING btree (author_id, operate_date);


--
-- Name: catalogs_parent_idx; Type: INDEX; Schema: public; Owner: blog
--

CREATE INDEX catalogs_parent_idx ON public.catalogs USING btree (author_id, parent_id);


--
-- Name: entries_author_id_idx; Type: INDEX; Schema: public; Owner: blog
--

CREATE INDEX entries_author_id_idx ON public.entries USING btree (author_id, cat_id);


--
-- Name: entries_slug_idx; Type: INDEX; Schema: public; Owner: blog
--

CREATE INDEX entries_slug_idx ON public.entries USING btree (slug);


--
-- Name: catalogs catalogs_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.catalogs
    ADD CONSTRAINT catalogs_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id);


--
-- Name: entries entries_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries
    ADD CONSTRAINT entries_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id);


--
-- Name: entries_statistic entries_statistic_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: blog
--

ALTER TABLE ONLY public.entries_statistic
    ADD CONSTRAINT entries_statistic_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id);


--
-- PostgreSQL database dump complete
--


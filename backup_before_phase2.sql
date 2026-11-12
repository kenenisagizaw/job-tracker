--
-- PostgreSQL database dump
--

\restrict sqcTBynLxgiVqa535XnWVToIbsir6atbNv1zblv9U0dW7m6yiHK9qNGo7Fnpqcj

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: kegy
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO kegy;

--
-- Name: application_activities; Type: TABLE; Schema: public; Owner: kegy
--

CREATE TABLE public.application_activities (
    id integer NOT NULL,
    job_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.application_activities OWNER TO kegy;

--
-- Name: application_activities_id_seq; Type: SEQUENCE; Schema: public; Owner: kegy
--

CREATE SEQUENCE public.application_activities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.application_activities_id_seq OWNER TO kegy;

--
-- Name: application_activities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kegy
--

ALTER SEQUENCE public.application_activities_id_seq OWNED BY public.application_activities.id;


--
-- Name: companies; Type: TABLE; Schema: public; Owner: kegy
--

CREATE TABLE public.companies (
    id integer NOT NULL,
    name character varying(150) NOT NULL,
    owner_id integer NOT NULL
);


ALTER TABLE public.companies OWNER TO kegy;

--
-- Name: companies_id_seq; Type: SEQUENCE; Schema: public; Owner: kegy
--

CREATE SEQUENCE public.companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.companies_id_seq OWNER TO kegy;

--
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kegy
--

ALTER SEQUENCE public.companies_id_seq OWNED BY public.companies.id;


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: kegy
--

CREATE TABLE public.jobs (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    location character varying(100) NOT NULL,
    salary double precision,
    job_type character varying(50) DEFAULT 'Full-time'::character varying NOT NULL,
    description text,
    status character varying(30) DEFAULT 'saved'::character varying NOT NULL,
    company_id integer NOT NULL,
    owner_id integer NOT NULL,
    deadline date,
    deadline_reminder_sent_for date,
    CONSTRAINT check_job_status CHECK (((status)::text = ANY ((ARRAY['saved'::character varying, 'applied'::character varying, 'interview'::character varying, 'offer'::character varying, 'rejected'::character varying])::text[]))),
    CONSTRAINT check_salary_positive CHECK (((salary IS NULL) OR (salary > (0)::double precision)))
);


ALTER TABLE public.jobs OWNER TO kegy;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: kegy
--

CREATE SEQUENCE public.jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.jobs_id_seq OWNER TO kegy;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kegy
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: kegy
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


ALTER TABLE public.users OWNER TO kegy;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: kegy
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO kegy;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kegy
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: application_activities id; Type: DEFAULT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.application_activities ALTER COLUMN id SET DEFAULT nextval('public.application_activities_id_seq'::regclass);


--
-- Name: companies id; Type: DEFAULT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.companies ALTER COLUMN id SET DEFAULT nextval('public.companies_id_seq'::regclass);


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.jobs ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: kegy
--

COPY public.alembic_version (version_num) FROM stdin;
20261111_activities
\.


--
-- Data for Name: application_activities; Type: TABLE DATA; Schema: public; Owner: kegy
--

COPY public.application_activities (id, job_id, event_type, description, created_at) FROM stdin;
1	10	status_changed	Status changed from 'interview' to 'offer'.	2026-11-10 23:14:57.735844+00
2	11	job_created	Job 'IT Officer' was added to the pipeline.	2026-11-10 23:16:55.073911+00
3	10	status_changed	Status changed from 'offer' to 'applied'.	2026-11-10 23:47:32.092008+00
4	10	status_changed	Status changed from 'applied' to 'interview'.	2026-11-11 18:46:36.122777+00
5	10	status_changed	Status changed from 'interview' to 'applied'.	2026-11-11 18:46:42.37381+00
6	10	status_changed	Status changed from 'applied' to 'interview'.	2026-11-11 22:49:51.290463+00
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: kegy
--

COPY public.companies (id, name, owner_id) FROM stdin;
1	Ethio Telecom	1
2	Safaricom Ethiopia	2
11	Safaricom Ethiopia	6
3	Dashen Bank	1
4	Commercial Bank of Ethiopia	1
5	Ethiopian Airlines	1
12	Ethiopian Airlines	4
6	Awash Bank	2
7	INSA	2
8	CBE	1
10	ODA	1
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: kegy
--

COPY public.jobs (id, title, location, salary, job_type, description, status, company_id, owner_id, deadline, deadline_reminder_sent_for) FROM stdin;
3	Marketing	AA	25000	Full-time	Urgent	saved	5	1	\N	\N
5	Sales	Addis Ababa	30000	Full-time	We accept urgent	saved	2	2	\N	\N
8	IT Technician	Addis Ababa	23000	Part-time	Good	applied	6	2	\N	\N
9	CyberSecurity	Addis Ababa	44986	Full-time	Urgent	saved	7	2	2026-11-08	\N
6	Backend	Addis Ababa	40000	Full-time	Onsite	saved	12	4	\N	\N
7	Marketing	AA	25000	Full-time	Urgent	saved	12	4	\N	\N
11	IT Officer	Addis Ababa	31989	Full-time	On the way	saved	11	6	2026-11-25	\N
10	AI Engineer	Addis Ababa	80000	Full-time	priority given	interview	11	6	2026-11-08	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: kegy
--

COPY public.users (id, email, hashed_password, is_active) FROM stdin;
1	Evaluater@example.com	$argon2id$v=19$m=65536,t=3,p=4$zPxNayKTdt3mP+hRl4URUA$OJtsf5jNTyheAeKpvx+iCljvZICthQl7xcKJWy+FlL0	t
2	evaluar@example.com	$argon2id$v=19$m=65536,t=3,p=4$b0SZ/99eUQCvzPvPLhaLyg$fuPAVDYJgQ+Dzn0SgG+EfNYVypIVKUGdeqbJfxQDegE	t
3	mulatu@example.com	$argon2id$v=19$m=65536,t=3,p=4$mHNSugpYuYGg3smeOqirRA$c1SFP7LQpJWU2B3W4LUq8VGwg4zZIeD7StQd2AJBcbk	t
4	abdela@gmail.com	$argon2id$v=19$m=65536,t=3,p=4$dImPKKGz7cj5mHlQ3DgtBA$Towm1BV7xTn+Lc50YeSHPo1jQYNig39pKC7y//HhE10	t
5	company-test-1794082144@example.com	$argon2id$v=19$m=65536,t=3,p=4$8zSVzcDqPlVh5cbVf9tYfg$OXrQ9p3ZoI3vgJNDBna3+sTspLEbz529kOgEACG7odw	t
6	kenenisagizaw.28@gmail.com	$argon2id$v=19$m=65536,t=3,p=4$1CxbE+nDzPYotrdibdjN7Q$NNaGIOgbXY6z5HbFcjzBbao7mXge7O8Oyc6VO2cmx/8	t
\.


--
-- Name: application_activities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kegy
--

SELECT pg_catalog.setval('public.application_activities_id_seq', 6, true);


--
-- Name: companies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kegy
--

SELECT pg_catalog.setval('public.companies_id_seq', 12, true);


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kegy
--

SELECT pg_catalog.setval('public.jobs_id_seq', 11, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: kegy
--

SELECT pg_catalog.setval('public.users_id_seq', 6, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: application_activities application_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.application_activities
    ADD CONSTRAINT application_activities_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: companies uq_companies_owner_name; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT uq_companies_owner_name UNIQUE (owner_id, name);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_application_activities_job_id; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_application_activities_job_id ON public.application_activities USING btree (job_id);


--
-- Name: ix_companies_owner_id; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_companies_owner_id ON public.companies USING btree (owner_id);


--
-- Name: ix_jobs_company_id; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_jobs_company_id ON public.jobs USING btree (company_id);


--
-- Name: ix_jobs_id; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_jobs_id ON public.jobs USING btree (id);


--
-- Name: ix_jobs_owner_id; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_jobs_owner_id ON public.jobs USING btree (owner_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: kegy
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: application_activities fk_application_activities_job_id; Type: FK CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.application_activities
    ADD CONSTRAINT fk_application_activities_job_id FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;


--
-- Name: companies fk_companies_owner_id_users; Type: FK CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT fk_companies_owner_id_users FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- Name: jobs fk_jobs_company_id_companies; Type: FK CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT fk_jobs_company_id_companies FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: jobs fk_jobs_owner_id_users; Type: FK CONSTRAINT; Schema: public; Owner: kegy
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT fk_jobs_owner_id_users FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict sqcTBynLxgiVqa535XnWVToIbsir6atbNv1zblv9U0dW7m6yiHK9qNGo7Fnpqcj


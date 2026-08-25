-- backend/sql/02_study_records.sql

create table if not exists public.study_records (
    record_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(user_id),
    subject varchar(100) not null,
    content varchar(2000),
    study_minutes integer not null
        check (study_minutes between 1 and 1440),
    studied_on date not null,
    proof_image_path text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
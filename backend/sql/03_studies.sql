-- backend/sql/03_studies.sql
create table if not exists public.studies (
    study_id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references public.users(user_id),
    title varchar(100) not null,
    category varchar(100) not null,
    goal text not null,
    schedule varchar(200) not null,
    capacity integer not null
        check (capacity between 2 and 20),
    status varchar(20) not null default 'recruiting'
        check (status in ('recruiting', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

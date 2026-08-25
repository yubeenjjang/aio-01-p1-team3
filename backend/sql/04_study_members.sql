-- backend/sql/04_study_members.sql

create table if not exists public.study_members (
    study_member_id uuid primary key default gen_random_uuid(),
    study_id uuid not null references public.studies(study_id),
    user_id uuid not null references public.users(user_id),
    joined_at timestamptz not null default now(),

    unique (study_id, user_id)
);
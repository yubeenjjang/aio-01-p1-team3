create extension if not exists pgcrypto;

create table if not exists public.users (
    user_id uuid primary key default gen_random_uuid(),
    email varchar(255) not null unique,
    password_hash varchar(255) not null,
    name varchar(50) not null,
    role varchar(20) not null default 'user'
        check (role in ('user', 'admin')),
    created_at timestamptz not null default now()
);

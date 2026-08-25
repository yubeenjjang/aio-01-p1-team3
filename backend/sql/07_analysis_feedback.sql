create table if not exists public.analysis_feedback (
    feedback_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(user_id),
    period_start date not null,
    period_end date not null,
    rating smallint not null check (rating between 1 and 5),
    comment varchar(1000),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, period_start, period_end),
    check (period_start <= period_end)
);

create index if not exists idx_analysis_feedback_created
    on public.analysis_feedback(created_at desc);
create index if not exists idx_analysis_feedback_rating
    on public.analysis_feedback(rating);

create table if not exists public.operation_logs (
    log_id bigint generated always as identity primary key,
    created_at timestamptz not null default now(),
    user_id uuid references public.users(user_id),
    action varchar(100) not null,
    status varchar(20) not null
        check (status in ('success', 'failure')),
    message text,
    latency_ms integer check (latency_ms is null or latency_ms >= 0),
    trace_id uuid not null
);

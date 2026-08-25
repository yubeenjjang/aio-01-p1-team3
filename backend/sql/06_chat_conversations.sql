create table if not exists public.chat_conversations (
    conversation_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(user_id),
    title varchar(100) not null default '새 학습 코치 대화',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
    message_id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.chat_conversations(conversation_id) on delete cascade,
    role varchar(10) not null check (role in ('user', 'model')),
    content text not null,
    created_at timestamptz not null default now(),
    input_tokens integer check (input_tokens is null or input_tokens >= 0),
    output_tokens integer check (output_tokens is null or output_tokens >= 0)
);

create index if not exists idx_chat_conversations_user_updated
    on public.chat_conversations(user_id, updated_at desc);
create index if not exists idx_chat_messages_conversation_created
    on public.chat_messages(conversation_id, created_at, message_id);

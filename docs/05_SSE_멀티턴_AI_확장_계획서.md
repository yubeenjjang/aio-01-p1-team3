# SSE 및 멀티턴 AI 확장 계획서

> **구현 동기화 기준(2026-08-11):** 1~4번 MVP 계획 이후 구현된 확장 기능과 팀 최종 합의를 반영합니다. 충돌하는 초기 초안보다 이 문서의 최종 결정이 우선합니다.

## 1. 목적과 범위

이 문서는 MVP 이후 구현된 실시간 운영 로그, 멀티턴 학습 코치, AI 분석 사용자 평가, 그룹 스터디 운영 보완과 사용자 사이드바 동선 개선을 현재 코드 기준으로 정리한 확장 계획서입니다.

1. Redis Pub/Sub 기반 관리자 운영 로그 SSE(Server-Sent Events)
2. AI 분석 페이지에 통합하는 Supabase 기반 Gemini 멀티턴 학습 코치
3. AI 분석 결과에 대한 사용자 평가 저장 및 관리자 조회
4. 그룹 스터디 삭제 API와 목록·상세 120초 자동 갱신
5. 사용자 정보 영역에서 마이페이지로 이동할 수 있도록 사이드바 배치 개선

기존 MVP의 기록·스터디·분석 API와 DB는 유지하고, 관리자 SSE·멀티턴 대화·분석 평가 API·테이블과 스터디 삭제 계약을 추가합니다.

## 2. 참고 구현

| 기능 | 참고 경로 | 적용할 핵심 |
| --- | --- | --- |
| SSE | `C:\mini_frontend\realtime_data_simple\backend\app\routers\real_router.py` | Redis Pub/Sub을 구독하고 `StreamingResponse`로 `text/event-stream` 응답 반환 |
| 멀티턴 Gemini | `C:\aidevs\02_supabase-ai-backend\02_llm-api-integration\04_multi-turn-call\03_gemini_sdk_multi_turn.py` | 이전 user/model 메시지를 Gemini `contents` 목록에 함께 전달 |

## 3. 확장 원칙

- SSE는 관리자 대시보드·운영 로그·분석 평가 화면의 서버 → 클라이언트 단방향 갱신에 사용합니다. 클라이언트 → 서버 요청은 기존 HTTP API를 사용합니다.
- 사용자 기록·스터디·AI 분석 화면은 SSE 대상에서 제외하고, 기존 조회 API와 수동 새로고침을 사용합니다.
- 실시간 알림이 실패해도 기록·스터디·대화의 DB 저장 성공 결과를 실패로 바꾸지 않습니다.
- 멀티턴 대화는 사용자별·대화방별로 분리합니다.
- Gemini에는 최근 메시지만 전달해 토큰 사용량과 응답 시간을 제한합니다.
- API 키, 비밀번호 원문, 전체 민감 데이터는 로그와 SSE 이벤트에 포함하지 않습니다.
- 현재 MVP의 `user_id` 연결 방식은 유지하되, 서버 세션 인증 도입 후에는 인증된 사용자 정보로 교체합니다.
- 그룹 스터디는 소유자만 삭제할 수 있고, 삭제 전 참여자 행을 정리합니다.

세부 설계서는 다음 문서를 참조합니다.

- [05-1 데이터베이스 설계서 (확장)](./05-1_데이터베이스_설계서_확장.md)
- [05-2 API 명세서 (확장)](./05-2_API_명세서_확장.md)
- [05-3 화면 설계서 (확장)](./05-3_화면_설계서_확장.md)

## 4. 1단계: SSE 실시간 알림

### 4.1 제공 기능

학습 기록, 스터디, AI 분석, AI 분석 평가 등 운영 로그가 생성되거나 갱신될 때 관리자 대시보드·운영 로그·분석 평가 화면이 공유하는 수신 큐에 최신 로그 갱신 이벤트를 보냅니다.

사용자 화면에는 SSE 이벤트를 보내지 않습니다. 활성 관리자 화면이 이벤트를 받으면 현재 필터를 유지한 채 관련 조회 API를 다시 호출합니다. 이벤트에 전체 데이터나 민감한 학습 내용은 넣지 않습니다.

### 4.2 구현 API 계약

```http
GET /events/stream?admin_user_id={uuid}
Accept: text/event-stream
```

성공 시 예시:

```text
event: admin.log.updated
data: {"event_id":"uuid","action":"analysis.feedback.submit","status":"success","occurred_at":"2026-08-10T12:00:00Z"}

```

이벤트 종류:

| event | 발생 시점 | 화면 동작 |
| --- | --- | --- |
| `admin.log.updated` | 주요 API 성공·실패 로그 생성 | 활성 관리자 화면의 관련 데이터 다시 조회 |
| `error` | Redis 구독 연결 오류 | 백그라운드 리스너 재연결, 세부 상태 표시는 후속 보완 |

### 4.3 구현 파일

| 구분 | 파일 | 역할 |
| --- | --- | --- |
| 추가 | `backend/app/core/redis_config.py` | `REDIS_URL`을 읽고 Redis async client 생성·종료 |
| 추가 | `backend/app/services/event_service.py` | 이벤트 JSON 생성, 관리자 채널 publish·subscribe |
| 추가 | `backend/app/routers/events_router.py` | `/events/stream` SSE endpoint와 keep-alive 처리 |
| 수정 | `backend/app/main.py` | events router 등록, Redis 연결 종료 처리 |
| 수정 | `backend/app/core/log_utils.py` | 관리자 로그 SSE 대상 이벤트 발행을 공통 처리 |
| 수정 | `backend/app/routers/analyses_router.py` | 분석 완료·실패 후 `admin.log.updated` 발행 |
| 수정 | `backend/app/routers/feedback_router.py` | 평가 저장 후 `admin.log.updated` 발행 |
| 수정 | `backend/requirements.txt` | `redis` 패키지 추가 |
| 추가 | `backend/tests/test_events_router.py` | SSE 헤더·이벤트 형식·구독 오류 테스트 |

### 4.4 Redis 채널 규칙

```text
study-management:admin
```

- 운영 로그 이벤트는 관리자 채널에만 발행합니다.
- 관리자 SSE 연결 시 `admin_user_id`의 role이 `admin`인지 확인합니다.
- 사용자별 개인 채널과 스터디 참여자 채널은 이번 확장 범위에서 만들지 않습니다.

### 4.5 SSE 구현 규칙

- 응답 타입: `StreamingResponse(..., media_type="text/event-stream")`
- 응답 헤더: `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- 이벤트 한 건 형식: `event: <name>\ndata: <JSON>\n\n`
- 15~30초마다 keep-alive 주석 이벤트를 보내 프록시 연결 종료를 줄입니다.
- 브라우저 재연결 시 이벤트를 다시 받으며, 유실된 로그는 기존 관리자 로그 조회 API로 복구합니다.
- Redis 장애는 스트림에 `error` 이벤트를 보내고 운영 로그에는 실패를 기록합니다.

## 5. 2단계: 멀티턴 AI 학습 코치

### 5.1 제공 기능

AI 분석 페이지에서 분석 기간을 선택하면 기간별 분석과 일반 학습 코치 채팅을 같은 화면에서 사용할 수 있습니다. 사용자가 학습 관련 질문을 보내면 같은 대화방의 이전 질문·답변을 참고해 Gemini가 답변합니다. 기존 `POST /analyses`의 기간별 단일 분석은 그대로 유지합니다.

분석 결과 아래에는 해당 분석에 대한 사용자 평가 영역을 제공합니다. 사용자는 1~5점 평점과 선택 의견을 남길 수 있고, 관리자 화면에서는 평가 목록·평균 평점·의견을 조회할 수 있습니다.

### 5.2 구현 DB 설계

새 SQL 파일: `backend/sql/06_chat_conversations.sql`

`chat_conversations`

| 컬럼 | 설명 |
| --- | --- |
| `conversation_id` UUID PK | 대화방 식별자 |
| `user_id` UUID FK | 대화 소유자 |
| `title` VARCHAR(100) | 첫 질문 기반 제목 또는 기본 제목 |
| `created_at`, `updated_at` TIMESTAMPTZ | 생성·수정 시각 |

`chat_messages`

| 컬럼 | 설명 |
| --- | --- |
| `message_id` UUID PK | 메시지 식별자 |
| `conversation_id` UUID FK | 소속 대화방 |
| `role` VARCHAR(10) | `user` 또는 `model` |
| `content` TEXT | 질문 또는 답변 |
| `created_at` TIMESTAMPTZ | 메시지 시각 |
| `input_tokens`, `output_tokens` INTEGER NULL | 제공 가능할 때만 저장하는 사용량 지표 |

대화방 삭제 시 메시지는 함께 삭제합니다. `user_id, updated_at`과 `conversation_id, created_at` 인덱스를 추가합니다.

`analysis_feedback`

| 컬럼 | 설명 |
| --- | --- |
| `feedback_id` UUID PK | 평가 식별자 |
| `user_id` UUID FK | 평가 작성 사용자 |
| `period_start`, `period_end` DATE | 평가 대상 분석 기간 |
| `rating` SMALLINT | 1~5점 평점 |
| `comment` VARCHAR(1000) NULL | 선택 사용자 의견 |
| `created_at`, `updated_at` TIMESTAMPTZ | 평가 생성·수정 시각 |

사용자와 분석 기간 조합은 하나의 평가만 가지도록 `UNIQUE(user_id, period_start, period_end)` 제약을 둡니다. 관리자 조회를 위해 `created_at`, `rating` 인덱스를 추가합니다.

### 5.3 구현 API 계약

| API | 설명 | 주요 응답 |
| --- | --- | --- |
| `POST /chat/conversations` | 빈 대화방 생성 | `conversation_id`, `title` |
| `GET /chat/conversations?user_id=` | 사용자 대화방 목록 | `items`, `total` |
| `GET /chat/conversations/{conversation_id}/messages?user_id=` | 메시지 이력 조회 | `items`, `total` |
| `POST /chat/conversations/{conversation_id}/messages` | 질문 저장·Gemini 응답 생성 | user/model 메시지 2건 |
| `DELETE /chat/conversations/{conversation_id}?user_id=` | 대화방과 메시지 삭제 | `204` |
| `POST /analyses/feedback` | 분석 결과 평가 생성·수정 | `feedback_id`, `rating`, `comment` |
| `GET /admin/analysis-feedback` | 관리자용 분석 평가 목록·통계 조회 | `items`, `total`, `average_rating` |

메시지 요청 예시:

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "FastAPI의 Depends를 쉽게 설명해줘."
}
```

평가 요청 예시:

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "period_start": "2026-08-01",
  "period_end": "2026-08-31",
  "rating": 5,
  "comment": "다음 목표를 정하는 데 도움이 되었습니다."
}
```

### 5.4 Gemini 호출 규칙

1. 대화방의 소유자와 요청 `user_id`가 같은지 확인합니다.
2. 현재 질문을 `chat_messages`에 `role=user`로 저장합니다.
3. 최근 20개의 메시지를 시간순으로 읽습니다.
4. Gemini 입력 `contents`로 변환합니다.
   - 사용자 메시지: `role="user"`
   - Gemini 답변: `role="model"`
5. 학습 코치용 시스템 지침과 최근 이력을 함께 Gemini에 전달합니다.
6. 응답을 `role=model`로 저장하고 API에 반환합니다.
7. 성공·실패 모두 `operation_logs`에 `chat.message` action을 기록합니다.

Gemini 호출 실패 규칙은 기존 분석 API와 통일합니다.

| 상황 | HTTP 상태 | code |
| --- | --- | --- |
| 대화방 없음 또는 타인 대화방 | 404 | `CONVERSATION_NOT_FOUND` |
| Gemini 할당량 초과 | 429 | `RATE_LIMITED` |
| Gemini 서비스 장애 | 503 | `GEMINI_UNAVAILABLE` |
| 기타 Gemini 실패 | 500 | `GEMINI_REQUEST_FAILED` |

### 5.5 구현 파일

| 구분 | 파일 | 역할 |
| --- | --- | --- |
| 추가 | `backend/app/schemas/chat_schema.py` | 대화방·메시지 요청/응답 Pydantic 모델 |
| 추가 | `backend/app/services/chat_service.py` | 대화 DB CRUD, 이력 제한, Gemini contents 변환 |
| 추가 | `backend/app/routers/chat_router.py` | 대화방·메시지 API |
| 추가 | `backend/app/schemas/feedback_schema.py` | 분석 평가 요청·응답·관리자 조회 모델 |
| 추가 | `backend/app/services/feedback_service.py` | 평가 생성·수정·관리자 통계 조회 |
| 추가 | `backend/app/routers/feedback_router.py` | 사용자 평가 API 및 관리자 평가 조회 API |
| 수정 | `backend/app/core/gemini_config.py` | 기존 단일 프롬프트 함수와 별도로 `contents` 기반 호출 함수 제공 |
| 수정 | `backend/app/main.py` | chat·feedback·events router 등록 |
| 추가 | `backend/tests/test_chat_router.py` | 대화 생성·이력 순서·최근 이력 제한·Gemini 오류·타인 접근 테스트 |
| 추가 | `backend/tests/test_feedback_router.py` | 평가 생성·수정·중복 평가·관리자 조회·타인 접근 테스트 |
| 추가 | `backend/sql/06_chat_conversations.sql` | 대화방·메시지 테이블과 인덱스 생성 |
| 추가 | `backend/sql/07_analysis_feedback.sql` | 분석 평가 테이블·제약조건·인덱스 생성 |

## 6. 3단계: 채팅 답변 스트리밍(선택)

멀티턴 일반 응답이 안정화된 뒤에만 추가합니다.

```http
POST /chat/conversations/{conversation_id}/messages/stream
Content-Type: application/json
Accept: text/event-stream
```

- `message` 이벤트: 생성 중인 답변 조각
- `done` 이벤트: 최종 message ID와 완료 상태
- `error` 이벤트: 표준 오류 코드
- 클라이언트는 `fetch`/`httpx.stream`으로 POST 스트림을 읽습니다. 기본 `EventSource`는 GET 요청만 지원하므로 이 API에는 사용하지 않습니다.
- 연결이 중간에 끊기면 완성되지 않은 모델 답변을 저장하지 않습니다.

## 7. 프론트엔드 세부 계획

### 7.1 담당 범위

| 영역 | 사용자 프론트엔드 | 관리자 프론트엔드 |
| --- | --- | --- |
| SSE 연결 | 연결하지 않음 | 대시보드·운영 로그·분석 평가가 하나의 이벤트 리스너와 큐 공유 |
| 화면 갱신 | 그룹 목록·상세 120초 자동 갱신과 수동 새로고침 | fragment가 5초마다 큐를 확인하고 관련 이벤트가 있을 때 조회 API 재호출 |
| 멀티턴 채팅 | AI 분석 페이지 내 일반 채팅 | 기본 범위에서는 구현하지 않음 |
| 분석 평가 | 분석 결과 아래 평점·의견 입력 | 평가 목록·평균 평점·의견 조회 |
| 사이드바 | 주요 기능 메뉴와 사용자 영역 분리, 사용자 정보 아래 마이페이지 버튼 배치 | 해당 없음 |
| 오류·연결 상태 | API 오류·빈 상태 표시 | SSE 재연결·API 오류 표시 |

### 7.2 사용자 프론트엔드 구현 파일

| 구분 | 파일 | 역할 |
| --- | --- | --- |
| 추가 | `frontend_user/clients/chat_client.py` | 대화방 생성·목록·메시지 조회·질문 전송·삭제 API 호출 |
| 추가 | `frontend_user/clients/feedback_client.py` | 분석 평가 생성·수정 API 호출 |
| 수정 | `frontend_user/app.py` | 주요 메뉴에서 마이페이지 링크를 분리하고 사용자 이름·역할 아래, 로그아웃 위에 이동 버튼 배치 |
| 수정 | `frontend_user/app_pages/09_analysis.py` | 분석 기간 아래 두 탭으로 분석·일반 채팅 표시, 분석 결과 아래 평가 입력 |

### 7.3 관리자 프론트엔드 구현 파일

| 구분 | 파일 | 역할 |
| --- | --- | --- |
| 추가 | `frontend_admin/clients/event_client.py` | 관리자 SSE 연결·이벤트 파싱 |
| 수정 | `frontend_admin/clients/admin_client.py` | 이벤트 수신 뒤 대시보드·로그·평가 재조회 함수 연결 |
| 수정 | `frontend_admin/app_pages/01_dashboard.py` | 관련 이벤트 수신 시 대시보드 데이터 다시 조회 |
| 수정 | `frontend_admin/app_pages/02_logs.py` | 이벤트 수신 시 현재 필터를 유지한 채 운영 로그 다시 조회 |
| 추가 | `frontend_admin/app_pages/03_analysis_feedback.py` | 분석 평가 목록·평균 평점·의견 조회 |

관리자 SSE는 개인 사용자 화면에 전달되지 않으며, `study-management:admin` 채널을 통해 운영 로그 갱신 이벤트만 전달합니다. 관리자 대시보드·로그·평가 화면은 이 이벤트를 재조회 신호로 사용합니다.

### 7.4 관리자 화면의 SSE 처리 규칙

| 수신 이벤트 | 영향을 받는 화면 | 화면 동작 |
| --- | --- | --- |
| `admin.log.updated` | 관리자 대시보드·운영 로그·분석 평가 | 현재 필터 조건을 유지하고 관련 API 재호출 |
| `error` | 관리자 SSE 사용 화면 | 백그라운드 리스너가 재연결하고 수동 새로고침 유지 |

SSE 이벤트에는 화면에 바로 표시할 전체 데이터를 넣지 않습니다. 이벤트를 받으면 기존 HTTP 조회 API를 다시 호출해 최신 상태를 표시합니다.

### 7.5 SSE 연결 상태 UI와 후속 보완

현재 대시보드·운영 로그는 단순 연결 안내를 표시하고, 평가 화면은 리스너 스레드 생존 여부로 연결·재연결 문구를 구분합니다. 아래의 실제 연결 단계 세분화는 후속 보완 범위입니다.

| 상태 | 표시 예시 | 동작 |
| --- | --- | --- |
| 연결됨 | `실시간 연결됨` | 이벤트 수신 후 해당 데이터 재조회 |
| 연결 중 | `실시간 연결 중...` | 중복 연결을 만들지 않음 |
| 재연결 중 | `연결이 끊어져 다시 연결합니다.` | 지수 백오프로 재시도 |
| 연결 실패 | `실시간 갱신을 사용할 수 없습니다.` | 기존 수동 새로고침·폴링은 계속 제공 |

Streamlit 화면은 브라우저 JavaScript의 `EventSource`처럼 백그라운드 SSE 수신 스레드가 직접 화면을 갱신할 수 없습니다. 1차 구현에서는 관리자 각 화면의 fragment가 5초마다 SSE Queue만 확인하고, 관련 이벤트가 있을 때만 해당 화면의 운영 로그·대시보드·평가 조회 API를 다시 호출합니다. 이벤트가 없을 때는 캐시된 화면 데이터를 사용하므로 DB/API 주기적 폴링은 하지 않습니다.

### 7.6 AI 분석·일반 채팅 통합 화면

`frontend_user/app_pages/09_analysis.py`는 분석 기간 선택 영역 아래에 분석과 일반 채팅을 합의된 두 탭으로 배치합니다.

1. AI 분석 탭은 기존 기간별 AI 분석 요청·결과·오류·재시도를 담당합니다.
2. 분석 결과 아래에 1~5점 평가와 선택 의견 입력을 표시합니다.
3. 평가가 이미 있으면 기존 평가를 표시하고 수정할 수 있게 합니다.
4. AI 코치 탭은 대화방 목록, `새 대화`·`삭제`, 메시지 이력을 표시합니다.
5. `user` 메시지와 `model` 메시지를 시각적으로 구분해 표시합니다.
6. 사용자가 질문을 보내면 전송 버튼을 비활성화하고 로딩 상태를 표시합니다.
7. 응답 성공 후 메시지 목록을 다시 조회하거나 반환받은 user/model 메시지를 즉시 화면에 추가합니다.
8. `429`, `503`, `500`은 각각 호출 한도·서비스 장애·일반 오류로 안내하고 재시도 버튼을 제공합니다.
9. 분석 결과·평가·대화방·메시지가 없을 때의 빈 상태 화면을 제공합니다.

일반 응답 API 구현이 먼저입니다. 3단계의 답변 스트리밍을 선택한 경우에만 `httpx.stream`으로 `message` 이벤트를 읽어 Streamlit placeholder에 답변 조각을 누적 표시합니다.

### 7.7 프론트엔드 테스트·수동 확인

| 확인 항목 | 방법 |
| --- | --- |
| 관리자 SSE 연결 | 관리자 대시보드·운영 로그·평가 화면에서 공용 리스너와 재조회 동작 확인 |
| SSE 범위 | 일반 사용자 화면에는 SSE 연결이 생성되지 않는지 확인 |
| 연결 실패 | Redis 연결을 끈 환경에서 관리자 오류 안내와 수동 새로고침이 유지되는지 확인 |
| 대화방 | 분석 화면 AI 코치 탭에서 생성·선택·삭제 후 상태 확인 |
| 멀티턴 | 첫 질문과 답변 뒤 두 번째 질문이 이전 문맥을 참조하는지 확인 |
| 분석 평가 | 평점·의견 저장, 수정, 새로고침 후 표시 확인 |
| 마이페이지 동선 | 로그인 후 사이드바 사용자 정보 아래의 마이페이지 버튼 표시·이동과 로그아웃 버튼 순서 확인 |
| 관리자 평가 | 관리자 평가 목록·평균 평점·의견 표시 확인 |
| Gemini 오류 | 429·503·500 메시지와 재시도 동작 확인 |

## 8. 구현 순서

1. Redis 연결 검사와 `redis` 의존성 추가
2. `event_service`와 `/events/stream`을 먼저 구현·테스트
3. 운영 로그 공통 이벤트 발행과 관리자 `/events/stream` 연결
4. 대화방·메시지 SQL을 Supabase에 적용
5. chat schema/service/router 및 일반 응답 API 구현
6. 분석 평가 SQL·schema/service/router 및 관리자 조회 API 구현
7. Gemini 최근 이력 제한·429/503 처리·운영 로그 추가
8. AI 분석 페이지 두 탭 레이아웃과 평가 입력 연결
9. 관리자 대시보드·운영 로그·평가 화면에 공용 SSE 큐 연결
10. 필요 시 채팅 답변 토큰 스트리밍 구현
11. 자동 테스트·Swagger·수동 시나리오 확인

## 9. 완료 기준과 테스트

### SSE

- `GET /events/stream`이 `text/event-stream`과 no-cache 헤더를 반환한다.
- Redis publish 후 `event`와 JSON `data`가 SSE 형식으로 전달된다.
- 주요 운영 로그 생성 뒤 관리자 채널에서 `admin.log.updated` 이벤트를 받는다.
- Redis 장애 시 데이터 저장 API는 성공 상태를 유지하고 스트림에는 오류 이벤트가 전달된다.
- 일반 사용자 화면에는 SSE 연결이 없고 관리자 대시보드·운영 로그·분석 평가 화면만 공용 SSE 리스너를 사용한다.

### 멀티턴

- 대화방과 메시지가 사용자별로 분리되어 저장된다.
- 두 번째 질문에서 첫 질문과 첫 답변이 Gemini `contents`에 포함된다.
- 최근 메시지 제한을 넘어도 정해진 개수만 전송한다.
- Gemini `model` 역할과 사용자 `user` 역할이 순서대로 변환된다.
- 404·429·503·500 오류와 `chat.message` 운영 로그를 확인한다.

### 분석 평가

- 분석 결과 아래에서 1~5점 평가와 선택 의견을 저장·수정할 수 있다.
- 동일 사용자·동일 분석 기간의 중복 평가가 새 행으로 생성되지 않는다.
- 관리자 평가 화면에서 목록·평균 평점·의견을 확인할 수 있다.
- 평가 등록·수정 성공과 실패가 운영 로그에 기록되고 관리자 SSE로 갱신된다.

## 10. 구현에 반영된 최종 결정

1. Redis 연결은 배포 환경의 `REDIS_URL` 환경변수로 주입합니다.
2. Gemini에 전달하는 최근 대화 이력은 최대 20개 메시지입니다.
3. 사용자는 자신의 대화방을 삭제할 수 있고 메시지는 FK cascade로 함께 삭제합니다.
4. 분석 평가는 사용자·분석 기간당 1개로 제한하며 같은 조합은 upsert로 수정합니다.
5. 평가 의견은 최대 1,000자입니다.
6. 채팅 답변 토큰 스트리밍은 현재 구현에서 제외합니다.
7. AI 분석과 일반 학습 코치는 한 화면의 두 탭으로 제공합니다.
8. 그룹 스터디 목록·상세 자동 갱신 주기는 120초입니다.
9. 관리자 대시보드·운영 로그·분석 평가는 하나의 SSE 수신 리스너와 큐를 공유하며, 각 화면 fragment가 5초마다 큐를 확인해 관련 이벤트가 있을 때만 조회 API를 다시 호출합니다.
10. 스터디 소유자는 `DELETE /studies/{study_id}`로 스터디를 삭제할 수 있으며 `study.delete` 운영 로그를 남깁니다.
11. 사용자 사이드바의 주요 메뉴는 메인·개인 스터디·그룹 스터디·AI 분석으로 구성하고, 마이페이지는 사용자 이름·역할 아래와 로그아웃 위에 별도 버튼으로 배치합니다.

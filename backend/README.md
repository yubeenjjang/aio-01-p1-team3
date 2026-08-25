# Backend

스터디 관리 서비스의 FastAPI 백엔드입니다. Supabase에는 서비스 역할 키로 연결하고, 학습 분석·코치에는 Gemini API를 사용하며 관리자 실시간 갱신에는 Redis Pub/Sub과 SSE를 사용합니다.

## 사전 준비

- Python 3.12
- Supabase 프로젝트 및 SQL 테이블 생성
- Supabase Storage의 `proof-images` 버킷 생성
- Gemini API 키
- Redis 인스턴스

## 환경변수 설정

`backend` 폴더에서 `.env.example`을 복사해 `.env` 파일을 만들고 값을 설정합니다.

```powershell
Copy-Item .env.example .env
```

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
GEMINI_API_KEY=<gemini-api-key>
REDIS_URL=redis://<host>:<port>
```

`.env`와 서비스 역할 키는 Git에 커밋하지 않습니다.

## 데이터베이스와 Storage 준비

Supabase SQL Editor에서 아래 파일을 순서대로 실행합니다.

1. `sql/01_users.sql`
2. `sql/02_study_records.sql`
3. `sql/03_studies.sql`
4. `sql/04_study_members.sql`
5. `sql/05_operation_logs.sql`
6. `sql/06_chat_conversations.sql`
7. `sql/07_analysis_feedback.sql`

이후 Supabase Storage에서 이름이 정확히 `proof-images`인 버킷을 만듭니다. 학습 인증 사진 업로드 API가 이 버킷을 사용합니다.

## 실행

기존 가상환경이 정상이라면 활성화한 뒤 실행합니다.

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

처음 설치하거나 패키지가 없다면 다음을 실행합니다.

```powershell
pip install -r requirements.txt
```

실행 후 다음 주소에서 확인합니다.

- Swagger: <http://127.0.0.1:8000/docs>
- 상태 확인: <http://127.0.0.1:8000/health>

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

테스트는 실제 Supabase·Gemini 키를 사용하지 않고, 서비스 호출을 mock 처리해 API 요청·응답 규칙을 확인합니다.

2026-08-11 전체 회귀 테스트 결과는 `63 passed, 1 warning`입니다. 경고는 Starlette TestClient의 httpx 호환성 deprecation 경고이며 테스트 실패는 아닙니다.

## 주요 API

- `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`
- `GET/POST /records`, `GET/PUT/DELETE /records/{record_id}`, `GET /records/stats`
- `POST /uploads/proof-image`
- `GET/POST /studies`, `GET/PUT/DELETE /studies/{study_id}`, `POST/DELETE /studies/{study_id}/join`
- `POST /analyses`
- `GET/POST /analyses/feedback`
- `GET/POST /chat/conversations`, `GET/POST /chat/conversations/{conversation_id}/messages`, `DELETE /chat/conversations/{conversation_id}`
- `GET /events/stream`
- `GET /admin/dashboard`, `GET /admin/logs`, `GET /admin/analysis-feedback`

## 참고 사항

- 회원가입 비밀번호는 8자 이상이어야 합니다.
- Gemini의 무료 할당량이 초과되면 분석 API는 `429 RATE_LIMITED`를 반환할 수 있습니다.
- 현재 MVP는 서버 세션 테이블이나 JWT를 사용하지 않으며, 요청의 `user_id`로 데이터를 연결합니다.
- Supabase client는 프로세스에서 재사용하며, 그룹 스터디 목록은 관련 데이터를 일괄 조회해 조합합니다.
- 관리자 대시보드·로그·평가 화면은 하나의 SSE 수신 큐를 공유합니다. 화면은 5초마다 큐만 확인하고 이벤트가 있을 때 관련 조회 API를 다시 호출합니다.
- 사용자 그룹 스터디 목록의 합의된 자동 갱신 주기는 120초입니다.
- 상세 API 계약은 `../docs/03_API_명세서_MVP.md`와 `../docs/05-2_API_명세서_확장.md`를 기준으로 합니다.

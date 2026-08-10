# 4단계｜개발 계획서 (MVP)

## 1. 목적과 구현 기준

이 계획서는 `docs/01_문제와_사용_시나리오_정의.md`, `docs/02_통합_아키텍처_설계.md`, MVP API·DB·화면 설계서를 구현 단위로 나눈 문서입니다.

데이터베이스 필드·제약조건의 정확한 정의는 `03_데이터베이스_설계서_MVP.md`, URL·요청·응답·오류 계약은 `03_API_명세서_MVP.md`, 화면 구성·상태·와이어프레임은 `03_화면_설계서_MVP.md`를 최종 기준으로 합니다. 이 문서는 그 상세 설계를 중복 정의하지 않고, 담당 파일과 구현 순서를 정합니다.

참고 저장소 `mini_frontend_upload`의 쉬운 구조를 따릅니다.

- FastAPI는 `router → service → Supabase` 순서로 구현합니다.
- Streamlit은 `app.py → app_pages → clients → core` 순서로 호출을 분리합니다.
- ORM, JWT, Redis, WebSocket, 복잡한 의존성 주입은 MVP에 넣지 않습니다.
- 사용자와 관리자는 별도 Streamlit 앱으로 실행하고 같은 FastAPI를 호출합니다.
- 공개 회원가입은 항상 `user` 역할로 생성합니다. 관리자 계정은 Supabase 초기 데이터 또는 운영 절차로 생성합니다.

## 2. 폴더·파일 구조

```text
aio-01-p1-team3/
├─ .gitignore
├─ README.md                       # 프로젝트 개요·실행 순서·문서 링크
├─ team_workspace/                 # 팀원별 로컬 작업 공간 (Git 제외)
│  ├─ backend_a/
│  ├─ backend_b/
│  ├─ frontend_a/
│  └─ frontend_b/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/
│  │  │  ├─ api_response.py
│  │  │  ├─ supabase_config.py
│  │  │  ├─ password.py
│  │  │  ├─ gemini_config.py
│  │  │  └─ log_utils.py
│  │  ├─ exceptions/
│  │  │  └─ handlers.py
│  │  ├─ routers/
│  │  │  ├─ auth_router.py
│  │  │  ├─ records_router.py
│  │  │  ├─ uploads_router.py
│  │  │  ├─ studies_router.py
│  │  │  ├─ analyses_router.py
│  │  │  └─ admin_router.py
│  │  ├─ schemas/
│  │  │  ├─ auth_schema.py
│  │  │  ├─ record_schema.py
│  │  │  ├─ study_schema.py
│  │  │  ├─ analysis_schema.py
│  │  │  └─ admin_schema.py
│  │  └─ services/
│  │     ├─ auth_service.py
│  │     ├─ record_service.py
│  │     ├─ upload_service.py
│  │     ├─ study_service.py
│  │     ├─ analysis_service.py
│  │     └─ admin_service.py
│  ├─ sql/
│  │  ├─ 01_users.sql
│  │  ├─ 02_study_records.sql
│  │  ├─ 03_studies.sql
│  │  ├─ 04_study_members.sql
│  │  └─ 05_operation_logs.sql
│  ├─ tests/
│  │  ├─ test_auth_router.py
│  │  ├─ test_records_router.py
│  │  ├─ test_studies_router.py
│  │  ├─ test_analyses_router.py
│  │  └─ test_admin_router.py
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ README.md
├─ frontend_user/
│  ├─ app.py
│  ├─ core/
│  │  ├─ api_client.py
│  │  └─ auth.py
│  ├─ clients/
│  │  ├─ auth_client.py
│  │  ├─ personal_study_client.py
│  │  ├─ group_study_client.py
│  │  └─ analysis_client.py
│  ├─ app_pages/
│  │  ├─ 00_login.py
│  │  ├─ 01_signup.py
│  │  ├─ 02_home.py
│  │  ├─ 03_personal_study_list.py
│  │  ├─ 04_personal_study_form.py
│  │  ├─ 05_personal_study_detail.py
│  │  ├─ 06_group_study_list.py
│  │  ├─ 07_group_study_form.py
│  │  ├─ 08_group_study_detail.py
│  │  ├─ 09_analysis.py
│  │  └─ 10_mypage.py
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ README.md
├─ frontend_admin/
   ├─ app.py
   ├─ core/
   │  ├─ api_client.py
   │  └─ auth.py
   ├─ clients/
   │  ├─ auth_client.py
   │  └─ admin_client.py
   ├─ app_pages/
   │  ├─ 00_login.py
   │  ├─ 01_dashboard.py
   │  └─ 02_logs.py
   ├─ .env.example
   ├─ requirements.txt
   └─ README.md
└─ docs/
   └─ test_checklist.md
```

`.venv`, 업로드 파일, `.env`는 Git에 올리지 않습니다. 인증 사진은 로컬 `uploads/`가 아니라 Supabase Storage에 저장합니다.

## 3. 파일별 역할

### 3.1 백엔드

| 경로 | 역할 |
| --- | --- |
| `app/main.py` | FastAPI 생성, CORS, 예외 처리 등록, Swagger 태그, 모든 router 등록 |
| `core/supabase_config.py` | `.env`의 Supabase URL·서비스 키를 읽고 Supabase client 생성 |
| `core/password.py` | 회원가입 비밀번호 해싱과 로그인 비밀번호 검증 |
| `core/gemini_config.py` | `GEMINI_API_KEY`를 읽어 Gemini client 생성 |
| `core/api_response.py` | API 명세서의 표준 오류 `code/message/details/trace_id` 생성 helper |
| `core/log_utils.py` | 요청마다 `trace_id` 생성, `operation_logs` 성공·실패 행 저장 |
| `exceptions/handlers.py` | 400·401·404·409·422·500 예외를 표준 오류 JSON으로 변환 |
| `routers/*.py` | URL·HTTP Method·Pydantic 요청/응답만 정의하고 service 호출 |
| `schemas/*.py` | Swagger에 보이는 요청·응답 Pydantic 모델과 입력 제한 정의 |
| `services/*.py` | Supabase CRUD, Gemini 호출, 참여 인원·중복 여부 등 기능 규칙 처리 |
| `sql/01_users.sql`~`05_operation_logs.sql` | MVP 5개 테이블과 PK·UNIQUE·CHECK 제약조건 생성 SQL |
| `tests/*.py` | 회원가입 중복, 기록 CRUD, 정원 초과·중복 참여 등 핵심 규칙 확인 |

루트 `README.md`에는 프로젝트 소개, 기술 스택, `backend`·`frontend_user`·`frontend_admin` 실행 명령, 환경변수 설정 위치, Swagger URL, `docs/` 설계 문서 링크를 작성합니다.

### 3.2 사용자 프론트엔드

| 경로 | 역할 |
| --- | --- |
| `app.py` | `st.session_state` 초기화, 로그인 여부에 따른 메뉴 구성, 좌측 사이드바·로그아웃 |
| `core/api_client.py` | `BACKEND_URL` 기반 공통 `httpx` 요청, 표준 오류를 `BackendAPIError`로 변환 |
| `core/auth.py` | `user_id`, `name`, `role`, 로그인 여부 저장·초기화·로그아웃 |
| `clients/*.py` | 화면이 사용할 API별 호출 함수. 화면에서 `httpx`를 직접 호출하지 않음 |
| `00_login.py`, `01_signup.py` | 로그인·일반 사용자 회원가입 |
| `02_home.py` | 누적 학습 시간, 과목별 통계, 최근 기록 |
| `03_personal_study_list.py`, `04_personal_study_form.py`, `05_personal_study_detail.py` | 개인 학습 기록 목록·입력/수정·상세, 인증 사진 업로드·삭제 |
| `06_group_study_list.py` | 참여 중인 그룹, 그룹 탐색·검색·생성 이동, 5~10초 폴링 |
| `07_group_study_form.py`, `08_group_study_detail.py` | 그룹 생성·수정, 상세·참여자·참여·탈퇴 |
| `09_analysis.py` | 기간별 Gemini 분석 요청, 결과·기록 없음·오류·재시도 표시 |
| `10_mypage.py` | 세션의 이름·역할 표시와 로그아웃 |

### 3.3 관리자 프론트엔드

| 경로 | 역할 |
| --- | --- |
| `app.py` | 관리자 로그인 상태 확인, 대시보드·로그 메뉴 구성 |
| `core/auth.py` | MVP에서는 `role == 'admin'`일 때만 메뉴 표시. 서버 권한 검증은 확장 항목 |
| `clients/admin_client.py` | 대시보드·운영 로그 API 호출 |
| `01_dashboard.py` | 사용자·스터디·기록 수, 과목별 시간, 모집 상태, 기능 이용량, AI 지표 표시 |
| `02_logs.py` | 상태·action 필터, 로그 목록, message·latency·trace ID 표시 |

### 3.4 기능별 백엔드 파일 연결

| 기능 | Router → Schema → Service | 상세 역할 | 저장·조회 대상 |
| --- | --- | --- | --- |
| 회원가입·로그인·로그아웃 | `auth_router.py` → `auth_schema.py` → `auth_service.py` | 이메일 중복 확인, 비밀번호 해싱·검증, 로그인 사용자 정보 반환, 공개 가입 역할을 `user`로 고정 | `users`, `operation_logs` |
| 개인 학습 기록 | `records_router.py` → `record_schema.py` → `record_service.py` | 목록·상세 조회, 등록·수정·삭제, 과목·기간별 시간 통계 계산 | `study_records`, `operation_logs` |
| 인증 사진 | `uploads_router.py` → `record_schema.py` → `upload_service.py` | JPG/JPEG/PNG·5MB 제한 확인, Supabase Storage 업로드, 경로 반환 | Supabase Storage, `study_records.proof_image_path`, `operation_logs` |
| 그룹 스터디 | `studies_router.py` → `study_schema.py` → `study_service.py` | 목록·상세·검색, 생성자 자동 참여, 수정, 정원·중복·모집 상태 확인, 참여·탈퇴 | `studies`, `study_members`, `operation_logs` |
| AI 분석 | `analyses_router.py` → `analysis_schema.py` → `analysis_service.py` | 기간별 본인 기록 집계, Gemini 요청, 결과·기록 없음·외부 API 오류 반환 | `study_records` 조회, `operation_logs` |
| 관리자 조회 | `admin_router.py` → `admin_schema.py` → `admin_service.py` | 사용자·스터디·기록 수, 과목별 시간, 모집 상태, 기능 이용량, AI 지표와 로그 필터 집계 | 5개 MVP 테이블, 특히 `operation_logs` |

`router`는 HTTP와 Pydantic 입력 검증만 담당하고, `service`는 Supabase·Gemini 처리와 기능 규칙을 담당합니다. 모든 service는 성공·실패 시 `log_utils.py`를 호출해 동일한 `trace_id`를 오류 응답과 `operation_logs`에 남깁니다.

### 3.5 기능별 프론트엔드 파일 연결

| 화면 기능 | Client | Page | 상세 역할 |
| --- | --- | --- | --- |
| 로그인·회원가입 | `auth_client.py` | `00_login.py`, `01_signup.py` | API 요청 후 `core/auth.py`에 `user_id·name·role` 저장, 실패 메시지 표시 |
| 메인·개인 기록 목록 | `personal_study_client.py` | `02_home.py`, `03_personal_study_list.py` | 기록 목록·통계·빈 데이터 표시, 선택한 `record_id`를 상세 화면으로 전달 |
| 개인 기록 입력·상세 | `personal_study_client.py` | `04_personal_study_form.py`, `05_personal_study_detail.py` | 사진 업로드 뒤 경로를 포함해 저장, 상세 조회·수정 이동·삭제 확인 처리 |
| 그룹 목록·입력·상세 | `group_study_client.py` | `06_group_study_list.py`, `07_group_study_form.py`, `08_group_study_detail.py` | 참여 중 그룹·검색 결과 분리, `source=list/search` 호출, 생성·수정·참여·탈퇴 처리 |
| AI 분석·마이페이지 | `analysis_client.py`, `auth_client.py` | `09_analysis.py`, `10_mypage.py` | 분석 기간 요청과 오류·재시도, 세션 사용자 정보·로그아웃 표시 |
| 관리자 대시보드·로그 | `frontend_admin/clients/admin_client.py` | `frontend_admin/app_pages/01_dashboard.py`, `02_logs.py` | 3~5초 폴링, KPI·로그 필터·trace ID 표시 |

페이지는 client 함수만 호출하고, `core/api_client.py`가 공통 HTTP 오류를 `BackendAPIError`로 바꿉니다. 따라서 화면마다 HTTP 상태 처리 코드를 반복하지 않습니다.

## 4. 데이터베이스 구현 계획

테이블의 전체 필드·타입·제약조건은 `03_데이터베이스_설계서_MVP.md`를 따릅니다. 아래 내용은 SQL 파일 분리와 구현 연결 기준입니다.

| 테이블 | 핵심 필드·제약 | 사용하는 기능 |
| --- | --- | --- |
| `users` | `user_id`, `email UNIQUE`, `password_hash`, `name`, `role` | 회원가입·로그인·관리자 구분 |
| `study_records` | `record_id`, `user_id`, `subject`, `content`, `study_minutes > 0`, `studied_on`, `proof_image_path` | 개인 학습 기록·통계·AI 분석 |
| `studies` | `study_id`, `owner_user_id`, `title`, `category`, `goal`, `schedule`, `capacity`, `status` | 그룹 생성·탐색·상세 |
| `study_members` | `study_member_id`, `study_id`, `user_id`, `joined_at`, `UNIQUE(study_id, user_id)` | 중복 참여 방지·참여 인원·탈퇴 |
| `operation_logs` | `log_id`, `created_at`, `user_id`, `action`, `status`, `message`, `latency_ms`, `trace_id` | 관리자 대시보드·로그 |

- 가입 시 `users.role`은 항상 `user`로 저장합니다.
- 그룹 생성은 `studies` 생성 뒤 같은 사용자를 `study_members`에 자동 추가합니다.
- 탈퇴는 MVP에서 `study_members` 행을 삭제합니다.
- 모든 주요 API 성공·실패는 `operation_logs`에 기록합니다.
- 학습 통계는 `study_records`를 과목별로 합산합니다. AI 성공률·오류율은 `operation_logs`의 `analysis.request` 성공·실패를 집계합니다.

## 5. API 구현 계획

URL, HTTP Method, 요청·응답 모델, 오류 코드는 `03_API_명세서_MVP.md`를 최종 기준으로 합니다. 라우터·서비스·프론트엔드 client는 아래 구현 연결을 동일하게 사용합니다. MVP의 `user_id`는 Query 또는 JSON 본문으로 전달하는 **데이터 연결값**이며 인증 토큰이 아닙니다.

| Router / client | API | 서비스 처리 | 화면 |
| --- | --- | --- | --- |
| `auth_router` / `auth_client` | `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout` | 이메일 중복 검사, 비밀번호 해싱·검증, 기본 역할 `user` | 로그인·회원가입·로그아웃 |
| `records_router` / `personal_study_client` | `GET/POST /records`, `GET/PUT/DELETE /records/{record_id}`, `GET /records/stats` | 기록 CRUD·상세 조회, 과목·기간별 시간 합계 | 메인·개인 스터디 |
| `uploads_router` / `personal_study_client` | `POST /uploads/proof-image` | 파일 형식·크기 검사, Storage 업로드, 경로 반환 | 개인 스터디 입력 |
| `studies_router` / `group_study_client` | `GET/POST /studies`, `GET/PUT /studies/{study_id}`, `POST/DELETE /studies/{study_id}/join` | 키워드·분야·상태 검색, 생성자 자동 참여, 정원·중복·모집 종료 검사 | 그룹 스터디 목록·입력·상세 |
| `analyses_router` / `analysis_client` | `POST /analyses` | 해당 사용자의 기간별 기록 집계 후 Gemini 요청, 결과 또는 오류 반환 | AI 분석 |
| `admin_router` / `admin_client` | `GET /admin/dashboard`, `GET /admin/logs` | 로그·테이블 집계, 상태·action 로그 필터 | 관리자 대시보드·로그 |

### API별 필수 규칙

- 모든 router는 Pydantic schema를 사용해 필수값·길이·범위를 검증합니다.
- 오류는 `code`, `message`, `details`, `trace_id` 형식으로 반환합니다.
- `study.join`은 이미 참여함, 정원 초과, 모집 마감 시 `409`를 반환합니다.
- `GET /studies`의 `source` Query Parameter가 `search`일 때만 `study.search` 로그를 기록합니다. 5~10초 폴링·일반 목록 조회는 `source=list`로 호출해 `study.list`로 기록합니다.
- 관리자 대시보드는 `subject_minutes`, `study_status_counts`, `action_counts`, `ai_metrics`를 반환합니다.
- Gemini API 키·Supabase 서비스 키·비밀번호 원문·학습 내용 원문은 로그에 저장하지 않습니다.

## 6. 화면 구현 계획

화면의 정확한 레이아웃, 메뉴, 버튼 조건, 폴링 주기, Loading·빈 데이터·오류 표시는 `03_화면_설계서_MVP.md`를 최종 기준으로 합니다. 아래 표는 각 화면을 구현할 파일과 API 연결만 정합니다.

| 화면 | 구현 파일 | 호출 API | 완료 기준 |
| --- | --- | --- | --- |
| 로그인·회원가입 | `00_login.py`, `01_signup.py` | `/auth/signup`, `/auth/login` | 로그인 뒤 세션에 사용자 정보 저장, 중복 이메일·실패 메시지 표시 |
| 메인 | `02_home.py` | `/records`, `/records/stats` | 누적 시간·과목별 시간·최근 기록·빈 데이터 버튼 표시 |
| 개인 스터디 목록·입력·상세 | `03_personal_study_list.py`~`05_personal_study_detail.py` | `/records`, `/records/{record_id}`, `/uploads/proof-image` | 목록·상세 조회, 등록·수정·삭제와 업로드 오류 표시 |
| 그룹 스터디 목록 | `06_group_study_list.py` | `/studies` | 참여 중 그룹과 탐색 결과 분리, 검색·새로고침·빈 결과, 폴링 반영 |
| 그룹 스터디 입력·상세 | `07_group_study_form.py`, `08_group_study_detail.py` | `/studies`, `/studies/{id}/join` | 생성·수정, 참여자·정원·모집 상태, 참여·탈퇴 처리 |
| AI 분석 | `09_analysis.py` | `/analyses` | 기간 선택, 분석 결과, 기록 없음·Gemini 실패·재시도 표시 |
| 마이페이지 | `10_mypage.py` | `/auth/logout` | 세션 사용자 정보와 로그아웃 표시 |
| 관리자 대시보드 | `01_dashboard.py` | `/admin/dashboard` | 핵심 수치·과목·스터디·AI 지표, 3~5초 폴링 |
| 운영 로그 | `02_logs.py` | `/admin/logs` | 상태·기능 필터와 trace ID·오류 상세 표시 |

모든 화면은 Loading, 빈 데이터, 입력 오류, API 오류, 404를 공통으로 표시합니다. `403` 권한 오류 화면은 서버 세션 인증을 도입하는 확장 단계에서 실제로 활성화합니다.

## 7. 개발 순서와 담당 경계

| 순서 | 백엔드 작업 | 프론트엔드 작업 | 확인 방법 |
| --- | --- | --- | --- |
| 1 | 프로젝트 뼈대, Supabase 연결, `users` SQL, Auth API | 두 앱의 `app.py`, 세션 상태, 로그인·회원가입 | Swagger 회원가입·로그인 후 메뉴 전환 |
| 2 | 기록·사진 업로드 API, `study_records` SQL | 메인·기록 목록·입력 화면 | 등록 후 통계와 목록 갱신 |
| 3 | 스터디·참여 API, `studies/study_members` SQL | 그룹 목록·생성·상세 화면 | 생성자 자동 참여, 중복·정원 초과 오류 |
| 4 | Gemini 분석 API, 공통 로그 저장 | AI 분석 화면과 오류·재시도 | 기록 유무별 분석 결과 확인 |
| 5 | 관리자 집계·로그 조회 API | 관리자 대시보드·로그 화면 | 로그 생성 후 지표·필터 확인 |
| 6 | 예외 처리·테스트·Render 환경변수 | 폴링·공통 오류 화면·최종 UI 점검 | 배포 URL과 Swagger로 시연 |

프론트엔드는 API 명세에 없는 필드를 임의로 만들지 않고 client 함수만 호출합니다. 백엔드는 화면 배치나 Streamlit 상태를 알 필요 없이 요청·응답 계약과 DB 규칙만 구현합니다.

## 8. 실행 환경과 제외 범위

### 환경변수

```text
# backend/.env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
GEMINI_API_KEY=

# frontend_user/.env, frontend_admin/.env
BACKEND_URL=https://<render-backend-url>
```

- Render에는 백엔드와 두 Streamlit 앱을 각각 배포합니다.
- 비밀번호는 `password_hash`만 저장합니다.
- 현재 MVP에서는 JWT, Redis, 서버 세션 테이블, 분석 이력, 다중 인증 사진, 사용자 평가, Gemini 멀티턴 채팅을 구현하지 않습니다.
- 위 기능은 기존 상세 DB 설계서와 확장 API의 후속 범위입니다.

## 9. 담당 파일 분리와 Git 협업 규칙

각 담당자는 아래 소유 파일만 직접 수정합니다. 다른 담당자의 파일 변경이 필요하면 해당 담당자에게 요청하고, 공용 파일은 소유자가 PR 병합 전에 반영합니다.

| 담당 | 소유 파일·폴더 | 구현 범위 |
| --- | --- | --- |
| 백엔드 A | `backend/app/main.py`, `core/`, `exceptions/`, `routers/auth_router.py`, `routers/records_router.py`, `routers/uploads_router.py`, `schemas/auth_schema.py`, `schemas/record_schema.py`, `services/auth_service.py`, `services/record_service.py`, `services/upload_service.py`, `sql/01_users.sql`, `sql/02_study_records.sql`, `tests/test_auth_router.py`, `tests/test_records_router.py`, `requirements.txt`, `.env.example` | 공통 설정·표준 오류·로그 helper, 회원·기록·사진 API |
| 백엔드 B | `routers/studies_router.py`, `routers/analyses_router.py`, `routers/admin_router.py`, `schemas/study_schema.py`, `schemas/analysis_schema.py`, `schemas/admin_schema.py`, `services/study_service.py`, `services/analysis_service.py`, `services/admin_service.py`, `sql/03_studies.sql`, `sql/04_study_members.sql`, `sql/05_operation_logs.sql`, `tests/test_studies_router.py`, `tests/test_analyses_router.py`, `tests/test_admin_router.py` | 그룹 스터디·Gemini 분석·관리자 집계 API |
| 프론트엔드 A | `frontend_user/app.py`, `frontend_user/core/`, `frontend_user/clients/auth_client.py`, `frontend_user/clients/personal_study_client.py`, `frontend_user/app_pages/00_login.py`~`05_personal_study_detail.py`, `frontend_user/requirements.txt`, `frontend_user/README.md` | 사용자 앱 공통 상태·사이드바, 로그인·회원가입·메인·개인 스터디 목록·입력·상세 |
| 프론트엔드 B | `frontend_user/clients/group_study_client.py`, `frontend_user/clients/analysis_client.py`, `frontend_user/app_pages/06_group_study_list.py`~`10_mypage.py`, `frontend_admin/` 전체 | 그룹 스터디·AI 분석·마이페이지, 관리자 앱 전체 |
| 공용 문서 담당 | 루트 `README.md`, `docs/*.md`, `docs/test_checklist.md`, 루트 `.gitignore` | 프로젝트 안내·API 계약 변경 기록, 테스트 결과 취합, Git 제외 규칙 관리 |

`backend/app/main.py`는 백엔드 A만 router를 등록합니다. 백엔드 B는 router 구현 후 파일 경로와 router 변수 이름만 전달합니다. `frontend_user/app.py`도 프론트엔드 A만 메뉴를 등록하며, 프론트엔드 B는 페이지 경로·메뉴명을 전달합니다.

### 브랜치와 병합 순서

1. 담당자는 자신의 담당 기능용 브랜치에서 소유 파일만 커밋합니다. 브랜치의 정확한 이름은 팀이 정하지 않아도 됩니다.
2. API 요청·응답 변경은 API 명세서를 먼저 합의합니다.
3. 백엔드 PR을 먼저 병합하고 Swagger에서 확인한 뒤, 연결되는 프론트엔드 PR을 병합합니다.
4. 공용 파일은 소유자가 최신 `main`을 반영한 뒤 병합합니다. 백엔드 A는 새 router를 `main.py`에 등록하고, 프론트엔드 A는 새 사용자 페이지를 `frontend_user/app.py` 메뉴에 등록했는지 확인합니다.
5. 다른 사람 파일을 임시 수정해야 하면 독립 커밋으로 분리하고 담당자 확인 전에는 병합하지 않습니다.

## 10. 테스트 계획

### 10.1 백엔드 자동 테스트

`pytest`와 FastAPI `TestClient`로 router 단위 테스트를 작성합니다. Supabase·Gemini는 실제 키를 쓰지 않고 service 함수를 mock 처리합니다.

| 테스트 파일 | 담당 | 필수 확인 |
| --- | --- | --- |
| `test_auth_router.py` | 백엔드 A | 일반 사용자 가입, 중복 이메일 409, 정상·실패 로그인, 비밀번호 평문 미저장 |
| `test_records_router.py` | 백엔드 A | 기록 목록·상세·등록·수정·삭제, `study_minutes` 입력 오류, 통계 합계, 사진 형식·크기 오류 |
| `test_studies_router.py` | 백엔드 B | 생성자 자동 참여, 검색 조건, 중복 참여·정원 초과·모집 마감 409, 탈퇴 |
| `test_analyses_router.py` | 백엔드 B | 기간별 기록 전달, 기록 없음 404, Gemini 실패 500/503, 성공·실패 로그 저장 |
| `test_admin_router.py` | 백엔드 B | 과목별 시간, 모집 상태, `study.search`만 검색 지표 집계, AI 성공률·오류율, 로그 필터·trace ID |

백엔드 `requirements.txt`에는 최소 `fastapi`, `uvicorn`, `pydantic`, `supabase`, `python-dotenv`, `google-genai`, `httpx`, `pytest`, `python-multipart`, `bcrypt`를 기록합니다. 프론트엔드 `requirements.txt`에는 최소 `streamlit`, `httpx`를 기록합니다. 백엔드 폴더에서 `pytest -q`를 실행하고, 실패한 테스트는 같은 브랜치에서 통과시킨 후 PR을 생성합니다.

### 10.2 프론트엔드 수동 테스트

`docs/test_checklist.md`에는 실행 날짜·담당자·결과만 기록합니다. 체크리스트는 공용 문서 담당이 병합합니다.

| 영역 | 담당 | 확인 시나리오 |
| --- | --- | --- |
| 사용자 인증·기록 | 프론트엔드 A | 가입→로그인→기록 등록→사진 업로드→통계·빈 데이터·입력 오류 |
| 그룹·AI | 프론트엔드 B | 그룹 생성→참여→탈퇴, 검색·폴링, 분석 성공·기록 없음·Gemini 오류·재시도 |
| 관리자 | 프론트엔드 B | 관리자 로그인, KPI·로그 필터·trace ID, 3~5초 갱신 |
| 통합 | 전원 | 새 router의 `main.py` 등록, 새 사용자 페이지의 `app.py` 메뉴 등록, 사용자 동작 뒤 관리자 로그·지표 갱신, Render URL과 Swagger 호출 |

## 11. `.gitignore` 관리

루트 `.gitignore`에는 아래 항목을 추가합니다. `.env.example`, SQL, 테스트 코드, 문서용으로 선별한 화면 캡처만 Git에 포함합니다.

```gitignore
# 비밀값과 Streamlit 설정
.env
.env.*
!.env.example
**/.streamlit/secrets.toml

# 가상환경·Python 생성 파일
.venv/
venv/
**/__pycache__/
*.py[cod]

# 테스트·커버리지 산출물
.pytest_cache/
.coverage
coverage.xml
htmlcov/
test-results/
tests/artifacts/

# 팀원별 로컬 실험·메모·임시 실행 공간
team_workspace/backend_a/
team_workspace/backend_b/
team_workspace/frontend_a/
team_workspace/frontend_b/

# 로컬 업로드·로그
uploads/
*.log

# 운영체제·편집기 개인 설정
.DS_Store
Thumbs.db
.vscode/*.local.json
```

- `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`는 절대 커밋하지 않습니다. `BACKEND_URL`은 두 Streamlit 앱의 Render 환경변수로 설정하며, 코드에 직접 작성하지 않습니다.
- 테스트 중 생성한 인증 사진, 커버리지 HTML, 실패 화면 캡처는 `tests/artifacts/`에 두고 Git에서 제외합니다.
- 팀이 공유해야 하는 화면 캡처만 `docs/images/`에 이름을 정해 별도로 추가합니다.
- 각 팀원은 `team_workspace/<내_담당>/`에서 API 호출 실험, 임시 화면, 개인 메모를 관리합니다. 공유가 필요한 코드·문서만 정리해 담당 기능 폴더로 옮긴 뒤 커밋합니다.

## 12. MVP 기능 매핑 검증

아래 표는 후보 기능(AI 평가·Gemini 멀티턴·Redis·WebSocket 등)을 제외한 현재 MVP 요구사항을 대상으로, 구현 파일이 모두 배정됐는지 확인한 결과입니다.

| MVP 기능 | DB·Storage | 백엔드 파일 | 프론트엔드 파일 | 테스트 | 결과 |
| --- | --- | --- | --- | --- | --- |
| 일반 사용자 회원가입·로그인·로그아웃 | `users` | `auth_router/schema/service`, `password.py` | `auth_client.py`, `00_login.py`, `01_signup.py`, `core/auth.py` | `test_auth_router.py` | 매핑 완료 |
| 개인 기록 목록·상세·등록·수정·삭제 | `study_records` | `records_router/schema/service` | `personal_study_client.py`, `02_home.py`, `03_personal_study_list.py`~`05_personal_study_detail.py` | `test_records_router.py` | 매핑 완료 |
| 인증 사진 업로드 | Supabase Storage, `proof_image_path` | `uploads_router.py`, `upload_service.py` | `personal_study_client.py`, `04_personal_study_form.py` | `test_records_router.py` | 매핑 완료 |
| 과목별·누적 학습 통계 | `study_records` | `records_router.py`, `record_service.py` | `02_home.py` | `test_records_router.py` | 매핑 완료 |
| 그룹 생성·목록·검색·상세·수정 | `studies`, `study_members` | `studies_router/schema/service` | `group_study_client.py`, `06_group_study_list.py`~`08_group_study_detail.py` | `test_studies_router.py` | 매핑 완료 |
| 그룹 참여·탈퇴·정원·중복 검사 | `study_members` | `studies_router.py`, `study_service.py` | `08_group_study_detail.py` | `test_studies_router.py` | 매핑 완료 |
| 그룹 변경 폴링·검색 로그 분리 | `operation_logs` | `studies_router.py`, `log_utils.py` | `06_group_study_list.py` | `test_studies_router.py`, `test_admin_router.py` | 매핑 완료 |
| Gemini 단일 분석·오류·재시도 | `study_records` 조회, `operation_logs` | `analyses_router/schema/service`, `gemini_config.py` | `analysis_client.py`, `09_analysis.py` | `test_analyses_router.py` | 매핑 완료 |
| 운영 로그·관리자 지표 | `operation_logs`와 MVP 테이블 | `admin_router/schema/service`, `log_utils.py` | `frontend_admin/clients/admin_client.py`, `01_dashboard.py`, `02_logs.py` | `test_admin_router.py` | 매핑 완료 |
| Loading·빈 데이터·입력·API 오류 | 해당 없음 | `exceptions/handlers.py`, `api_response.py` | 두 앱의 `core/api_client.py`, 각 page | 자동 테스트 + 수동 체크리스트 | 매핑 완료 |

문서 매핑 결과로는 현재 MVP의 필수 기능에 빠진 파일이 없습니다. 다만 이는 구현 계획의 완결성 검증이며, 실제 동작 여부는 10단계 테스트와 Render 배포 시연으로 확인합니다.

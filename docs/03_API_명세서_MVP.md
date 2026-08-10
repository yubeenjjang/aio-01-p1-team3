# API 명세서｜간소화 MVP

```text
Base URL: http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
Format:   application/json (이미지 업로드만 multipart/form-data)
```

> **현재 구현 기준 문서:** 이 API 명세서는 `03_데이터베이스_설계서_MVP.md`를 기준으로 합니다. 서버 세션·분석 이력·다중 이미지 등은 문서 마지막의 확장 API에서 다룹니다.

## 목차

1. 로그인 사용자 전달
2. 공통 오류
3. Auth
4. Records
5. Studies
6. AI Analysis
7. Admin
8. Streamlit 호출표
9. 전체 기능 확장 시 추가 API

## 문서 개요

| 항목 | 내용 |
| --- | --- |
| 서비스명 | 스터디 관리 웹 서비스 |
| 목적 | 학습 기록·스터디·Gemini 분석·운영 로그를 관리 |
| Base URL | `http://127.0.0.1:8000` |
| 데이터 형식 | JSON, 이미지 업로드는 `multipart/form-data` |
| API 버전 | v1 |
| 현재 사용자 식별 방식 | Streamlit `session_state`의 `user_id`를 요청에 포함 |
| 확장 인증 방식 | FastAPI 서버 세션과 보안 쿠키 |

## 사용자 식별값 전달 (MVP)

로그인 성공 후 Streamlit은 `user_id`, `role`을 `st.session_state`에 저장합니다. 기능 API는 학습 기록·스터디·로그를 어떤 사용자와 연결할지 알기 위해 `user_id`를 Query Parameter 또는 JSON 본문으로 받습니다.

```text
GET 요청:  /records?user_id={user_id}
POST/PUT:  { "user_id": "{user_id}", ... }
DELETE:    /records/{record_id}?user_id={user_id}
```

`user_id`는 **인증 토큰이나 보안 정보가 아닙니다.** 간소화 MVP에서는 정상적인 입력만 들어온다고 가정하고 데이터 연결에만 사용합니다. 메뉴 분리는 Streamlit의 `role` 값으로 처리합니다. FastAPI의 실제 세션 인증·권한 검증은 전체 기능 확장 단계에서 추가합니다.

## 공통 오류

```json
{
  "code": "ERROR_CODE",
  "message": "오류 메시지",
  "details": {},
  "trace_id": "uuid"
}
```

| Code | 의미 |
| --- | --- |
| 400 | 입력값 오류 |
| 401 | 로그인 실패 |
| 403 | 전체 기능 확장 시 서버 권한 검증에 사용 |
| 404 | 데이터 없음 |
| 409 | 중복 참여·정원 초과·모집 종료 |
| 500 | 서버·Gemini 오류 |

## 운영 로그 action 이름

FastAPI는 아래 이름으로 `operation_logs.action` 값을 저장합니다.

| 기능 | action |
| --- | --- |
| 로그인·로그아웃 | `auth.login`, `auth.logout` |
| 학습 기록 | `record.create`, `record.update`, `record.delete`, `record.list` |
| 인증 사진 업로드 | `record.image_upload` |
| 스터디 | `study.create`, `study.update`, `study.list`, `study.search`, `study.detail`, `study.join`, `study.leave` |
| AI 분석 | `analysis.request` |
| 관리자 조회 | `admin.dashboard`, `admin.logs` |

## 요청·응답 모델

FastAPI는 아래 Pydantic 모델을 기준으로 Swagger(`/docs`)에 요청·응답 형식을 표시합니다.

```python
from datetime import date, datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

class SignupRequest(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=50)

class LoginRequest(BaseModel):
    email: str
    password: str

class RecordRequest(BaseModel):
    user_id: UUID
    subject: str = Field(..., min_length=1, max_length=100)
    content: str | None = Field(default=None, max_length=2000)
    study_minutes: int = Field(..., ge=1, le=1440)
    studied_on: date
    proof_image_path: str | None = None

class StudyRequest(BaseModel):
    user_id: UUID
    title: str = Field(..., min_length=1, max_length=100)
    category: str
    goal: str
    schedule: str
    capacity: int = Field(..., ge=2, le=20)
    status: Literal["recruiting", "closed"] = "recruiting"

class StudyMemberResponse(BaseModel):
    user_id: UUID
    name: str
    joined_at: datetime

class StudyResponse(BaseModel):
    study_id: UUID
    owner_user_id: UUID
    title: str
    category: str
    goal: str
    schedule: str
    capacity: int
    member_count: int
    status: Literal["recruiting", "closed"]
    is_joined: bool

class StudyDetailResponse(BaseModel):
    study: StudyResponse
    members: list[StudyMemberResponse]

class SubjectStat(BaseModel):
    subject: str
    minutes: int

class RecordStatsResponse(BaseModel):
    total_minutes: int
    by_subject: list[SubjectStat]

class AnalysisRequest(BaseModel):
    user_id: UUID
    period_start: date
    period_end: date
```

## 표준 오류 응답

FastAPI는 요청마다 `trace_id`를 생성하고, 오류 응답과 `operation_logs`에 같은 값을 저장합니다.

```json
{
  "code": "STUDY_FULL",
  "message": "스터디 정원이 가득 찼습니다.",
  "details": {"study_id": "uuid", "capacity": 5},
  "trace_id": "uuid"
}
```

| API | 주요 오류 코드 | HTTP 상태 |
| --- | --- | --- |
| `POST /auth/signup` | `VALIDATION_ERROR`, `EMAIL_DUPLICATED` | 400, 409 |
| `POST /auth/login` | `LOGIN_FAILED` | 401 |
| `GET /records/{record_id}` | `RECORD_NOT_FOUND` | 404 |
| `POST`, `PUT /records` | `VALIDATION_ERROR`, `RECORD_NOT_FOUND` | 400, 404 |
| `POST /uploads/proof-image` | `INVALID_FILE_TYPE`, `FILE_TOO_LARGE` | 400 |
| `POST /studies/{study_id}/join` | `STUDY_NOT_FOUND`, `ALREADY_JOINED`, `STUDY_FULL`, `STUDY_CLOSED` | 404, 409 |
| `POST /analyses` | `NO_STUDY_RECORDS`, `GEMINI_REQUEST_FAILED`, `GEMINI_UNAVAILABLE` | 404, 500, 503 |
| 전체 API | `RATE_LIMITED` | 429 |

## Auth

### `POST /auth/signup`

```json
// Request
{"email":"user@example.com","password":"password123","name":"홍길동"}

// Response 201
{"user_id":"uuid","email":"user@example.com","name":"홍길동","role":"user"}
```

공개 회원가입으로 생성되는 계정의 역할은 항상 `user`입니다. 관리자 계정은 회원가입 화면에서 선택하지 않으며, 배포·운영 담당자가 별도 초기 데이터 또는 관리 절차로만 생성합니다.

### `POST /auth/login`

```json
// Request
{"email":"user@example.com","password":"password123"}

// Response 200
{"user_id":"uuid","name":"홍길동","role":"user"}
```

### `POST /auth/logout`

Query: `user_id`  
Response: `204 No Content`

## Records

### `GET /records`

Query: `user_id`, `from?`, `to?`, `subject?`

```json
// Response 200
{
  "items":[{
    "record_id":"uuid", "subject":"Python", "content":"FastAPI 학습",
    "study_minutes":90, "studied_on":"2026-08-07", "proof_image_path":null
  }],
  "total":1
}
```

### `GET /records/{record_id}`

Query: `user_id`

```json
// Response 200
{"record_id":"uuid","subject":"Python","content":"FastAPI 학습","study_minutes":90,"studied_on":"2026-08-07","proof_image_path":"records/user-id/file.png"}
```

Errors: `404 RECORD_NOT_FOUND`

### `POST /records`

```json
// Request
{
  "user_id":"uuid", "subject":"Python", "content":"FastAPI 학습", "study_minutes":90,
  "studied_on":"2026-08-07", "proof_image_path":null
}

// Response 201
{"record_id":"uuid","subject":"Python","content":"FastAPI 학습","study_minutes":90,"studied_on":"2026-08-07","proof_image_path":null}
```

Rules: `subject` 1~100자, `study_minutes` 1~1440

### `PUT /records/{record_id}`

Request: `POST /records`와 동일  
Response: `200` + 학습 기록 객체  
Errors: `404` 기록 없음

### `DELETE /records/{record_id}`

Query: `user_id`  
Response: `204 No Content`

### `POST /uploads/proof-image`

Content-Type: `multipart/form-data`  
Form: `user_id`, `file` (JPG/JPEG/PNG, 최대 5MB)

```json
// Response 200
{"proof_image_path":"records/user-id/file.png"}
```

### `GET /records/stats`

Query: `user_id`, `from?`, `to?`

```json
// Response 200
{"total_minutes":300,"by_subject":[{"subject":"Python","minutes":180}]}
```

## Studies

### `GET /studies`

Query: `user_id`, `keyword?`, `category?`, `status?`, `source?` (`list` 또는 `search`, 기본 `list`)

사용자가 검색 버튼으로 조건을 적용하면 프론트엔드는 `source=search`를 전달하고 FastAPI는 `study.search` 로그를 저장합니다. 폴링·일반 목록 조회는 `source=list`를 전달하고 `study.list` 로그를 저장합니다.

```json
// Response 200
{
  "items":[{
    "study_id":"uuid", "owner_user_id":"uuid", "title":"FastAPI 스터디",
    "category":"백엔드", "goal":"CRUD 완성", "schedule":"월·수 19:00",
    "capacity":5, "member_count":3, "status":"recruiting", "is_joined":false
  }],
  "total":1
}
```

### `GET /studies/{study_id}`

Query: `user_id`

```json
// Response 200
{
  "study":{"study_id":"uuid","owner_user_id":"uuid","title":"FastAPI 스터디","category":"백엔드","goal":"CRUD 완성","schedule":"월·수 19:00","capacity":5,"member_count":3,"status":"recruiting","is_joined":true},
  "members":[{"user_id":"uuid","name":"홍길동","joined_at":"2026-08-07T10:30:00+09:00"}]
}
```

### `POST /studies`

```json
// Request
{"user_id":"uuid","title":"FastAPI 스터디","category":"백엔드","goal":"CRUD 완성","schedule":"월·수 19:00","capacity":5}

// Response 201
{"study_id":"uuid","title":"FastAPI 스터디","status":"recruiting","member_count":1}
```

Rules: `title` 1~100자, `capacity` 2~20. 생성자는 자동 참여합니다.

### `PUT /studies/{study_id}`

Request: 생성 요청 + `status` (`recruiting` 또는 `closed`)  
Response: `200` + 스터디 객체  
Errors: `404` 스터디 없음

### `POST /studies/{study_id}/join`

Request: `{"user_id":"uuid"}`

```json
// Response 201
{"message":"스터디에 참여했습니다."}
```

Errors: `409` 이미 참여함·정원 초과·모집 종료

### `DELETE /studies/{study_id}/join`

Query: `user_id`  
Response: `204 No Content`  
Errors: `400` 생성자는 탈퇴 불가

## AI Analysis

### `POST /analyses`

```json
// Request
{"user_id":"uuid","period_start":"2026-08-01","period_end":"2026-08-31"}

// Response 200
{
  "summary":"이번 달 총 학습 시간은 300분입니다.",
  "strengths":["Python 학습이 꾸준합니다."],
  "improvements":["SQL 학습 시간을 늘려보세요."],
  "next_goal":"다음 주 SQL 학습 120분"
}
```

Errors: `404` 분석할 기록 없음, `500` Gemini 요청 실패

## Admin

간소화 MVP에서는 Streamlit이 `role = admin`일 때만 관리자 메뉴를 표시합니다. FastAPI의 관리자 권한 검증은 전체 기능 확장 단계에서 추가합니다.

### `GET /admin/dashboard`

Query: `user_id`

```json
// Response 200
{
  "user_count":20, "study_count":5, "record_count":100,
  "subject_minutes":[{"subject":"Python","minutes":1800}],
  "study_status_counts":{"recruiting":3,"closed":2},
  "action_counts":{"record.create":30,"record.update":4,"record.delete":2,"study.create":5,"study.search":20,"study.join":10,"analysis.request":8},
  "ai_metrics":{"request_count":8,"success_count":6,"failure_count":2,"success_rate":75.0,"failure_rate":25.0,"average_latency_ms":1250},
  "failure_count":2
}
```

`subject_minutes`는 과목별 이용 현황, `study_status_counts`와 `action_counts`는 스터디 모집·검색·참여 현황, `ai_metrics`는 AI 요청량·성공률·오류율·평균 응답 시간을 위한 값입니다. `study.search`는 사용자가 검색 조건을 적용했을 때만 기록하며, 폴링·일반 목록 조회는 `study.list`로 기록해 검색 지표에서 제외합니다.

### `GET /admin/logs`

Query: `user_id`, `status?`, `action?`, `limit?` (기본 50)

```json
// Response 200
{
  "items":[{
    "log_id":1, "created_at":"2026-08-07T10:30:00+09:00",
    "user_name":"홍길동", "action":"analysis.request", "status":"failure",
    "message":"Gemini 요청에 실패했습니다.", "latency_ms":3000,
    "trace_id":"4d7e3e5b-3c78-4d6e-a0d3-6b5d4b8af0d3"
  }],
  "total":1
}
```

## Streamlit 호출표

| 화면 | API |
| --- | --- |
| 회원가입·로그인 | `/auth/signup`, `/auth/login` |
| 학습 기록·통계 | `/records`, `/records/{record_id}`, `/records/stats`, `/uploads/proof-image` |
| 스터디 목록·상세 | `/studies`, `/studies/{study_id}` |
| 스터디 참여·탈퇴 | `/studies/{study_id}/join` |
| AI 분석 | `/analyses` |
| 관리자 대시보드 | `/admin/dashboard`, `/admin/logs` |

## 전체 기능 확장 시 추가 API

아래 API는 현재 간소화 MVP에 포함하지 않습니다. 1·2단계에서 정의한 전체 기능으로 확장할 때 필요한 항목입니다.

### 1. 안전한 로그인 세션

| Method | URL | 역할 |
| --- | --- | --- |
| `POST` | `/auth/login` | 로그인 성공 시 서버 세션·보안 쿠키 발급 |
| `POST` | `/auth/logout` | 현재 세션 폐기 |
| `GET` | `/auth/me` | 현재 로그인 사용자와 역할 조회 |

이 단계에서는 `user_id`를 Query·본문으로 전달하지 않고, FastAPI가 보안 쿠키의 세션을 검증합니다.

### 2. 학습 기록 확장

| Method | URL | 역할 |
| --- | --- | --- |
| `GET` | `/records/{record_id}/images` | 학습 기록의 인증 사진 목록 조회 |
| `POST` | `/records/{record_id}/images` | 인증 사진 추가 업로드 |
| `DELETE` | `/records/{record_id}/images/{image_id}` | 인증 사진 삭제 |

여러 장의 인증 사진과 삭제 이력을 관리하려면 간소화 MVP의 `proof_image_path` 대신 상세 설계의 `study_record_images` 테이블을 사용합니다.

### 3. 스터디 기능 확장

| Method | URL | 역할 |
| --- | --- | --- |
| `GET` | `/studies?joined_only=true&schedule=...` | 내가 참여한 스터디·활동 시간대 조건 검색 |
| `GET` | `/studies/{study_id}/members` | 참여자 목록만 조회 |
| `PATCH` | `/studies/{study_id}/owner` | 생성자 권한을 다른 참여자에게 이전 |
| `GET` | `/studies/{study_id}/members/history` | 참여·탈퇴 이력 조회 |

재참여 이력과 동시 참여 요청 처리, 생성자 권한 이전은 상세 데이터베이스 설계의 스터디 운영 규칙을 확정한 뒤 구현합니다.

그룹 상세 화면의 확장 정보는 `description`, `start_date`, `end_date`를 `StudyRequest`와 `StudyResponse`에 추가해 제공합니다. 이 필드는 상세 데이터베이스 설계의 `studies` 테이블과 함께 도입합니다.

### 4. AI 분석 이력

| Method | URL | 역할 |
| --- | --- | --- |
| `POST` | `/analyses` | 분석 결과를 `ai_analyses`에 저장한 뒤 분석 ID 반환 |
| `GET` | `/analyses` | 내 분석 이력 목록 조회 |
| `GET` | `/analyses/{analysis_id}` | 특정 분석 결과·실패 정보 조회 |

### 5. 관리자 대시보드·로그 확장

| Method | URL | 역할 |
| --- | --- | --- |
| `GET` | `/admin/dashboard?from=...&to=...` | 기간별 사용자·스터디·기능 이용량·AI 성공률·오류율 조회 |
| `GET` | `/admin/studies/recruiting` | 모집 중 스터디와 참여 인원 현황 조회 |
| `GET` | `/admin/studies/low-members` | 참여 인원이 적은 스터디 조회 |
| `GET` | `/admin/logs?user_id=...&resource_type=...&resource_id=...&http_status=...` | 사용자·기능 데이터·HTTP 오류별 상세 로그 필터링 |

이 기능을 구현하려면 상세 설계의 `operation_logs` 필드(`resource_type`, `resource_id`, `result_count`, `http_status`)를 사용합니다.

### 6. 자동 갱신을 위한 조회 조건

| Method | URL | 역할 |
| --- | --- | --- |
| `GET` | `/studies?updated_after=...` | 마지막 조회 이후 변경된 스터디만 조회 |
| `GET` | `/admin/logs?occurred_after=...` | 마지막 조회 이후 새 로그만 조회 |

MVP에서는 기본 목록·상세 조회 API를 Streamlit이 주기적으로 호출하는 폴링 방식으로 최신 정보를 반영합니다. `updated_after`, `occurred_after` 조건은 데이터가 늘어날 때 추가하는 최적화 항목이며, Redis·WebSocket·SSE는 후속 후보입니다.

### 7. 팀 합의 필요 후보

| Method | URL | 역할 |
| --- | --- | --- |
| `POST` | `/analyses/{analysis_id}/feedback` | AI 분석 결과 점수·의견 등록 |
| `GET` | `/admin/analysis-feedback` | AI 분석 평가 통계 조회 |
| `POST` | `/chat/sessions` | Gemini 멀티턴 대화방 생성 |
| `GET` | `/chat/sessions` | 내 대화방 목록 조회 |
| `GET` | `/chat/sessions/{session_id}/messages` | 대화 이력 조회 |
| `POST` | `/chat/sessions/{session_id}/messages` | 사용자 메시지 전송·Gemini 응답 저장 |

AI 평가와 Gemini 멀티턴 채팅은 팀 합의 전 후보 기능이므로, 확정되기 전에는 MVP API와 화면에 포함하지 않습니다.

AI 평가를 확정하면 `POST /analyses/{analysis_id}/feedback`의 요청 본문은 `score: int (1~5, 필수)`, `comment: str | null (선택)`으로 하며, 성공 시 `201`과 피드백 식별자를 반환합니다. 이 기능은 현재 MVP 구현 대상이 아닙니다.

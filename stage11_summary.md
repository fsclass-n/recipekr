# Stage 11 Summary: 대시보드 권한 관리 기능 복원, 전역 디자인 통일 및 서비스 최적화

## 📌 목표 및 개요
10단계의 안정화 작업에 이어, 관리자 대시보드 내 유실되었던 **"회원 권한 관리"** 기능을 복원하고, 웹 페이지 전체의 로고 및 메뉴 디자인을 통일하였으며, 클라우드(Render) 환경 배포 시 발생하는 로그 인코딩 및 RPA 속도 지연 문제를 근본적으로 해결했습니다. 또한, Render 무료 범위 내에서 안정적으로 서비스를 구동하기 위한 가이드와 깃허브 액션(GitHub Actions) 기반의 서버 기상 시스템을 추가 구축했습니다.

---

## 🛠️ 주요 변경 내역

### 1. 전역 헤더 로고 통일 및 메뉴 음영 적용
- **헤더 로고 통일**: 기존에 페이지마다 상이하던 로고 이미지(`plate.svg` 등)를 메인 페이지와 일치하도록 **🍽️ 이모지**로 전역 통일했습니다.
  - 적용 대상: 공통 레이아웃([base.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/layout/base.html)), 레시피 추천([recommend.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/recipe/recommend.html)), 마이페이지([mypage.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/mypage.html)), 로그인([login.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/auth/login.html)), 회원가입([signup.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/auth/signup.html)), 관리자 대시보드([dashboard.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/admin/dashboard.html))
- **활성 메뉴 음영 처리**: 레시피 추천 페이지의 네비게이션 바에서 활성화된 메뉴 항목에 둥근 사각형 음영(`border-radius: 10px`, `box-shadow`, `border`)을 입혀 시각적 안정성과 통일성을 높였습니다.

### 2. 관리자 대시보드 내 "회원 권한 관리" 기능 복원 및 백엔드 연동
- **백엔드 기능 구현**: 
  - [UserRepository.java](file:///d:/wi/lab/recipekr/src/main/java/com/recipekr/repository/UserRepository.java)에 전체 회원을 역순 조회하는 `findAll()` 및 특정 사용자의 권한을 변경하는 `updateRole(id, role)` 메소드를 추가했습니다.
  - [AdminController.java](file:///d:/wi/lab/recipekr/src/main/java/com/recipekr/controller/AdminController.java)에서 회원 목록 데이터를 모델에 바인딩하여 뷰로 전달하고, `POST /admin/update-role` 엔드포인트를 추가로 매핑하여 권한 변경을 실제 DB에 반영할 수 있는 API를 완성했습니다.
- **프론트엔드 UI 반영**:
  - [dashboard.html](file:///d:/wi/lab/recipekr/src/main/resources/templates/admin/dashboard.html) 하단 영역에 가입된 회원들의 ID, 아이디, 닉네임, 이메일, 현재 권한(USER/ADMIN 배지)을 출력하는 테이블을 추가했습니다.
  - 관리자가 각 행마다 드롭다운을 통해 권한을 선택하고 체크(`✓`) 버튼을 눌러 즉시 서버에 반영할 수 있는 폼을 구성하고, `새로고침` 기능도 연결했습니다.

### 3. Render 서버 한글 로그 깨짐 수정
- [Dockerfile](file:///d:/wi/lab/recipekr/Dockerfile)의 `JAVA_OPTS` 환경변수에 `-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8` JVM 인자를 명시적으로 주입하여 Linux 환경의 Render 콘솔 로그에 한글이 깨지지 않고 정상 인코딩 출력되도록 해결했습니다.

### 4. RPA 크롤링 속도 개선 및 타임아웃 최적화
- 기존에 각 마트별 크롤러 스크립트(`emart_crawler.py`, `lottemart_crawler.py`, `homeplus_crawler.py`)에 하드코딩되어 있던 페이지 로드 제한 시간(35~40초)을 줄이기 위해 환경 변수 `PLAYWRIGHT_TIMEOUT`을 읽도록 동적 처리했습니다.
- `Dockerfile`에 `ENV PLAYWRIGHT_TIMEOUT=25000`을 명시하여 Render 클라우드 환경에서는 최대 **25초** 이내에 반응하지 않을 경우 빠르게 다음 대상지로 넘어가도록 하여 전체 RPA 대기 시간을 대폭 단축했습니다. (환경변수가 지정되지 않은 로컬 등에서는 기본 20초가 적용됩니다.)

---

## 📈 Render 무료 인스턴스 750시간 제한 및 깨우기(Wake-up) 전략

### ⚠️ 계정별 월 750시간 한도 주의 사항
렌더 무료 티어는 **단일 계정(Workspace)당 총 750시간**의 가동 시간 한도를 공유합니다.
- `movie-flow`와 `recipekr` 2개 웹 서비스를 하나의 계정에서 24시간 내내 깨워두면 약 15일 만에 750시간 한도를 초과하여 한 달 전체 서비스가 강제 차단됩니다.
- 이를 해결하기 위한 최적의 방안을 아래와 같이 정리하였습니다.

### 1) 계정 분리 운영 (가장 직관적임)
- 렌더 회원가입을 2개의 계정으로 구분하여 진행하고, 각각 `movie-flow`와 `recipekr`를 한 개씩 배포합니다.
- 계정별로 750시간의 무료 가동 시간이 부여되므로, 두 프로젝트 모두 아래 깃허브 액션이나 외부 핑 서비스를 이용해 한 달 동안 24시간 내내 정상 작동시킬 수 있습니다.

### 2) GitHub Actions 기반 스케줄러를 통한 슬립 깨우기
- **공개(Public)** 레포지토리에 아래의 워크플로우 파일을 설정하면 GitHub Actions 실행 시간 제한 없이 무료로 Render 인스턴스를 깨울 수 있습니다. (비공개 레포지토리인 경우 월 2,000분 제한이 발생하므로 전용 Public 빈 레포지토리에 분리 가동을 적극 권장합니다.)

#### 📄 `.github/workflows/wake_up.yml` 설정 내용
```yaml
name: Wake Up Render Service

on:
  schedule:
    # 렌더의 슬립 모드(15분 미요청 시 중지)를 예방하기 위해 12분 간격으로 HTTP 호출을 보냅니다.
    # 단일 서비스(recipekr)만 가동하므로 24시간 상시 가동(월 720시간 소모)이 무료 범위(750시간) 내에 완전히 들어옵니다.
    - cron: '*/12 * * * *'
  
  workflow_dispatch: # 필요 시 깃허브 액션 탭에서 수동으로도 트리거 가능

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Web Service
        run: |
          echo "Pinging recipekr..."
          curl -sL -w " -> HTTP %{http_code}\n" "https://recipekr.onrender.com/" -o /dev/null
```

---

## 🔍 검증 결과
- `.\gradlew.bat compileJava` 빌드 정상 확인 (컴파일 에러 및 설정 무결성 검증 완료).
- `stage11_summary.md` 추가 및 깃 변경 파일 상태 확인.

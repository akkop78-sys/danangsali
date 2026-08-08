# 다낭살이 — 인터넷에 올리기 (Render)

이 쇼핑몰은 **Render 무료 웹서비스**에 올려 두면 지인에게 링크를 보낼 수 있습니다.

## 1. GitHub에 코드 올리기

1. https://github.com 가입
이미 코드가 올라가 있습니다: https://github.com/akkop78-sys/danangsali

## 2. Render에 연결 (지금 할 일)

1. 브라우저에서 열기: https://render.com/deploy?repo=https://github.com/akkop78-sys/danangsali  
   (또는 https://render.com 가입 후 GitHub로 로그인)
2. GitHub 권한을 허용합니다.
3. **Apply** / **Create** 를 누릅니다. (Free 플랜)
4. 5~10분 정도 빌드를 기다립니다.
5. 초록색 Live가 되면 `https://danangsali-xxxx.onrender.com` 같은 주소가 생깁니다.

수동으로 만들 때 설정값:
- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn shop:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

## 3. 환경변수 (권장)

| 키 | 값 |
|----|-----|
| `SECRET_KEY` | 아무 긴 비밀번호 문자열 |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | 본인만 아는 비밀번호 |
| `PAYMENT_MODE` | `demo` |

## 4. 접속

배포가 끝나면 Render가 `https://이름.onrender.com` 주소를 줍니다.  
그 주소를 지인에게 보내면 됩니다.

관리자: `https://이름.onrender.com/admin/login`

## 참고

- Render **무료** 플랜은 잠깐 접속이 없으면 잠들었다가, 다시 열면 30초~1분 걸릴 수 있습니다.
- 무료 서버의 SQLite 데이터는 재배포 시 초기화될 수 있습니다. (상품 샘플은 다시 자동 생성됨)
- 주문·회원을 오래 보관하려면 나중에 PostgreSQL을 붙이면 됩니다.

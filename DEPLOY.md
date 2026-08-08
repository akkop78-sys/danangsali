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
| `ADMIN_PASSWORD` | 관리자 비밀번호 (기본 안내: `danangsali123`) |
| `PAYMENT_MODE` | `demo` |
| `SHOP_PHONE` | 문자 문의용 번호 (화면에 노출 안 함, sms 링크만) |
| `SHOP_KAKAO` | 카카오톡 ID 또는 오픈채팅 안내 |
| `SHOP_EMAIL` | 이메일 문의용 (화면에 주소 노출 안 함, mailto 링크만) |
| `ADMIN_NOTIFY_EMAIL` | 주문·문의 알림 받을 이메일 |
| `DISCORD_WEBHOOK_URL` | (선택) 디스코드 웹훅 |
| `NTFY_TOPIC` | 폰 푸시 주제 (기본 `danangsali-akkop78-orders`) — [ntfy 앱](https://ntfy.sh)에서 구독 |
| `MAIL_SERVER` 등 | (선택) 지메일 SMTP로 메일 알림. 없으면 메일은 안 감 |

### 주문 알림 받는 법 (추천)

1. 휴대폰에 **ntfy** 앱 설치 (앱스토어/플레이스토어)
2. 앱에서 **Subscribe to topic** → `danangsali-akkop78-orders` 입력
3. 이후 주문이 들어오면 폰으로 알림이 옵니다
4. 주문 내용·주소는 관리자 로그인 → **주문** 메뉴에서도 항상 볼 수 있습니다

## 4. 접속

배포가 끝나면 Render가 `https://이름.onrender.com` 주소를 줍니다.  
그 주소를 지인에게 보내면 됩니다.

관리자: `https://이름.onrender.com/admin/login`

## 참고

- Render **무료** 플랜은 잠깐 접속이 없으면 잠들었다가, 다시 열면 30초~1분 걸릴 수 있습니다.
- 무료 서버의 SQLite 데이터는 **재배포 시 초기화**될 수 있습니다. (상품은 다시 자동 생성, 주문은 사라질 수 있음)
- 주문이 본격적으로 들어오면 Render 대시보드에서 **Disk**를 추가하고 환경변수 `DATA_DIR=/var/data` 를 넣으세요.
- 또는 Render **PostgreSQL**을 붙이고 `DATABASE_URL`을 연결하면 주문이 더 안전합니다.
- 당장은 입금 확인 시 카톡/메모장에 주문번호·이름·금액을 적어 두는 것도 방법입니다.

## 관리자 운영 순서

1. `/admin/login` → admin / (설정한 비밀번호)
2. **주문**에서 입금대기 확인 → 통장 대조 → 입금확인
3. 포장·발송 후 배송중/완료
4. **마케팅** 문구를 네이버에 주 2~3회 올리기

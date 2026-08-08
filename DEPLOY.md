# 다낭살이 — 인터넷에 올리기 (Render)

이 쇼핑몰은 **Render 무료 웹서비스**에 올려 두면 지인에게 링크를 보낼 수 있습니다.

## 1. GitHub에 코드 올리기

1. https://github.com 가입
2. 새 저장소 만들기 (예: `danangsali`)
3. 이 폴더에서 Git으로 push (아래 명령, 저장소 주소만 본인 것으로)

```bash
git init
git add .
git commit -m "Deploy danangsali shop"
git branch -M main
git remote add origin https://github.com/본인아이디/danangsali.git
git push -u origin main
```

## 2. Render에 연결

1. https://render.com 가입 (GitHub 로그인 추천)
2. **New +** → **Web Service**
3. GitHub 저장소 `danangsali` 연결
4. 설정:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn shop:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. **Create Web Service**

또는 저장소에 있는 `render.yaml`로 **New + → Blueprint** 배포도 가능합니다.

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

# Great Car — 카페24 서버 배포 가이드

**서버 정보**: `/var/www/greatcar` · Ubuntu · Python 3.10 · MariaDB 10.6 · Nginx · Gunicorn
**포트**: `127.0.0.1:8002` (기존 8001·8080·8091 사용 중이라 8002 지정)
**도메인**: `greatcar.kr` (primary), `greatcar.co.kr` (301 redirect)

---

## 1. Clone (이미 완료됨)

```bash
cd /var/www
git clone https://github.com/Jeongdonghwan/gcar_prj.git greatcar
cd greatcar
```

---

## 2. MariaDB DB · 유저 만들기 (수동, 1회)

```bash
mysql -u root -p
```

```sql
CREATE DATABASE greatcar DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 아래 비밀번호는 강한 값으로 바꿔서 사용, instance/.env 에도 같은 값 넣기
CREATE USER 'greatcar_user'@'localhost' IDENTIFIED BY '적당히_강한_비밀번호';
GRANT ALL PRIVILEGES ON greatcar.* TO 'greatcar_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 3. 초기 세팅 스크립트 실행

```bash
cd /var/www/greatcar
bash deploy/setup.sh
```

이 스크립트가 하는 일:
1. Python 3.10 확인
2. `.venv` 생성
3. `pip install -r requirements.txt`
4. `app/static/uploads/{_tmp,vehicles,brands,banners}` 생성 + 권한
5. `instance/.env` 자동 생성 + `SECRET_KEY` 랜덤 채워넣기
   - **일시정지 후 nano로 DB_PASSWORD 채우기 요구함**
6. DB 연결 확인 + `flask db upgrade`

`.env` 편집이 필요할 때:
```bash
nano /var/www/greatcar/instance/.env
# DB_PASSWORD 를 위 CREATE USER 시 넣은 값과 동일하게
```

---

## 4. 어드민 계정 · 시드 (선택)

```bash
cd /var/www/greatcar
source .venv/bin/activate
export FLASK_APP=run.py

# 어드민 (이메일은 valid TLD 사용: .dev / .com — .local·.test는 email_validator 거절)
flask create-admin
# ex) admin@greatcar.kr / 강한비번

# 브랜드 마스터 시드 (10개 브랜드 SVG 로고 포함)
flask seed-brands

# 샘플 차량 3대 (원한다면 — 실운영 전 삭제 가능)
# flask seed-real

# 기본 배너 3개 (텍스트만 — 어드민에서 이미지 업로드)
flask seed-banners
```

---

## 5. systemd 서비스 등록

```bash
sudo mkdir -p /var/log/greatcar
sudo chown www-data:www-data /var/log/greatcar

sudo cp /var/www/greatcar/deploy/greatcar.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable greatcar
sudo systemctl start greatcar
sudo systemctl status greatcar
```

정상이면:
```
● greatcar.service - Great Car — Flask App (Gunicorn)
     Loaded: loaded (/etc/systemd/system/greatcar.service; enabled; ...)
     Active: active (running) since ...
   Main PID: ...
      Tasks: 4 (limit: ...)
     Memory: ~150M
```

로컬 확인:
```bash
curl -I http://127.0.0.1:8002/
# HTTP/1.1 200 OK 나와야 함
```

---

## 6. Nginx site 등록

```bash
sudo cp /var/www/greatcar/deploy/greatcar.nginx /etc/nginx/sites-available/greatcar
sudo ln -sf /etc/nginx/sites-available/greatcar /etc/nginx/sites-enabled/greatcar

sudo nginx -t  # 문법 검사
sudo systemctl reload nginx
```

이 시점에 `http://greatcar.kr` (HTTP) 접속 시:
- Certbot이 발급하기 전이라 SSL 없음
- HTTP → HTTPS 301 리다이렉트 규칙 때문에 리다이렉트 오류 뜰 수 있음

---

## 7. SSL 발급 (Certbot / Let's Encrypt)

먼저 도메인 DNS가 서버 IP로 향해 있어야 합니다.
DNS 확인:
```bash
dig +short greatcar.kr
dig +short www.greatcar.kr
dig +short greatcar.co.kr
dig +short www.greatcar.co.kr
# 결과가 서버 공인 IP와 같아야 함
```

발급:
```bash
sudo certbot --nginx \
    -d greatcar.kr -d www.greatcar.kr \
    -d greatcar.co.kr -d www.greatcar.co.kr \
    --email admin@greatcar.kr \
    --agree-tos --no-eff-email --redirect
```

Certbot이 `greatcar.nginx` 를 자동으로 수정해서:
- `listen 443 ssl http2;` 라인 추가
- SSL 인증서 경로 삽입
- HTTP→HTTPS 리다이렉트 확실히 설정

자동 갱신 확인:
```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## 8. 최종 확인

브라우저에서:
- **https://greatcar.kr** → 200 OK, 사이트 노출
- **https://www.greatcar.kr** → 301 → `greatcar.kr`
- **https://greatcar.co.kr** → 301 → `greatcar.kr`
- **https://www.greatcar.co.kr** → 301 → `greatcar.kr`
- **https://greatcar.kr/admin** → 로그인 페이지

---

## 🔄 이후 코드 업데이트 배포

로컬에서 커밋·push한 뒤 서버에서:
```bash
cd /var/www/greatcar
git pull
source .venv/bin/activate

# 의존성 변경 시
pip install -r requirements.txt

# 마이그레이션 새 버전 있을 때
export FLASK_APP=run.py
flask db upgrade

# 재시작
sudo systemctl restart greatcar
```

---

## 🛠 문제 해결

**서비스 안 뜸**: `journalctl -u greatcar -n 50` 로그 확인
**502 Bad Gateway**: Gunicorn 안 뜬 것 → `systemctl status greatcar`
**정적 파일 404**: Nginx location `/static/` alias 경로 확인 (`/var/www/greatcar/app/static/`)
**DB 연결 실패**: `instance/.env` DB_USER/DB_PASSWORD 값 + MariaDB의 GRANT 확인
**업로드 실패 (권한)**: `chown -R www-data:www-data /var/www/greatcar/app/static/uploads`
**Kakao OAuth 실패**: Kakao Developers에 등록한 Redirect URI가 `https://greatcar.kr/auth/kakao/callback` 인지 확인

---

## 📌 카페24 특이사항

- 기존 3개 사이트(`ilioom`, `mynowship`, `rank1`) 함께 실행 중
- MariaDB 3306 공유 — 새 DB(`greatcar`) + 별도 유저(`greatcar_user`)로 격리
- Nginx도 공유 — sites-enabled 에 greatcar site 추가만
- 포트: **8002** (기존 8001·8080·8091 회피)
- 로그: `/var/log/greatcar/` (systemd unit 이 자동 생성)

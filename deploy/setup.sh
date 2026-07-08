#!/usr/bin/env bash
# =============================================================================
# Great Car — 초기 배포 스크립트
# 카페24 Ubuntu 서버 · Python 3.10 · MariaDB 10.6 · Nginx + Gunicorn
#
# 실행: /var/www/greatcar 에서
#   bash deploy/setup.sh
#
# 스크립트 실행 전 사용자가 준비할 것:
#   1) MariaDB에 DB · 유저 생성 (아래 SQL 참고)
#   2) instance/.env 값 채워넣기 (자동 생성되지만 SECRET_KEY / DB 비밀번호 확인 필요)
# =============================================================================
set -euo pipefail

PROJECT_DIR="/var/www/greatcar"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="python3"

cd "$PROJECT_DIR"

echo "=== [1/6] Python 확인 ==="
$PYTHON_BIN --version
if ! $PYTHON_BIN -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
  echo "Python 3.10 이상이 필요합니다." >&2
  exit 1
fi

echo ""
echo "=== [2/6] venv 생성 ==="
if [ ! -d "$VENV_DIR" ]; then
  $PYTHON_BIN -m venv "$VENV_DIR"
  echo "venv 생성 완료"
else
  echo "venv 이미 존재 — 재사용"
fi

echo ""
echo "=== [3/6] pip 의존성 설치 ==="
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo ""
echo "=== [4/6] 업로드 디렉토리 생성 + 권한 ==="
mkdir -p "$PROJECT_DIR/app/static/uploads/_tmp"
mkdir -p "$PROJECT_DIR/app/static/uploads/vehicles"
mkdir -p "$PROJECT_DIR/app/static/uploads/brands"
mkdir -p "$PROJECT_DIR/app/static/uploads/banners"
# Nginx (www-data) 가 정적 파일 서빙하고 Flask (예: root or greatcar user)가 씀
chown -R www-data:www-data "$PROJECT_DIR/app/static/uploads"
chmod -R 755 "$PROJECT_DIR/app/static/uploads"

echo ""
echo "=== [5/6] instance/.env 확인 ==="
if [ ! -f "$PROJECT_DIR/instance/.env" ]; then
  cp "$PROJECT_DIR/instance/.env.example" "$PROJECT_DIR/instance/.env"
  # SECRET_KEY 자동 생성
  RANDOM_KEY=$("$VENV_DIR/bin/python" -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$RANDOM_KEY|" "$PROJECT_DIR/instance/.env"
  # Prod 설정
  sed -i "s|^FLASK_ENV=.*|FLASK_ENV=production|" "$PROJECT_DIR/instance/.env"
  # Kakao redirect 도메인
  sed -i "s|^KAKAO_REDIRECT_URI=.*|KAKAO_REDIRECT_URI=https://greatcar.kr/auth/kakao/callback|" "$PROJECT_DIR/instance/.env"
  echo ""
  echo "  ⚠ instance/.env 방금 생성됨. 아래 값들 확인/수정하세요:"
  echo "     - DB_PASSWORD (MariaDB 유저 비밀번호)"
  echo "     - KAKAO_REST_API_KEY (카카오 앱 키, 나중에 채워도 됨)"
  echo "     - KAKAO_CHANNEL_URL (카카오 1:1 채널)"
  echo ""
  echo "  편집: nano $PROJECT_DIR/instance/.env"
  echo ""
  read -p "  값 채우신 뒤 Enter를 누르면 계속됩니다..." _
else
  echo "instance/.env 이미 존재 — 그대로 사용"
fi
chmod 600 "$PROJECT_DIR/instance/.env"

echo ""
echo "=== [6/6] DB 마이그레이션 ==="
export FLASK_APP=run.py
cd "$PROJECT_DIR"

# DB 연결 확인
if ! "$VENV_DIR/bin/python" -c "
from app import create_app
from app.extensions import db
from sqlalchemy import text
app = create_app()
with app.app_context():
    db.session.execute(text('SELECT 1'))
    print('DB 연결 OK')
" 2>/dev/null; then
  echo ""
  echo "  ✗ DB 연결 실패. MariaDB에 DB/유저를 먼저 만들어주세요:"
  echo ""
  cat <<'EOSQL'
  # MariaDB에 접속 후 실행:
  mysql -u root -p

  # SQL:
  CREATE DATABASE greatcar DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER 'greatcar_user'@'localhost' IDENTIFIED BY '설정한_비밀번호_넣기';
  GRANT ALL PRIVILEGES ON greatcar.* TO 'greatcar_user'@'localhost';
  FLUSH PRIVILEGES;
  EXIT;

  # 그 다음 instance/.env 에 DB_USER/DB_PASSWORD 채우고 이 스크립트 다시 실행
EOSQL
  exit 1
fi

"$VENV_DIR/bin/flask" db upgrade

echo ""
echo "==============================================="
echo "  ✓ 초기 배포 완료"
echo "==============================================="
echo ""
echo "다음 단계:"
echo ""
echo "  1) 어드민 계정 생성:"
echo "     cd $PROJECT_DIR"
echo "     source .venv/bin/activate"
echo "     export FLASK_APP=run.py"
echo "     flask create-admin"
echo ""
echo "  2) 시드 데이터 (선택):"
echo "     flask seed-brands"
echo "     flask seed-real   # 3대 샘플 차량 (나중에 어드민에서 삭제 가능)"
echo ""
echo "  3) systemd 서비스 등록:"
echo "     sudo cp deploy/greatcar.service /etc/systemd/system/"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable greatcar"
echo "     sudo systemctl start greatcar"
echo "     sudo systemctl status greatcar"
echo ""
echo "  4) Nginx 설정:"
echo "     sudo cp deploy/greatcar.nginx /etc/nginx/sites-available/greatcar"
echo "     sudo ln -sf /etc/nginx/sites-available/greatcar /etc/nginx/sites-enabled/greatcar"
echo "     sudo nginx -t"
echo "     sudo systemctl reload nginx"
echo ""
echo "  5) SSL 인증서 (Let's Encrypt):"
echo "     sudo certbot --nginx -d greatcar.kr -d www.greatcar.kr -d greatcar.co.kr -d www.greatcar.co.kr"
echo ""

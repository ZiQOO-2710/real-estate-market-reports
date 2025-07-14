#!/bin/bash
# Cloudflare WARP 저장소 문제 해결 스크립트

echo "🔧 WARP 저장소 문제 해결 중..."

# 1. 기존 문제 파일들 삭제
echo "📋 기존 파일들 삭제..."
sudo rm -f /etc/apt/sources.list.d/cloudflare-client.list
sudo rm -f /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

# 2. GPG 키 다시 다운로드 및 설치
echo "🔑 GPG 키 다시 설치..."
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

# 3. 저장소 파일 올바르게 생성
echo "📦 저장소 파일 생성..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ noble main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list

# 4. 권한 설정
echo "🔒 권한 설정..."
sudo chmod 644 /etc/apt/sources.list.d/cloudflare-client.list
sudo chmod 644 /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

# 5. 패키지 목록 업데이트
echo "🔄 패키지 목록 업데이트..."
sudo apt update

# 6. WARP 설치
echo "⬇️ Cloudflare WARP 설치..."
sudo apt install -y cloudflare-warp

echo "✅ 설치 완료!"
echo ""
echo "다음 명령어로 설정하세요:"
echo "warp-cli register"
echo "warp-cli connect"
echo "warp-cli status"
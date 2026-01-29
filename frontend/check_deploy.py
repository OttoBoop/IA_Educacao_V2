"""
Script para verificar versão do deploy
"""

from playwright.sync_api import sync_playwright
import requests

BASE_URL = "https://ia-educacao-v2.onrender.com"

def check_deploy():
    print("🔍 Verificando versão do deploy...\n")
    
    # Verificar se as imagens existem
    print("1. Verificando imagens do tutorial:")
    images = [
        "/static/tutorial-images/01-dashboard.png",
        "/static/tutorial-images/03-chat.png",
    ]
    
    for img_path in images:
        try:
            response = requests.head(f"{BASE_URL}{img_path}", timeout=10)
            status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
            print(f"   {img_path}: {status}")
        except Exception as e:
            print(f"   {img_path}: ❌ ({e})")
    
    # Verificar tamanho do HTML
    print("\n2. Verificando tamanho do HTML:")
    try:
        response = requests.get(BASE_URL, timeout=30)
        size = len(response.text)
        print(f"   Tamanho do HTML: {size} bytes")
        
        # O HTML com tutorial deve ter mais de 200KB
        if size > 200000:
            print("   ✅ Parece ser a versão nova (> 200KB)")
        else:
            print("   ⚠️ Pode ser a versão antiga (< 200KB)")
            
        # Verificar conteúdo específico
        if "modal-welcome" in response.text:
            print("   ✅ Contém modal-welcome")
        else:
            print("   ❌ Não contém modal-welcome")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n3. Verificando API de status:")
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=10)
        print(f"   Status API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Resposta: {data}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    check_deploy()

# 1. Atualizar o sistema e instalar dependências
pkg update && pkg upgrade -y
pip install telethon

# 2. Clonar o repositório
git clone https://github.com/AMHEEX/TLM-PY-BOT.git

# 3. Entrar na pasta do projeto e executar
cd TLM-PY-BOT
python index.py

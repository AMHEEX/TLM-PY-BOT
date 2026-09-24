import asyncio
import random
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import (
    UserStatusOnline, 
    UserStatusRecently, 
    UserStatusLastWeek, 
    UserStatusOffline
)

# ================= CONFIGURAÇÕES =================
api_id = 38325876
api_hash = '4159d8f4d17c6929d05416871d36ce18'
phone = '+5546999020341'

grupo_origem = 'https://t.me/rendaextrajaaa'
grupo_destino = 'https://t.me/AcountMoney'

LIMITE =  # Para exatamente ao bater 100 pessoas adicionadas

# Lista de tempos em segundos: 30s, 1m, 2m, 2m, 4m, 5m
# TEMPOS_ESPERA = [30, 60, 120, 120, 240, 300] 
TEMPOS_ESPERA = [60, 120] 

# =================================================

# Função para verificar se a pessoa esteve online nos últimos 7 dias
def esteve_online_7_dias(membro):
    if not hasattr(membro, 'status') or membro.status is None:
        return False
        
    status = membro.status
    
    # Se está online agora, esteve recentemente (1 a 3 dias) ou na última semana (3 a 7 dias)
    if isinstance(status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
        return True
        
    # Se tem a data exata da última vez online, calcula se faz menos de 7 dias
    elif isinstance(status, UserStatusOffline):
        agora = datetime.now(timezone.utc)
        sete_dias_atras = agora - timedelta(days=7)
        if status.was_online >= sete_dias_atras:
            return True
            
    return False

async def main():
    client = TelegramClient('sessao', api_id, api_hash)
    await client.start(phone=phone)
    print("✅ Conectado ao Telegram!")
    
    origem = await client.get_entity(grupo_origem)
    destino = await client.get_entity(grupo_destino)
    
    # 1. Buscar membros já no destino
    print("🔍 Analisando quem já está no grupo de destino...")
    membros_destino = set()
    async for membro in client.iter_participants(destino):
        membros_destino.add(membro.id)
    print(f"📋 Membros já no destino: {len(membros_destino)}")

    # 2. Buscar TODOS os membros do grupo de origem
    print("📥 Buscando membros do grupo de origem...")
    membros_origem = []
    async for membro in client.iter_participants(origem):
        membros_origem.append(membro)
    print(f"📋 Total de membros na origem: {len(membros_origem)}")
    
    # 3. Adicionar membros filtrados
    print("\n🚀 Iniciando as adições...\n")
    adicionados = 0
    
    for membro in membros_origem:
        # Para imediatamente se atingir 100 adicionados
        if adicionados >= LIMITE:
            print(f"\n✅ META ATINGIDA: {LIMITE} pessoas foram adicionadas com sucesso!")
            break

        # Regra 1: Pular se já estiver no grupo de destino
        if membro.id in membros_destino:
            continue
            
        # Regra 2: Pular bots ou contas excluídas
        if membro.bot or getattr(membro, 'deleted', False):
            continue
            
        # Regra 3: Adicionar SÓ quem esteve online nos últimos 7 dias
        if not esteve_online_7_dias(membro):
            print(f"⏭️ Pulando {membro.first_name or membro.id} (Inativo há mais de 7 dias)")
            continue
        
        try:
            # Tenta adicionar o usuário
            await client(InviteToChannelRequest(
                channel=destino,
                users=[membro.id]
            ))
            
            adicionados += 1
            membros_destino.add(membro.id)
            print(f"✅ Adicionado ({adicionados}/{LIMITE}): {membro.first_name or membro.id}")
            
            # Pausa com tempo variável (apenas se ainda não bateu o limite)
            if adicionados < LIMITE:
                tempo_pausa = random.choice(TEMPOS_ESPERA)
                minutos = tempo_pausa // 60
                segundos = tempo_pausa % 60
                print(f"⏳ Aguardando {minutos}m e {segundos}s para disfarçar o robô...")
                await asyncio.sleep(tempo_pausa)
                
        except FloodWaitError as e:
            print(f"⚠️ O Telegram pediu para esperar: {e.seconds} segundos (Limite de SPAM).")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            # Muitos usuários bloqueiam quem pode adicioná-los, esse erro cai aqui
            print(f"❌ Não foi possível adicionar {membro.first_name or membro.id} (Privacidade ou Erro)")
            await asyncio.sleep(5) # Pausa curta após um erro
    
    print(f"\n🏁 Processo Finalizado! Total real de adicionados hoje: {adicionados}.")

with asyncio.Runner() as runner:
    runner.run(main())

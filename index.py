import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
import time

# CONFIGURAÇÕES
api_id = 38325876
api_hash = '4159d8f4d17c6929d05416871d36ce18'
phone = '+5546999250673'

grupo_origem = '@osprogramadores'
grupo_destino = '@AcountMoney'

LIMITE = 250
TEMPO_ESPERA = 70

async def main():
    client = TelegramClient('sessao', api_id, api_hash)
    await client.start(phone=phone)
    print("✅ Conectado!")
    
    origem = await client.get_entity(grupo_origem)
    destino = await client.get_entity(grupo_destino)
    
    # Buscar TODOS os membros do grupo de origem
    print("📥 Buscando membros do grupo de origem...")
    membros_origem = []
    async for membro in client.iter_participants(origem):
        membros_origem.append(membro)
    
    print(f"📋 Total de membros na origem: {len(membros_origem)}")
    
    # Buscar membros já no destino
    print("🔍 Verificando membros já no destino...")
    membros_destino = set()
    async for membro in client.iter_participants(destino):
        membros_destino.add(membro.id)
    
    print(f"📋 Membros já no destino: {len(membros_destino)}")
    
    # Adicionar apenas quem não está no destino
    adicionados = 0
    for membro in membros_origem:
        if membro.id in membros_destino:
            print(f"⏭️ Pulando {membro.first_name or membro.id} (já está no destino)")
            continue
        
        if adicionados >= LIMITE:
            print(f"✅ Limite de {LIMITE} atingido!")
            break
        
        try:
            await client(InviteToChannelRequest(
                channel=destino,
                users=[membro.id]
            ))
            print(f"✅ Adicionado: {membro.first_name or membro.id}")
            adicionados += 1
            membros_destino.add(membro.id)
            
            # Espera entre adições
            if adicionados < LIMITE:
                print(f"⏳ Aguardando {TEMPO_ESPERA} segundos...")
                await asyncio.sleep(TEMPO_ESPERA)
                
        except FloodWaitError as e:
            print(f"⚠️ Flood wait: {e.seconds} segundos")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Erro ao adicionar {membro.first_name or membro.id}: {e}")
            await asyncio.sleep(5)
    
    print(f"\n🏁 Finalizado! {adicionados} membros adicionados.")

with asyncio.Runner() as runner:
    runner.run(main())
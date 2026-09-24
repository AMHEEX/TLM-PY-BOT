import asyncio
import random
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import (
    UserStatusOnline, 
    UserStatusRecently, 
    UserStatusLastWeek, 
    UserStatusOffline
)

# ================= CONFIGURAÇÕES TELEGRAM =================
api_id = 38325876
api_hash = '4159d8f4d17c6929d05416871d36ce18'

# Valores Padrão (utilizados caso o usuário dê ENTER sem digitar)
PHONE_PADRAO = '+5546999020341'
GRUPO_ORIGEM_PADRAO = 'https://t.me/rendaextrajaaa'
GRUPO_DESTINO_PADRAO = 'https://t.me/AcountMoney'
# ==========================================================

def esteve_online_7_dias(membro):
    if not hasattr(membro, 'status') or membro.status is None:
        return False
        
    status = membro.status
    
    if isinstance(status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
        return True
        
    elif isinstance(status, UserStatusOffline):
        agora = datetime.now(timezone.utc)
        sete_dias_atras = agora - timedelta(days=7)
        if hasattr(status, 'was_online') and status.was_online >= sete_dias_atras:
            return True
            
    return False

def calcular_tempo_ate_meia_noite():
    agora = datetime.now()
    amanha = agora.date() + timedelta(days=1)
    meia_noite = datetime.combine(amanha, datetime.min.time())
    
    diferenca = (meia_noite - agora).total_seconds()
    return max(diferenca, 0)

def obter_configuracoes_usuario():
    print("⚙️  === CONFIGURAÇÃO DE ADIÇÃO AUTOMÁTICA ===")
    
    # 1. Perguntar Número de Telefone
    print("\n📱 --- CONTA TELEGRAM ---")
    phone = input(f"👉 Número de telefone com DDD/País [Padrão: {PHONE_PADRAO}]: ").strip() or PHONE_PADRAO

    # 2. Perguntar URLs dos Grupos
    print("\n🔗 --- CONFIGURAÇÃO DOS GRUPOS ---")
    url_origem = input(f"👉 Link/Username do grupo de ORIGEM [Padrão: {GRUPO_ORIGEM_PADRAO}]: ").strip() or GRUPO_ORIGEM_PADRAO
    url_destino = input(f"👉 Link/Username do grupo de DESTINO [Padrão: {GRUPO_DESTINO_PADRAO}]: ").strip() or GRUPO_DESTINO_PADRAO

    # 3. Obter tempo restante no dia atual
    segundos_restantes_dia = calcular_tempo_ate_meia_noite()
    horas_restantes = int(segundos_restantes_dia // 3600)
    minutos_restantes = int((segundos_restantes_dia % 3600) // 60)
    
    print("\n⏰ --- PLANEJAMENTO DE TEMPO ---")
    print(f"• Horário Atual: {datetime.now().strftime('%H:%M:%S')}")
    print(f"• Tempo até meia-noite (00:00): {horas_restantes}h {minutos_restantes}min ({int(segundos_restantes_dia)}s)")
    
    # 4. Perguntar quantas pessoas deseja adicionar no dia
    while True:
        try:
            limite = int(input("\n👉 Quantas pessoas deseja adicionar até o final do dia (00:00)? "))
            if limite > 0:
                break
            print("❌ Digite um número maior que 0.")
        except ValueError:
            print("❌ Digite um número inteiro válido.")

    # 5. Intervalo mínimo de segurança
    while True:
        try:
            min_seg = int(input("👉 Qual o tempo mínimo de segurança (em segundos) por pessoa? [Padrão: 60]: ") or "60")
            if min_seg >= 10:
                break
            print("⚠️ Digite pelo menos 10 segundos para proteção da conta.")
        except ValueError:
            print("❌ Digite um número inteiro válido.")

    # 6. Cálculo do intervalo automático
    tempo_base = segundos_restantes_dia / limite

    print("\n📊 === RESUMO DA OPERAÇÃO ===")
    print(f"• Telefone da conta: {phone}")
    print(f"• Origem: {url_origem}")
    print(f"• Destino: {url_destino}")
    print(f"• Meta: {limite} pessoas")
    print(f"• Período útil restante: {horas_restantes}h {minutos_restantes}min")
    
    h_base = int(tempo_base // 3600)
    m_base = int((tempo_base % 3600) // 60)
    s_base = int(tempo_base % 60)
    
    print(f"• Intervalo automático estimado: ~{h_base}h {m_base}m {s_base}s ({int(tempo_base)}s)")

    if tempo_base < min_seg:
        print(f"\n⚠️ AVISO: O tempo até meia-noite não é suficiente para adicionar {limite} pessoas com intervalo de {min_seg}s.")
        print(f"   O script ajustará a pausa para o mínimo configurado de {min_seg}s.")
        tempo_base = min_seg

    input("\nPressione ENTER para iniciar o robô...")
    return phone, url_origem, url_destino, limite, tempo_base, min_seg

async def main():
    phone, grupo_origem, grupo_destino, limite_meta, tempo_base_espera, tempo_minimo_espera = obter_configuracoes_usuario()

    # Cria nome de sessão dinâmico baseado nos números do telefone para evitar conflito
    session_name = f'sessao_{phone.replace("+", "").replace(" ", "")}'
    client = TelegramClient(session_name, api_id, api_hash)
    
    await client.start(phone=phone)
    print("\n✅ Conectado ao Telegram!")
    
    try:
        origem = await client.get_entity(grupo_origem)
        destino = await client.get_entity(grupo_destino)
    except Exception as e:
        print(f"❌ Erro ao localizar os grupos fornecidos: {e}")
        return
    
    # 1. Verificar quem já está no destino
    print("\n🔍 [1/3] Mapeando membros que já estão no grupo de destino...")
    membros_destino_ids = set()
    async for membro in client.iter_participants(destino):
        membros_destino_ids.add(membro.id)
    print(f"📋 {len(membros_destino_ids)} membros já existem no destino e serão ignorados.")

    # 2. Obter membros válidos da origem
    print("\n📥 [2/3] Buscando e filtrando membros da origem...")
    membros_para_adicionar = []
    
    async for membro in client.iter_participants(origem):
        if membro.id in membros_destino_ids:
            continue
            
        if membro.bot or getattr(membro, 'deleted', False):
            continue
            
        if esteve_online_7_dias(membro):
            membros_para_adicionar.append(membro)

    print(f"🎯 Total de candidatos ativos nos últimos 7 dias: {len(membros_para_adicionar)}")
    print("\n🚀 [3/3] Iniciando o ciclo de adição...\n")
    
    adicionados = 0

    # 3. Adicionar membros com pausa dinâmica
    for membro in membros_para_adicionar:
        if adicionados >= limite_meta:
            print(f"\n✅ META ATINGIDA: {limite_meta} pessoas foram adicionadas com sucesso!")
            break

        nome_exibicao = membro.first_name or f"ID:{membro.id}"
        
        try:
            await client(InviteToChannelRequest(
                channel=destino,
                users=[membro]
            ))
            
            adicionados += 1
            membros_destino_ids.add(membro.id)
            print(f"✅ Adicionado ({adicionados}/{limite_meta}): {nome_exibicao}")
            
            if adicionados < limite_meta:
                variacao = tempo_base_espera * 0.1
                tempo_pausa = random.uniform(tempo_base_espera - variacao, tempo_base_espera + variacao)
                tempo_pausa = max(tempo_pausa, tempo_minimo_espera)
                
                horas = int(tempo_pausa // 3600)
                minutos = int((tempo_pausa % 3600) // 60)
                segundos = int(tempo_pausa % 60)
                
                print(f"⏳ Próxima adição em: {horas}h {minutos}m {segundos}s...")
                await asyncio.sleep(tempo_pausa)
                
        except UserPrivacyRestrictedError:
            print(f"🔒 {nome_exibicao} bloqueia convites por privacidade.")
            await asyncio.sleep(5)
        except FloodWaitError as e:
            print(f"⚠️ Telegram pediu pausa por limite de ações: {e.seconds} segundos.")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            print(f"❌ Erro ao adicionar {nome_exibicao}: {e}")
            await asyncio.sleep(10)

    print(f"\n🏁 Processo Finalizado! Total de adicionados hoje: {adicionados}.")

if __name__ == '__main__':
    asyncio.run(main())

"""
Assistente interativo em linha de comando para configurar os alertas de monitoramento.
Permite ativar/desativar canais como E-mail, Telegram, ntfy (celular), Discord e WhatsApp.
"""

import os
import sys
import json
from notifiers import NotificationDispatcher

CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists("config_default.json"):
        with open("config_default.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("\n[OK] Configurações salvas com sucesso em 'config.json'!\n")


def print_header():
    print("=" * 65)
    print("      CONFIGURADOR DO MONITOR - INSTITUTO AVALIA")
    print("=" * 65)


def show_status(cfg):
    print("\nStatus atual dos canais:")
    print(f"  [1] Notificação Windows + Alarme Sonoro : {'[ATIVADO]' if cfg.get('windows', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [2] Push no Celular (ntfy.sh - Sem cadastro) : {'[ATIVADO] Topico: ' + str(cfg.get('ntfy', {}).get('topic')) if cfg.get('ntfy', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [3] E-mail (SMTP - Gmail/Outlook)     : {'[ATIVADO] Para: ' + str(cfg.get('email', {}).get('to_email')) if cfg.get('email', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [4] Telegram Bot                       : {'[ATIVADO]' if cfg.get('telegram', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [5] Discord Webhook                    : {'[ATIVADO]' if cfg.get('discord', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [6] WhatsApp (CallMeBot)               : {'[ATIVADO]' if cfg.get('whatsapp', {}).get('enabled') else '[DESATIVADO]'}")
    print(f"  [7] Intervalo de checagem             : {cfg.get('interval_seconds', 60)} segundos")
    print("=" * 65)


def configure_ntfy(cfg):
    print("\n--- CONFIGURAÇÃO NTFY.SH (Push no Celular / Navegador) ---")
    print("O ntfy.sh é 100% gratuito e não exige cadastro nem cartão.")
    print("Basta escolher um nome único para o seu tópico.")
    print("Você pode instalar o app 'ntfy' no Android/iOS ou abrir no navegador:")
    print("  Exemplo: https://ntfy.sh/meu_concurso_avalia_123\n")

    current = cfg.get("ntfy", {}).get("topic", "avalia_concurso_619_alerta")
    topic = input(f"Digite o nome do tópico desejado [atual: {current}]: ").strip() or current
    
    cfg.setdefault("ntfy", {})["enabled"] = True
    cfg["ntfy"]["topic"] = topic
    cfg["ntfy"]["priority"] = "urgent"
    print(f"\n[OK] ntfy ativado no tópico: {topic}")
    print(f"-> Abra no seu celular: https://ntfy.sh/{topic} e clique em 'Inscrever-se' (Subscribe) para receber alertas!")


def configure_email(cfg):
    print("\n--- CONFIGURAÇÃO DE E-MAIL (SMTP) ---")
    print("DICA: Para o Gmail, gere uma 'Senha de App' em sua conta Google")
    print("      (Segurança -> Verificação em 2 etapas -> Senhas de app).")
    print("      Nunca utilize a sua senha principal se a conta tiver 2FA ativado.\n")

    cfg.setdefault("email", {})
    host = input(f"Servidor SMTP [padrão: {cfg['email'].get('smtp_host', 'smtp.gmail.com')}]: ").strip() or cfg['email'].get('smtp_host', 'smtp.gmail.com')
    port = input(f"Porta SMTP [padrão: {cfg['email'].get('smtp_port', 587)}]: ").strip() or str(cfg['email'].get('smtp_port', 587))
    user = input(f"Seu E-mail remetente [atual: {cfg['email'].get('smtp_user', '')}]: ").strip() or cfg['email'].get('smtp_user', '')
    pwd = input(f"Senha de App do E-mail [deixe vazio para manter atual]: ").strip() or cfg['email'].get('smtp_pass', '')
    to = input(f"E-mail de destino (onde vai receber o alerta) [atual: {cfg['email'].get('to_email', '')}]: ").strip() or cfg['email'].get('to_email', '')

    cfg["email"]["enabled"] = True
    cfg["email"]["smtp_host"] = host
    cfg["email"]["smtp_port"] = int(port)
    cfg["email"]["smtp_user"] = user
    cfg["email"]["smtp_pass"] = pwd
    cfg["email"]["from_email"] = user
    cfg["email"]["to_email"] = to
    cfg["email"]["use_tls"] = True
    print("\n[OK] E-mail configurado e ativado!")


def configure_telegram(cfg):
    print("\n--- CONFIGURAÇÃO DO TELEGRAM ---")
    print("1. Abra o Telegram e procure por @BotFather para criar um bot (/newbot).")
    print("2. Copie o TOKEN HTTP API gerado.")
    print("3. Procure pelo bot @userinfobot ou envie uma mensagem para o seu novo bot para saber seu Chat ID.\n")

    cfg.setdefault("telegram", {})
    token = input(f"Bot Token [atual: {cfg['telegram'].get('bot_token', '')}]: ").strip() or cfg['telegram'].get('bot_token', '')
    chat_id = input(f"Chat ID do seu usuário ou canal [atual: {cfg['telegram'].get('chat_id', '')}]: ").strip() or cfg['telegram'].get('chat_id', '')

    cfg["telegram"]["enabled"] = bool(token and chat_id)
    cfg["telegram"]["bot_token"] = token
    cfg["telegram"]["chat_id"] = chat_id
    print("\n[OK] Telegram configurado e ativado!")


def configure_discord(cfg):
    print("\n--- CONFIGURAÇÃO DO DISCORD ---")
    print("No seu servidor do Discord, clique com botão direito no canal -> Editar Canal -> Integrações -> Criar Webhook.")
    cfg.setdefault("discord", {})
    url = input(f"URL do Webhook do Discord: ").strip() or cfg["discord"].get("webhook_url", "")
    cfg["discord"]["enabled"] = bool(url)
    cfg["discord"]["webhook_url"] = url
    print("\n[OK] Discord configurado!")


def configure_whatsapp(cfg):
    print("\n--- CONFIGURAÇÃO DO WHATSAPP (CallMeBot) ---")
    print("1. Salve o número +34 911 06 48 59 no seu WhatsApp.")
    print("2. Envie a mensagem: 'I allow callmebot to send me messages'")
    print("3. Aguarde a mensagem com a sua API Key.\n")
    cfg.setdefault("whatsapp", {})
    phone = input(f"Seu número com DDI e DDD (ex: +5511999999999): ").strip() or cfg["whatsapp"].get("phone", "")
    apikey = input(f"API Key recebida: ").strip() or cfg["whatsapp"].get("apikey", "")
    cfg["whatsapp"]["enabled"] = bool(phone and apikey)
    cfg["whatsapp"]["phone"] = phone
    cfg["whatsapp"]["apikey"] = apikey
    print("\n[OK] WhatsApp configurado!")


def configure_interval(cfg):
    print("\n--- INTERVALO DE VERIFICAÇÃO ---")
    print("Recomendado: 45 a 120 segundos para não sobrecarregar o servidor e ter aviso quase imediato.")
    val = input(f"Segundos entre cada consulta [atual: {cfg.get('interval_seconds', 60)}]: ").strip()
    if val.isdigit():
        cfg["interval_seconds"] = max(15, int(val))
        print(f"[OK] Intervalo ajustado para {cfg['interval_seconds']} segundos.")


def test_notifications(cfg):
    print("\n--- ENVIANDO NOTIFICAÇÃO DE TESTE ---")
    dispatcher = NotificationDispatcher(cfg)
    test_title = "TESTE - Monitor Instituto Avalia"
    test_msg = "Se você está vendo esta mensagem, seu canal de alerta está funcionando 100%!"
    test_url = f"https://www.avalia.org.br/concursos/{cfg.get('concurso_id', 619)}"
    results = dispatcher.send_all(test_title, test_msg, test_url, {"concurso_nome": cfg.get("nome_amigavel", "Concurso 619")})
    print("\nResultado dos disparos:")
    for ch, success in results.items():
        status_txt = "Sucesso" if success else "Falhou ou Desativado"
        print(f" - {ch.upper()}: {status_txt}")
    print("\nVerifique seu celular, e-mail ou tela para confirmar o recebimento!")


def main():
    cfg = load_config()
    while True:
        print_header()
        show_status(cfg)
        print("Opções:")
        print("  1 - Configurar Windows (Som e Pop-up)")
        print("  2 - Configurar Push no Celular (ntfy.sh - Recomendado, mais rápido)")
        print("  3 - Configurar E-mail (Gmail / Outlook)")
        print("  4 - Configurar Telegram Bot")
        print("  5 - Configurar Discord Webhook")
        print("  6 - Configurar WhatsApp (CallMeBot)")
        print("  7 - Ajustar intervalo de checagem")
        print("  T - TESTAR canais agora (disparar notificação teste)")
        print("  S - Salvar e Sair")
        print("  Q - Sair sem salvar")
        
        choice = input("\nEscolha uma opção: ").strip().lower()

        if choice == "1":
            cur = cfg.get("windows", {}).get("enabled", True)
            cfg.setdefault("windows", {})["enabled"] = not cur
            print(f"Windows Notificações agora está: {'[ATIVADO]' if not cur else '[DESATIVADO]'}")
        elif choice == "2":
            configure_ntfy(cfg)
        elif choice == "3":
            configure_email(cfg)
        elif choice == "4":
            configure_telegram(cfg)
        elif choice == "5":
            configure_discord(cfg)
        elif choice == "6":
            configure_whatsapp(cfg)
        elif choice == "7":
            configure_interval(cfg)
        elif choice == "t":
            test_notifications(cfg)
        elif choice == "s":
            save_config(cfg)
            break
        elif choice == "q":
            print("Saindo sem salvar.")
            break
        else:
            print("[!] Opção inválida.")
        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    main()


"""
Monitor de Publicações do Instituto Avalia
Site Oficial: https://www.avalia.org.br/concursos/619

Monitora periodicamente a página e API do Instituto Avalia e notifica
imediatamente via Celular (ntfy.sh), E-mail, Telegram, Discord, WhatsApp
e Alarme Sonoro no Windows assim que uma nova publicação for lançada.
"""

import os
import sys
import json
import time
import random
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Garantir UTF-8 no console do Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from avalia_api import get_concurso_info
from notifiers import NotificationDispatcher

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists("config_default.json"):
        with open("config_default.json", "r", encoding="utf-8") as f:
            return json.load(f)
    # Padrão
    return {
        "concurso_id": 619,
        "interval_seconds": 60,
        "random_delay_jitter": 10,
        "windows": {"enabled": True, "play_sound": True},
        "ntfy": {"enabled": True, "topic": "avalia_concurso_619_alerta", "priority": "urgent"}
    }


def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Aviso] Erro ao ler {STATE_FILE}, recriando: {e}")
    return {
        "concurso_id": 619,
        "known_publicacoes": [],
        "known_links": [],
        "history": [],
        "last_checked": None
    }


def save_state(state: Dict[str, Any]):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Erro] Falha ao salvar estado: {e}")


def format_timestamp() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def print_banner(concurso_id: int, nome_amigavel: str, interval: int, cfg: Dict[str, Any]):
    print("=" * 72)
    print("      🚀 MONITOR DE PUBLICAÇÕES - INSTITUTO AVALIA 🚀")
    print(f"  Alvo: Concurso {concurso_id} ({nome_amigavel})")
    print(f"  URL:  https://www.avalia.org.br/concursos/{concurso_id}")
    print(f"  Checagem: a cada ~{interval} segundos")
    print("-" * 72)
    print("  Canais de alerta ativados:")
    if cfg.get("windows", {}).get("enabled"):
        som = "com alarme sonoro" if cfg.get("windows", {}).get("play_sound") else "sem som"
        print(f"   [x] Windows Desktop ({som})")
    if cfg.get("ntfy", {}).get("enabled"):
        topico = cfg.get("ntfy", {}).get("topic")
        print(f"   [x] Celular / Web via ntfy.sh (Tópico: {topico})")
        print(f"       -> Acesse no celular: https://ntfy.sh/{topico}")
    if cfg.get("email", {}).get("enabled"):
        print(f"   [x] E-mail SMTP (Destino: {cfg.get('email', {}).get('to_email')})")
    if cfg.get("telegram", {}).get("enabled"):
        print(f"   [x] Telegram Bot (Chat ID: {cfg.get('telegram', {}).get('chat_id')})")
    if cfg.get("discord", {}).get("enabled"):
        print(f"   [x] Discord Webhook")
    if cfg.get("whatsapp", {}).get("enabled"):
        print(f"   [x] WhatsApp CallMeBot ({cfg.get('whatsapp', {}).get('phone')})")
    print("=" * 72)
    print("Pressione Ctrl + C para encerrar a qualquer momento.\n")


def notify_new_publication(dispatcher: NotificationDispatcher, pub: Dict[str, Any], concurso_info: Dict[str, Any]):
    titulo = pub.get("nome", "Nova Publicação Sem Título")
    url = pub.get("url", concurso_info.get("url_pagina", ""))
    pub_id = pub.get("id", "N/A")
    concurso_nome = concurso_info.get("nome", "Instituto Avalia")

    msg_title = f"NOVA PUBLICAÇÃO! {concurso_info.get('edital', 'Concurso').upper()}"
    msg_body = (
        f"Acaba de ser divulgada uma nova publicação no site do Instituto Avalia!\n\n"
        f"📄 Publicação: {titulo}\n"
        f"🏛 Concurso: {concurso_nome}\n"
        f"⏰ Horário da detecção: {format_timestamp()}\n"
    )

    print("\n" + "#" * 72)
    print(f"🚨 [ALERTA MÁXIMO] NOVA PUBLICAÇÃO DETECTADA! ID: {pub_id}")
    print(f"Título: {titulo}")
    print(f"Link:   {url}")
    print("#" * 72 + "\n")

    # Disparar alertas
    results = dispatcher.send_all(
        title=msg_title,
        message=msg_body,
        url=url,
        extra_data={
            "concurso_nome": concurso_nome,
            "pub_id": pub_id,
            "pub_nome": titulo,
            "pub_url": url,
            "concurso_id": concurso_info.get("concurso_id")
        }
    )
    return results


def notify_new_link(dispatcher: NotificationDispatcher, link_item: Dict[str, Any], concurso_info: Dict[str, Any]):
    nome = link_item.get("nome", "Novo Link/Sistema")
    url = link_item.get("url", concurso_info.get("url_pagina", ""))
    categoria = link_item.get("categoria", "Geral")
    concurso_nome = concurso_info.get("nome", "Instituto Avalia")

    msg_title = f"NOVO LINK / SISTEMA DISPONÍVEL! ({categoria})"
    msg_body = (
        f"Um novo link de acompanhamento foi adicionado na página do concurso:\n\n"
        f"🔗 Nome: {nome}\n"
        f"📁 Categoria: {categoria}\n"
        f"🏛 Concurso: {concurso_nome}\n"
        f"⏰ Horário: {format_timestamp()}\n"
    )

    print("\n" + "*" * 72)
    print(f"📢 [NOVIDADE] NOVO LINK/SISTEMA ADICIONADO: {nome}")
    print(f"URL: {url}")
    print("*" * 72 + "\n")

    dispatcher.send_all(
        title=msg_title,
        message=msg_body,
        url=url,
        extra_data={"concurso_nome": concurso_nome, "link_nome": nome, "link_url": url}
    )


def run_monitor(args):
    config = load_config()

    concurso_id = args.concurso or config.get("concurso_id", 619)
    interval = args.interval or config.get("interval_seconds", 60)
    jitter = config.get("random_delay_jitter", 10)
    nome_amigavel = config.get("nome_amigavel", f"Concurso {concurso_id}")

    dispatcher = NotificationDispatcher(config)

    # Modo Teste: envia uma notificação teste e encerra
    if args.test:
        print("\n[MODO TESTE] Enviando notificação teste para todos os canais ativados...")
        test_url = f"https://www.avalia.org.br/concursos/{concurso_id}"
        results = dispatcher.send_all(
            title="TESTE DE FUNCIONAMENTO - MONITOR AVALIA",
            message=f"Teste do monitor para o Concurso {concurso_id} ({nome_amigavel}).\nSeu sistema de alerta está configurado e operante!",
            url=test_url,
            extra_data={"concurso_nome": nome_amigavel}
        )
        print("\nResultado dos disparos:")
        for ch, status in results.items():
            print(f" - {ch.upper()}: {'Sucesso' if status else 'Falha / Não configurado'}")
        print("\nVerifique se recebeu o alerta no seu dispositivo!")
        return

    state = load_state()
    if args.reset_state:
        print("[AVISO] Resetando estado salvo...")
        state = {"concurso_id": concurso_id, "known_publicacoes": [], "known_links": [], "history": []}

    print_banner(concurso_id, nome_amigavel, interval, config)

    # Verificação inicial para registrar baseline se não houver
    first_run = len(state.get("known_publicacoes", [])) == 0

    cycle = 0
    while True:
        cycle += 1
        now_str = format_timestamp()

        try:
            concurso_info = get_concurso_info(concurso_id)
            publicacoes = concurso_info.get("publicacoes", [])
            links = concurso_info.get("links", [])

            # Conjunto de IDs conhecidos
            known_pub_ids = set(state.get("known_publicacoes", []))
            known_link_ids = set(state.get("known_links", []))

            if first_run:
                # Primeira execução: aprende todos os já existentes sem disparar alertas
                for p in publicacoes:
                    p_id = p.get("id") or p.get("url")
                    if p_id:
                        known_pub_ids.add(p_id)

                for l in links:
                    l_id = l.get("identificador") or l.get("url") or l.get("nome")
                    if l_id:
                        known_link_ids.add(l_id)

                state["concurso_id"] = concurso_id
                state["known_publicacoes"] = list(known_pub_ids)
                state["known_links"] = list(known_link_ids)
                state["last_checked"] = now_str
                save_state(state)
                first_run = False

                print(f"[{now_str}] [BASE ESTABELECIDA] {len(publicacoes)} publicações e {len(links)} links registrados como conhecidos.")
                print(f"[{now_str}] Monitoramento ativo! Aguardando novos lançamentos...\n")
            else:
                # Checagem de novas publicações
                novas_pubs = []
                for p in publicacoes:
                    p_id = p.get("id") or p.get("url")
                    if p_id and p_id not in known_pub_ids:
                        novas_pubs.append(p)

                # Checagem de novos links
                novos_links = []
                for l in links:
                    l_id = l.get("identificador") or l.get("url") or l.get("nome")
                    if l_id and l_id not in known_link_ids:
                        novos_links.append(l)

                if novas_pubs:
                    print(f"\n[{now_str}] ATENÇÃO: {len(novas_pubs)} NOVA(S) PUBLICAÇÃO(ÕES) ENCONTRADA(S)!")
                    for p in novas_pubs:
                        notify_new_publication(dispatcher, p, concurso_info)
                        p_id = p.get("id") or p.get("url")
                        known_pub_ids.add(p_id)
                        state.setdefault("history", []).append({
                            "type": "publicacao",
                            "item": p,
                            "detected_at": now_str
                        })

                if novos_links:
                    print(f"\n[{now_str}] ATENÇÃO: {len(novos_links)} NOVO(S) LINK(S) ENCONTRADO(S)!")
                    for l in novos_links:
                        notify_new_link(dispatcher, l, concurso_info)
                        l_id = l.get("identificador") or l.get("url") or l.get("nome")
                        known_link_ids.add(l_id)
                        state.setdefault("history", []).append({
                            "type": "link",
                            "item": l,
                            "detected_at": now_str
                        })

                if not novas_pubs and not novos_links:
                    print(f"[{now_str}] [Checagem #{cycle}] Nenhuma novidade. Total: {len(publicacoes)} pubs, {len(links)} links. Próxima em ~{interval}s...")

                state["known_publicacoes"] = list(known_pub_ids)
                state["known_links"] = list(known_link_ids)
                state["last_checked"] = now_str
                save_state(state)

        except Exception as e:
            print(f"[{now_str}] [Aviso] Falha momentânea ao consultar o Instituto Avalia: {e}")
            print("  -> Não se preocupe, o monitor continuará tentando no próximo ciclo.")

        if args.once:
            print("\nExecução única (--once) concluída.")
            break

        # Esperar com pequeno jitter aleatório
        sleep_time = interval + random.uniform(0, jitter)
        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n[Encerrado pelo usuário] Monitor finalizado. Até logo!")
            break


def main():
    parser = argparse.ArgumentParser(description="Monitor de Publicações do Instituto Avalia")
    parser.add_argument("--test", action="store_true", help="Dispara notificação de teste em todos os canais e encerra")
    parser.add_argument("--once", action="store_true", help="Executa apenas uma verificação e encerra")
    parser.add_argument("--reset-state", action="store_true", help="Apaga o histórico local e recria a base")
    parser.add_argument("--interval", type=int, help="Intervalo em segundos entre verificações")
    parser.add_argument("--concurso", type=int, help="ID do concurso a ser monitorado (padrão: 619)")
    args = parser.parse_args()

    run_monitor(args)


if __name__ == "__main__":
    main()


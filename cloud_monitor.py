"""
Monitor de Publicações do Instituto Avalia - Versão Nuvem (GitHub Actions / Cloud)
Executa verificações contínuas e envia alertas para ntfy.sh, Telegram, E-mail, etc.
Otimizado para rodar em servidores Linux / contêineres na nuvem sem precisar do PC ligado.
"""

import os
import sys
import json
import time
import random
import argparse
from datetime import datetime
from typing import Dict, Any, List

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
            cfg = json.load(f)
    elif os.path.exists("config_default.json"):
        with open("config_default.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {"concurso_id": 619, "interval_seconds": 60, "ntfy": {"enabled": True, "topic": "avalia_concurso_619_alerta"}}

    # Na nuvem, desativa popups locais do Windows
    if "windows" in cfg:
        cfg["windows"]["enabled"] = False
        cfg["windows"]["play_sound"] = False

    # Sobrescrever variáveis de ambiente caso configuradas no GitHub Secrets
    if os.environ.get("NTFY_TOPIC"):
        cfg.setdefault("ntfy", {})["topic"] = os.environ["NTFY_TOPIC"]
        cfg["ntfy"]["enabled"] = True
    if os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        cfg.setdefault("telegram", {})["bot_token"] = os.environ["TELEGRAM_TOKEN"]
        cfg["telegram"]["chat_id"] = os.environ["TELEGRAM_CHAT_ID"]
        cfg["telegram"]["enabled"] = True

    return cfg


def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Aviso] Erro ao ler {STATE_FILE}: {e}")
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


def run_cloud_monitor(args):
    config = load_config()
    concurso_id = args.concurso or config.get("concurso_id", 619)
    interval = args.interval or config.get("interval_seconds", 60)
    max_duration_sec = (args.duration * 60) if args.duration else None

    dispatcher = NotificationDispatcher(config)
    state = load_state()

    print("=" * 70)
    print("      ☁️ MONITOR INSTITUTO AVALIA - MODO NUVEM ☁️")
    print(f"  Concurso ID: {concurso_id}")
    print(f"  Intervalo: ~{interval}s")
    if max_duration_sec:
        print(f"  Duração máxima desta sessão: {args.duration} minutos")
    print(f"  Canal de alerta ntfy: {config.get('ntfy', {}).get('topic')}")
    print("=" * 70)

    start_time = time.time()
    cycle = 0

    first_run = len(state.get("known_publicacoes", [])) == 0

    while True:
        cycle += 1
        now_str = format_timestamp()

        try:
            concurso_info = get_concurso_info(concurso_id)
            publicacoes = concurso_info.get("publicacoes", [])
            links = concurso_info.get("links", [])

            known_pub_ids = set(state.get("known_publicacoes", []))
            known_link_ids = set(state.get("known_links", []))

            if first_run:
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
                print(f"[{now_str}] [BASE ESTABELECIDA] {len(publicacoes)} publicações e {len(links)} links registrados.")
            else:
                novas_pubs = [p for p in publicacoes if (p.get("id") or p.get("url")) not in known_pub_ids]
                novos_links = [l for l in links if (l.get("identificador") or l.get("url") or l.get("nome")) not in known_link_ids]

                if novas_pubs:
                    print(f"\n🚨 [{now_str}] NOVA PUBLICAÇÃO DETECTADA! Total: {len(novas_pubs)}")
                    for p in novas_pubs:
                        titulo = p.get("nome", "Nova Publicação")
                        url = p.get("url", concurso_info.get("url_pagina", ""))
                        print(f"  -> {titulo}\n     Link: {url}")
                        dispatcher.send_all(
                            title=f"NOVA PUBLICAÇÃO! {concurso_info.get('edital', 'Concurso').upper()}",
                            message=f"Acaba de sair uma nova publicação no site do Instituto Avalia!\n\n📄 {titulo}\n⏰ {now_str}",
                            url=url,
                            extra_data={"concurso_nome": concurso_info.get("nome", "Instituto Avalia")}
                        )
                        known_pub_ids.add(p.get("id") or p.get("url"))
                        state.setdefault("history", []).append({"type": "publicacao", "item": p, "detected_at": now_str})

                if novos_links:
                    print(f"\n📢 [{now_str}] NOVO LINK/SISTEMA DETECTADO! Total: {len(novos_links)}")
                    for l in novos_links:
                        nome = l.get("nome", "Novo Link")
                        url = l.get("url", concurso_info.get("url_pagina", ""))
                        print(f"  -> {nome}\n     Link: {url}")
                        dispatcher.send_all(
                            title=f"NOVO SISTEMA DISPONÍVEL! ({l.get('categoria', 'Geral')})",
                            message=f"Novo link adicionado no Instituto Avalia:\n\n🔗 {nome}\n⏰ {now_str}",
                            url=url,
                            extra_data={"concurso_nome": concurso_info.get("nome", "Instituto Avalia")}
                        )
                        known_link_ids.add(l.get("identificador") or l.get("url") or l.get("nome"))
                        state.setdefault("history", []).append({"type": "link", "item": l, "detected_at": now_str})

                if not novas_pubs and not novos_links:
                    print(f"[{now_str}] [Ciclo #{cycle}] Nenhuma novidade. Total: {len(publicacoes)} pubs, {len(links)} links. Próxima em ~{interval}s...")

                state["known_publicacoes"] = list(known_pub_ids)
                state["known_links"] = list(known_link_ids)
                state["last_checked"] = now_str
                save_state(state)

        except Exception as e:
            print(f"[{now_str}] [Aviso Nuvem] Falha ao consultar banca: {e}")

        if args.once:
            break

        # Verificar se atingiu a duração máxima estipulada
        elapsed = time.time() - start_time
        if max_duration_sec and (elapsed + interval >= max_duration_sec):
            print(f"\n[Tempo Limite Atingido] Sessão de {args.duration} min finalizada com sucesso.")
            break

        time.sleep(interval + random.uniform(0, 5))


def main():
    parser = argparse.ArgumentParser(description="Monitor de Concursos em Nuvem")
    parser.add_argument("--once", action="store_true", help="Executa apenas uma verificação")
    parser.add_argument("--duration", type=int, default=300, help="Duração máxima em minutos da execução contínua")
    parser.add_argument("--interval", type=int, default=60, help="Intervalo em segundos entre verificações")
    parser.add_argument("--concurso", type=int, default=619, help="ID do concurso")
    args = parser.parse_args()

    run_cloud_monitor(args)


if __name__ == "__main__":
    main()

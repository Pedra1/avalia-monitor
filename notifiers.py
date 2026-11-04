"""
Módulo de notificações com suporte a múltiplos canais:
- ntfy.sh (Push notification no celular/navegador - 100% grátis, sem cadastro)
- Telegram Bot
- E-mail (SMTP - Gmail, Outlook, etc.)
- Discord Webhook
- WhatsApp (CallMeBot)
- Notificação nativa no Windows + Alarme Sonoro
- Webhook Genérico (Zapier, Make, n8n, etc.)
"""

import os
import sys
import json
import smtplib
import urllib.request
import urllib.parse
import urllib.error
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any, List

# Suporte a som no Windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class NotificationDispatcher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def send_all(self, title: str, message: str, url: str = "", extra_data: Dict[str, Any] = None) -> Dict[str, bool]:
        """Envia a notificação para todos os canais habilitados no config."""
        results = {}
        extra_data = extra_data or {}

        # 1. Alerta Sonoro / Windows
        if self.config.get("windows", {}).get("enabled", True):
            results["windows"] = self.send_windows(title, message, url)

        # 2. ntfy.sh (Push no celular)
        if self.config.get("ntfy", {}).get("enabled", False):
            results["ntfy"] = self.send_ntfy(title, message, url)

        # 3. Telegram
        if self.config.get("telegram", {}).get("enabled", False):
            results["telegram"] = self.send_telegram(title, message, url)

        # 4. E-mail
        if self.config.get("email", {}).get("enabled", False):
            results["email"] = self.send_email(title, message, url, extra_data)

        # 5. Discord
        if self.config.get("discord", {}).get("enabled", False):
            results["discord"] = self.send_discord(title, message, url)

        # 6. WhatsApp (CallMeBot)
        if self.config.get("whatsapp", {}).get("enabled", False):
            results["whatsapp"] = self.send_whatsapp(title, message, url)

        # 7. Webhook Genérico
        if self.config.get("webhook", {}).get("enabled", False):
            results["webhook"] = self.send_webhook(title, message, url, extra_data)

        return results

    # ==========================================
    # CANAL 1: WINDOWS (Toast + Som)
    # ==========================================
    def send_windows(self, title: str, message: str, url: str = "") -> bool:
        cfg = self.config.get("windows", {})
        try:
            # Tocar som de alarme se habilitado
            if cfg.get("play_sound", True) and HAS_WINSOUND:
                try:
                    # Sequência de bips de atenção
                    for _ in range(2):
                        for freq in [750, 1000, 1250]:
                            winsound.Beep(freq, 120)
                except Exception as e:
                    print(f"  [Aviso] Falha ao tocar som: {e}")

            # Notificação visual (PowerShell balloon/toast)
            clean_title = title.replace('"', ' ').replace("'", " ")[:60]
            clean_msg = message.replace('"', ' ').replace("'", " ")[:150]

            ps_script = f'''
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
            $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
            $objNotifyIcon.BalloonTipIcon = "Info"
            $objNotifyIcon.BalloonTipTitle = "{clean_title}"
            $objNotifyIcon.BalloonTipText = "{clean_msg}"
            $objNotifyIcon.Visible = $True
            $objNotifyIcon.ShowBalloonTip(10000)
            '''
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=8
            )
            print("  [OK] Notificação Windows exibida com sucesso.")
            return True
        except Exception as e:
            print(f"  [ERRO] Falha na notificação Windows: {e}")
            return False

    # ==========================================
    # CANAL 2: NTFY.SH (Push para celular/browser)
    # ==========================================
    def send_ntfy(self, title: str, message: str, url: str = "") -> bool:
        cfg = self.config.get("ntfy", {})
        topic = cfg.get("topic", "").strip()
        if not topic:
            print("  [AVISO ntfy] Tópico não configurado no config.json.")
            return False

        ntfy_server = cfg.get("server", "https://ntfy.sh").rstrip("/")
        endpoint = f"{ntfy_server}"

        priority_str = cfg.get("priority", "urgent").lower()
        priority_map = {"urgent": 5, "max": 5, "high": 4, "default": 3, "low": 2, "min": 1}
        priority_val = priority_map.get(priority_str, 5)

        payload = {
            "topic": topic,
            "title": title[:120],
            "message": message,
            "priority": priority_val,
            "tags": ["loudspeaker", "memo"],
        }
        if url:
            payload["click"] = url
            payload["actions"] = [
                {
                    "action": "view",
                    "label": "Abrir Publicação (PDF)",
                    "url": url
                }
            ]

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 201):
                    print(f"  [OK] Notificação ntfy.sh enviada ao tópico: {topic}")
                    return True
                else:
                    print(f"  [ERRO ntfy] Código de resposta HTTP: {resp.status}")
                    return False
        except Exception as e:
            print(f"  [ERRO ntfy] {e}")
            return False

    # ==========================================
    # CANAL 3: TELEGRAM BOT
    # ==========================================
    def send_telegram(self, title: str, message: str, url: str = "") -> bool:
        cfg = self.config.get("telegram", {})
        token = cfg.get("bot_token", "").strip()
        chat_id = cfg.get("chat_id", "").strip()

        if not token or not chat_id:
            print("  [AVISO Telegram] Bot token ou chat_id ausente.")
            return False

        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        
        texto_html = f"🚨 <b>{title}</b>\n\n{message}"
        if url:
            texto_html += f"\n\n🔗 <a href=\"{url}\"><b>CLIQUE AQUI PARA ABRIR O PDF / LINK</b></a>"

        payload = {
            "chat_id": chat_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("ok"):
                    print("  [OK] Mensagem Telegram enviada com sucesso!")
                    return True
                else:
                    print(f"  [ERRO Telegram] Resposta: {res_data}")
                    return False
        except Exception as e:
            print(f"  [ERRO Telegram] {e}")
            return False

    # ==========================================
    # CANAL 4: E-MAIL (SMTP)
    # ==========================================
    def send_email(self, title: str, message: str, url: str = "", extra_data: Dict[str, Any] = None) -> bool:
        cfg = self.config.get("email", {})
        smtp_host = cfg.get("smtp_host", "").strip()
        smtp_port = int(cfg.get("smtp_port", 587))
        smtp_user = cfg.get("smtp_user", "").strip()
        smtp_pass = cfg.get("smtp_pass", "").strip()
        from_email = cfg.get("from_email", smtp_user).strip()
        to_email = cfg.get("to_email", "").strip()
        use_tls = cfg.get("use_tls", True)
        use_ssl = cfg.get("use_ssl", False)

        if not smtp_host or not smtp_user or not smtp_pass or not to_email:
            print("  [AVISO E-mail] Dados de SMTP (host, usuário, senha ou destinatário) incompletos.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[ALERTA CONCURSO] {title}"
            msg["From"] = from_email
            msg["To"] = to_email

            # Texto puro
            texto_puro = f"{title}\n\n{message}\n"
            if url:
                texto_puro += f"\nLink direto para a publicação: {url}\n"

            # HTML estilizado
            btn_html = f'''
            <p style="margin-top: 25px;">
                <a href="{url}" style="background-color: #0070f3; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Abrir Publicação / Documento PDF &rarr;
                </a>
            </p>
            ''' if url else ""

            concurso_nome = extra_data.get("concurso_nome", "Instituto Avalia - Concurso 619") if extra_data else "Instituto Avalia"

            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
            </head>
            <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e1e4e8;">
                    <div style="background-color: #d32f2f; color: white; padding: 18px 24px;">
                        <h2 style="margin: 0; font-size: 20px;">🚨 Nova Publicação Detectada!</h2>
                        <p style="margin: 5px 0 0; font-size: 14px; opacity: 0.9;">{concurso_nome}</p>
                    </div>
                    <div style="padding: 24px;">
                        <p style="font-size: 16px; font-weight: bold; color: #111; margin-top: 0;">{title}</p>
                        <p style="font-size: 15px; line-height: 1.5; color: #444; white-space: pre-line;">{message}</p>
                        {btn_html}
                        <hr style="border: none; border-top: 1px solid #eaeaea; margin: 25px 0 15px;">
                        <p style="font-size: 12px; color: #888; margin: 0;">
                            Notificação enviada automaticamente pelo Monitor Instituto Avalia às {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''

            msg.attach(MIMEText(texto_puro, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if use_tls:
                    server.starttls()

            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()

            print(f"  [OK] E-mail enviado com sucesso para: {to_email}")
            return True
        except Exception as e:
            print(f"  [ERRO E-mail] {e}")
            return False

    # ==========================================
    # CANAL 5: DISCORD WEBHOOK
    # ==========================================
    def send_discord(self, title: str, message: str, url: str = "") -> bool:
        cfg = self.config.get("discord", {})
        webhook_url = cfg.get("webhook_url", "").strip()
        if not webhook_url:
            print("  [AVISO Discord] Webhook URL ausente.")
            return False

        payload = {
            "content": "🚨 **NOVA PUBLICAÇÃO DETECTADA - BANCA AVALIA!** @everyone",
            "embeds": [
                {
                    "title": title[:256],
                    "description": message[:2048],
                    "url": url if url else None,
                    "color": 15158332,  # Vermelho Alerta
                    "fields": [
                        {"name": "🔗 Link Direto", "value": f"[Clique para Acessar]({url})" if url else "Página do Concurso", "inline": True}
                    ],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "footer": {"text": "Monitor Instituto Avalia"}
                }
            ]
        }

        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AvaliaMonitor/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 204):
                    print("  [OK] Mensagem Discord enviada com sucesso!")
                    return True
                else:
                    print(f"  [ERRO Discord] Código HTTP: {resp.status}")
                    return False
        except Exception as e:
            print(f"  [ERRO Discord] {e}")
            return False

    # ==========================================
    # CANAL 6: WHATSAPP (CallMeBot)
    # ==========================================
    def send_whatsapp(self, title: str, message: str, url: str = "") -> bool:
        cfg = self.config.get("whatsapp", {})
        phone = cfg.get("phone", "").strip()
        apikey = cfg.get("apikey", "").strip()

        if not phone or not apikey:
            print("  [AVISO WhatsApp] Telefone ou API Key do CallMeBot ausente.")
            return False

        texto = f"*🚨 NOVA PUBLICAÇÃO - AVALIA 🚨*\n\n*{title}*\n{message}"
        if url:
            texto += f"\n\n*Link do PDF:*\n{url}"

        params = urllib.parse.urlencode({
            "phone": phone,
            "text": texto,
            "apikey": apikey
        })
        url_api = f"https://api.callmebot.com/whatsapp.php?{params}"

        try:
            req = urllib.request.Request(url_api, headers={"User-Agent": "AvaliaMonitor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_text = resp.read().decode("utf-8", errors="ignore")
                if "Message queued" in resp_text or "success" in resp_text.lower() or resp.status == 200:
                    print("  [OK] Mensagem de WhatsApp enviada!")
                    return True
                else:
                    print(f"  [AVISO WhatsApp] Resposta CallMeBot: {resp_text}")
                    return True
        except Exception as e:
            print(f"  [ERRO WhatsApp] {e}")
            return False

    # ==========================================
    # CANAL 7: WEBHOOK GENÉRICO
    # ==========================================
    def send_webhook(self, title: str, message: str, url: str = "", extra_data: Dict[str, Any] = None) -> bool:
        cfg = self.config.get("webhook", {})
        endpoint = cfg.get("url", "").strip()
        if not endpoint:
            return False

        payload = {
            "event": "nova_publicacao",
            "title": title,
            "message": message,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "extra": extra_data or {}
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.status in (200, 201, 204)
        except Exception as e:
            print(f"  [ERRO Webhook Genérico] {e}")
            return False

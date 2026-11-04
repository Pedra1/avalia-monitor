# 🚨 Monitor de Publicações - Instituto Avalia (Concurso 619)

Aplicação desenvolvida sob medida para monitorar a página do **Instituto Avalia** ([Concurso 619 - Polícia Penal RN / SEAD-RN](https://www.avalia.org.br/concursos/619)) e disparar **alertas imediatos** assim que uma nova publicação, edital, anexo ou link for divulgado hoje.

---

## ⚡ Como Funciona

- O monitor se conecta diretamente à **API oficial em tempo real da banca Avalia** (`https://link.avalia.org.br/api/concursos/619`).
- Isso garante **detecção instantânea**, sem atrasos de cache de navegador ou renderização pesada.
- O sistema já registrou as **37 publicações existentes** como base inicial para não disparar falsos alertas antigos.
- Assim que um novo item surgir, o monitor:
  1. Identifica o título e o link direto de download (PDF).
  2. Dispara som de alerta no seu computador.
  3. Envia notificações para todos os canais que você ativar (Celular, E-mail, Telegram, etc.).

---

## 🚀 Como Iniciar em 1 Clique (Windows)

Na pasta do projeto (`c:\Users\pedro\Desktop\attualizador`):

1. **Para iniciar o monitoramento:**
   - Dê dois cliques em **`iniciar_monitor.bat`** (ou rode `python monitor.py`).
   - Ele ficará consultando a banca a cada ~60 segundos e avisará imediatamente no console e nos canais cadastrados.

2. **Para testar seus canais agora mesmo:**
   - Dê dois cliques em **`testar_notificacoes.bat`** (ou rode `python monitor.py --test`).
   - Ele enviará uma notificação de teste para você confirmar o recebimento no seu celular ou e-mail.

3. **Para configurar os alertas via assistente interativo:**
   - Dê dois cliques em **`configurar.bat`** (ou rode `python setup_wizard.py`).

4. **Para abrir o Painel Visual Web (Opcional):**
   - Dê dois cliques em **`abrir_dashboard.bat`** (abre no navegador uma interface completa com as publicações recentes, botões de download e configurações).

---

## 📱 Como Receber Alertas no Celular em 10 Segundos (ntfy.sh - Recomendado)

O método mais rápido, 100% gratuito e que **não requer nenhum cadastro**:

1. No seu celular (Android ou iPhone):
   - **Opção A (sem app):** Abra o navegador do celular e acesse:  
     👉 **https://ntfy.sh/avalia_concurso_619_alerta**  
     Clique em **"Inscrever-se" / "Permitir Notificações"**.
   - **Opção B (com app):** Baixe o aplicativo gratuito **ntfy** na Play Store ou App Store e adicione o tópico:  
     `avalia_concurso_619_alerta`
2. Pronto! Assim que sair a publicação hoje, seu celular vai tocar/vibrar com o título da publicação e um botão direto para abrir o PDF!
3. Se quiser mudar o nome do tópico para um particular (ex: `concurso_pedro_619`), basta alterar no arquivo `config.json` ou usar o `configurar.bat`.

---

## 📧 Como Ativar Notificação por E-mail (Gmail / Outlook)

No arquivo `config.json` ou executando `configurar.bat`:

1. Altere `"enabled": true` na seção `"email"`.
2. Para o **Gmail**:
   - `smtp_host`: `"smtp.gmail.com"`
   - `smtp_port`: `587`
   - `smtp_user`: Seu e-mail do Gmail
   - `smtp_pass`: **Senha de App** do Google (gerada em *Conta Google -> Segurança -> Senhas de App*)
   - `to_email`: O e-mail onde você quer receber o aviso
3. Teste dando dois cliques em `testar_notificacoes.bat`.

---

## 🤖 Como Ativar Telegram Bot

1. Abra o Telegram e procure por `@BotFather`.
2. Digite `/newbot` e siga as instruções para criar o bot e pegar o **Token HTTP API**.
3. Procure pelo bot `@userinfobot` para ver seu **Chat ID**.
4. Inicie uma conversa com seu novo bot clicando em `/start`.
5. No `config.json` ou `configurar.bat`, preencha `bot_token` e `chat_id` e ative o canal.

---

## 💻 Canais Suportados

| Canal | Descrição | Configuração |
|---|---|---|
| **ntfy.sh (Celular)** | Push direto no celular/navegador com som | Já ativo por padrão! Só abrir o link no celular. |
| **Windows Desktop** | Notificação na bandeja + Bips sonoros de alerta | Já ativo por padrão no seu PC! |
| **E-mail (SMTP)** | E-mail com layout HTML e botão para baixar o PDF | Gmail, Outlook, Yahoo ou SMTP próprio |
| **Telegram** | Mensagem com link direto para o PDF | Bot Token + Chat ID |
| **Discord** | Mensagem com menção `@everyone` no canal | Webhook URL |
| **WhatsApp** | Notificação via CallMeBot | Telefone + API Key |
| **Webhook Genérico** | Disparo de JSON via POST | Zapier, Make, n8n |

---

## ⚙️ Linha de Comando (Opções Avançadas)

```bash
# Executar verificação contínua
python monitor.py

# Disparar notificação de teste em todos os canais
python monitor.py --test

# Executar apenas uma vez e sair
python monitor.py --once

# Alterar intervalo para 30 segundos
python monitor.py --interval 30

# Resetar histórico de publicações memorizadas
python monitor.py --reset-state
```

---

## 📂 Arquivos do Projeto

- `monitor.py`: Script principal do serviço de monitoramento.
- `notifiers.py`: Módulo responsável pelos disparos em todos os canais.
- `avalia_api.py`: Comunicação com a API oficial do Instituto Avalia.
- `setup_wizard.py`: Assistente interativo de configuração.
- `dashboard.py`: Interface visual web completa em Streamlit.
- `config.json`: Arquivo central de configurações.
- `state.json`: Memória persistente das publicações já identificadas.
- `iniciar_monitor.bat`: Inicializador rápido para o Windows.
- `testar_notificacoes.bat`: Testador de alertas para o Windows.
- `configurar.bat`: Configurador rápido para o Windows.
- `abrir_dashboard.bat`: Inicializador da interface web.


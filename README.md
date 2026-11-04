# 🚨 Monitor de Publicações - Instituto Avalia (Concurso 619)

Aplicação desenvolvida sob medida para monitorar a página do **Instituto Avalia** ([Concurso 619 - Polícia Penal RN / SEAD-RN](https://www.avalia.org.br/concursos/619)) e disparar **alertas imediatos no celular** assim que uma nova publicação, edital, anexo ou link for divulgado hoje.

---

## ☁️ Como Rodar na Nuvem (Para Desligar o Computador)

Para não precisar deixar o seu computador ligado:

1. Acesse **[github.com/new](https://github.com/new)** no seu navegador.
2. Crie um novo repositório com qualquer nome (ex: `avalia-monitor`).
   - *Dica:* Deixe como **Público** para ter minutos de execução ilimitados e 100% gratuitos no GitHub Actions.
3. Copie o link do repositório (ex: `https://github.com/Pedra1/avalia-monitor.git`).
4. Na pasta do projeto, dê dois cliques em **[`publicar_no_github.bat`](file:///c:/Users/pedro/Desktop/attualizador/publicar_no_github.bat)** e cole o link.
5. Pronto! Acesse a aba **Actions** no seu GitHub, clique em **"Monitor Concurso Avalia 619"** e clique no botão **"Run workflow"**.
6. **Você já pode desligar o computador completamente!** O monitor estará rodando na nuvem do GitHub e enviará a notificação para o seu celular assim que sair o resultado.

---

## 💻 Como Rodar Localmente no seu Computador

Se preferir rodar no próprio PC:

1. Dê dois cliques em **[`iniciar_monitor.bat`](file:///c:/Users/pedro/Desktop/attualizador/iniciar_monitor.bat)**.
2. Deixe a janela aberta (pode minimizar).
3. Teste o disparo a qualquer momento em **[`testar_notificacoes.bat`](file:///c:/Users/pedro/Desktop/attualizador/testar_notificacoes.bat)**.
4. Abra o painel web em **[`abrir_dashboard.bat`](file:///c:/Users/pedro/Desktop/attualizador/abrir_dashboard.bat)**.

---

## 📱 Notificações no Celular (ntfy.sh)

- **Tópico:** `avalia_concurso_619_alerta`
- **Link no Celular:** [https://ntfy.sh/avalia_concurso_619_alerta](https://ntfy.sh/avalia_concurso_619_alerta)
- Não precisa de cadastro, funciona em segundo plano e abre o PDF direto pelo botão!

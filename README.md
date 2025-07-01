# Radar Industrial Automatizado com IA

Este projeto automatiza um radar diário de notícias industriais, analisa com IA (Google Gemini), salva dados em planilha do Google Sheets e envia os destaques por e-mail para múltiplos destinatários.

## 🚀 Funcionalidades

- Coleta notícias de economia e indústria via RSS
- Usa IA para gerar análises estratégicas e nota de relevância
- Salva histórico no Google Sheets
- Envia e-mail com os Top 5 em cópia oculta (CCO)
- Gera tendência semanal, mensal e anual
- Automatizado com Render.com (gratuito)

## ⚙️ Como configurar

As credenciais são configuradas por variáveis de ambiente no Render:

| Variável           | O que é                                      |
|--------------------|-----------------------------------------------|
| CHAVE_API_GEMINI   | Sua chave da API do Gemini                   |
| EMAIL_REMETENTE    | Gmail usado para enviar                      |
| SENHA_APP          | Senha de app do Gmail                        |
| EMAIL_DESTINO      | Lista de e-mails separados por vírgula       |

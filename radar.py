import os
import feedparser
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

CHAVE_API_GEMINI = os.environ.get("CHAVE_API_GEMINI")
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
SENHA_APP = os.environ.get("SENHA_APP")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO").split(",")
ARQUIVO_CREDENCIAL_JSON = "credenciais.json"
NOME_PLANILHA = "Radar Industrial"

FONTES_RSS = [
    "https://g1.globo.com/rss/g1/economia/",
    "https://valor.globo.com/rss/",
    "https://www1.folha.uol.com.br/rss/folha-dinheiro.xml",
    "https://exame.com/rss/",
    "https://oglobo.globo.com/rss/economia/",
    "https://feeds.reuters.com/Reuters/worldNews",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.npr.org/rss/rss.php?id=1006"
]

def coletar_noticias(max_por_fonte=3):
    todas_noticias = []
    for url in FONTES_RSS:
        feed = feedparser.parse(url)
        for item in feed.entries[:max_por_fonte]:
            todas_noticias.append({
                "titulo": item.title,
                "resumo": item.summary if 'summary' in item else '',
                "link": item.link
            })
    return todas_noticias

def analisar_noticia(titulo, resumo):
    prompt = f"""Notícia: {titulo}
Resumo: {resumo}

Perguntas:
1. Essa notícia afeta a macroeconomia? Como?
2. Quais setores industriais são impactados?
3. Existe alguma oportunidade para uma consultoria de engenharia de produção como a Produttare?

Responda de forma resumida, em português, clara e estratégica.
Dê uma nota de relevância (0 a 10) no final: Relevância: x/10"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Erro {r.status_code}"

def enviar_email(assunto, corpo):
    mensagem = MIMEMultipart()
    mensagem['From'] = EMAIL_REMETENTE
    mensagem['To'] = "Radar Produttare <noreply@produttare.com>"
    mensagem['Bcc'] = ", ".join(EMAIL_DESTINO)
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP)
        servidor.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, mensagem.as_string())
        servidor.quit()
        return "✅ E-mail enviado com sucesso!"
    except Exception as erro:
        return f"❌ Erro ao enviar e-mail: {erro}"

def extrair_nota_relevancia(texto):
    try:
        linha = [l for l in texto.splitlines() if "Relevância" in l][0]
        nota = int(linha.split(":")[-1].strip().split("/")[0])
        return nota
    except:
        return 0

def salvar_em_sheets(top5):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDENCIAL_JSON, scope)
    client = gspread.authorize(creds)
    aba = client.open(NOME_PLANILHA).worksheet("Histórico")
    data = datetime.now().strftime("%d/%m/%Y")
    for item in top5:
        nota = extrair_nota_relevancia(item["analise"])
        aba.append_row([data, item["titulo"], item["link"], item["analise"], nota])

print("🔍 Coletando notícias...")
noticias = coletar_noticias()
analises_completas = []

print("🤖 Analisando com IA...")
for noticia in noticias:
    resposta = analisar_noticia(noticia['titulo'], noticia['resumo'])
    analises_completas.append({
        "titulo": noticia['titulo'],
        "link": noticia['link'],
        "analise": resposta
    })

analises_completas.sort(key=lambda x: extrair_nota_relevancia(x["analise"]), reverse=True)
top5 = analises_completas[:5]
salvar_em_sheets(top5)

corpo_email = "📡 Radar de Oportunidades Industriais – Top 5 do Dia

"
for item in top5:
    corpo_email += f"{item['titulo']}
{item['link']}
{item['analise']}

---

"

print(enviar_email("Radar Produttare - Top 5 Oportunidades do Dia", corpo_email))

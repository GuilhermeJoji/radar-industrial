# === IMPORTAÇÕES ===
import feedparser
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


# === NOVAS IMPORTAÇÕES ===
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# === 🔐 CONFIGURAÇÕES ===
CHAVE_API_GEMINI = os.environ.get("CHAVE_API_GEMINI")
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
SENHA_APP = os.environ.get("SENHA_APP")
ARQUIVO_CREDENCIAL_JSON = "credenciais.json"
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO")


# === CONFIGS PARA GOOGLE SHEETS ===
NOME_PLANILHA = "Radar Industrial"

# === SALVAR ANÁLISES NO GOOGLE SHEETS ===
def salvar_em_sheets(top5):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDENCIAL_JSON, scope)
    client = gspread.authorize(creds)
    aba = client.open(NOME_PLANILHA).worksheet("Histórico")
    data = datetime.now().strftime("%d/%m/%Y")
    for item in top5:
        nota = extrair_nota_relevancia(item["analise"])
        aba.append_row([data, item["titulo"], item["link"], item["analise"], nota])

# === GERAR DIRECIONAMENTO COMERCIAL ===
def gerar_direcionamento(top5):
    # Junta os títulos e análises para alimentar o prompt
    blocos = "\n\n".join([f"{item['titulo']}\n{item['analise']}" for item in top5])

    # Prompt estruturado para gerar até 2 direcionamentos comerciais estratégicos
    prompt = f"""
Você é um estrategista comercial da Produttare, uma consultoria brasileira especializada em engenharia de produção, eficiência operacional, Lean Office, PCP, logística, custos e gestão industrial.

Com base nas análises das notícias abaixo, gere até 2 DIRECIONAMENTOS COMERCIAIS objetivos, relevantes para o mercado BRASILEIRO.

Formato:
1) Setor/Perfil: [Ex: Agroindústria do Sul, grandes indústrias químicas, empresas com cadeia logística internacional etc.]
- Oportunidade: [Resumo direto do que pode ser explorado comercialmente]
- Justificativa: [Ligação clara com as análises abaixo]
- Ação recomendada: [Sugestão prática para os vendedores — ex: "abordar empresas do setor X com proposta de otimização logística"]

2) (Outro direcionamento se aplicável)

Instruções:
- Se as notícias não gerarem 2 focos claros, dê apenas 1.
- Evite generalizações. Foco total no contexto brasileiro.
- Use linguagem executiva e comercial, sem repetir as análises.

Análises:
{blocos}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        try:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return "Erro na resposta da IA"
    else:
        return f"Erro {r.status_code}"

# === FUNÇÃO: Gera a análise de tendência do mês ===
def gerar_analise_mensal():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
    client = gspread.authorize(creds)
    aba = client.open(NOME_PLANILHA).worksheet("Histórico")
    registros = aba.get_all_records()
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year

    noticias_mes = [r for r in registros if datetime.strptime(r['Data'], "%d/%m/%Y").month == mes_atual and datetime.strptime(r['Data'], "%d/%m/%Y").year == ano_atual]

    if not noticias_mes:
        return "Sem dados suficientes para análise mensal."

    blocos = "\n\n".join([f"{r['Título']}\n{r['Análise']}" for r in noticias_mes[:30]])

    prompt = f"""
Você é um analista estratégico da Produttare, consultoria brasileira de engenharia de produção.

Com base nas análises abaixo, gere um RESUMO EXECUTIVO com foco no cenário INDUSTRIAL BRASILEIRO deste mês.

Inclua:
- Setores ou regiões brasileiras em destaque
- Oportunidades recorrentes para serviços de consultoria como os da Produttare (PCP, logística, processos, custos, estratégia industrial etc.)
- Desafios ou sinais de atenção para a indústria nacional
- Recomendação clara de foco comercial para o mês seguinte

Evite termos genéricos. Use uma linguagem objetiva e com potencial comercial.

Análises:
{blocos}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        try:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return "Erro ao gerar análise mensal."
    else:
        return f"Erro {r.status_code}"


# === FUNÇÃO: Gera tendência do próximo ano ===
def gerar_tendencia_anual():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
    client = gspread.authorize(creds)
    aba = client.open(NOME_PLANILHA).worksheet("Histórico")
    registros = aba.get_all_records()

    blocos = "\n\n".join([f"{r['Título']}\n{r['Análise']}" for r in registros[-100:]])

    prompt = f"""
Você é um analista da Produttare e precisa antecipar o cenário industrial BRASILEIRO para o próximo ano com base nas análises abaixo.

Escreva uma previsão estratégica com foco em:

- Setores ou movimentos industriais no Brasil que devem ganhar força
- Oportunidades para atuação da Produttare (engenharia de produção, operações, logística, custos, processos etc.)
- Sinais de alerta para a indústria nacional
- Sugestões claras de foco comercial e posicionamento estratégico para o ano

Evite generalizações e destaque caminhos reais de atuação no Brasil.

Análises:
{blocos}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        try:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return "Erro ao gerar previsão anual."
    else:
        return f"Erro {r.status_code}"





# Fontes RSS nacionais e internacionais
FONTES_RSS = [
# 🇧🇷 Economia
    "https://g1.globo.com/rss/g1/economia/",
    "https://valor.globo.com/rss/",
    "https://www1.folha.uol.com.br/rss/folha-dinheiro.xml",
    "https://exame.com/rss/",
    "https://oglobo.globo.com/rss/economia/",
    "https://istoedinheiro.com.br/feed/", 

    # 🌍 Mundo
    "https://feeds.reuters.com/Reuters/worldNews",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.npr.org/rss/rss.php?id=1006",

    # 🧭 Política e macroambiente
    "https://g1.globo.com/rss/g1/politica/",  
    "https://www1.folha.uol.com.br/rss/folha-poder.xml", 
    "https://www.nexojornal.com.br/rss.xml", 

    # 📊 Fontes oficiais e estratégicas
    "https://agenciadenoticias.ibge.gov.br/rss/ultimas-noticias.xml",
    "https://noticias.portaldaindustria.com.br/rss/",

    # 💡 Inovação e tecnologia
    "https://www.technologyreview.com/feed/",
]

# === FUNÇÃO: Coleta notícias dos feeds
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

# === FUNÇÃO: Usa a IA para avaliar relevância e gerar análise
def analisar_noticia(titulo, resumo):
    prompt = f"""
    Notícia: {titulo}
    Resumo: {resumo}

    Perguntas:
    1. Essa notícia afeta a macroeconomia? Como?
    2. Quais setores industriais são impactados?
    3. Existe alguma oportunidade para uma consultoria de engenharia de produção como a Produttare?

    Responda de forma resumida, em português, clara e estratégica.
    Dê uma nota de relevância (0 a 10) no final: Relevância: x/10
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    resposta = requests.post(url, json=payload)
    if resposta.status_code == 200:
        try:
            return resposta.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return "Erro na resposta da IA"
    else:
        return f"Erro {resposta.status_code}: {resposta.text}"

# === FUNÇÃO: Envia o radar por e-mail
def enviar_email(assunto, corpo):
    mensagem = MIMEMultipart()
    mensagem['From'] = EMAIL_REMETENTE
    mensagem['To'] = "Radar Produttare <noreply@produttare.com>"
    mensagem['Bcc'] = ", ".join(EMAIL_DESTINO.split(","))
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP)
        servidor.send_message(mensagem)
        servidor.quit()
        return "✅ E-mail enviado com sucesso!"
    except Exception as erro:
        return f"❌ Erro ao enviar e-mail: {erro}"

# === GERAR TENDÊNCIA DA SEMANA E ENVIAR POR E-MAIL ===
def gerar_tendencia_semanal():
    # Conecta ao Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(ARQUIVO_CREDENCIAL_JSON, scope)
    client = gspread.authorize(creds)
    aba = client.open(NOME_PLANILHA).worksheet("Histórico")

    # Pega os últimos 7 dias
    hoje = datetime.now()
    limite = hoje - timedelta(days=7)
    registros = aba.get_all_records()

    ultimos_dias = []
    for linha in registros:
        try:
            data = datetime.strptime(linha['Data'], "%d/%m/%Y")
            if data >= limite:
                ultimos_dias.append(linha)
        except:
            continue

    # Se não houver dados suficientes, sai
    if not ultimos_dias:
        print("Nenhum dado suficiente para tendência semanal.")
        return

    # Monta prompt com as análises da semana
    texto = "\n\n".join([f"{item['Título']}\n{item['Análise']}" for item in ultimos_dias])
    prompt = f"""
Você é um estrategista da Produttare, consultoria focada na indústria brasileira.

Com base nas análises a seguir (últimos 7 dias), identifique a principal TENDÊNCIA INDUSTRIAL observada no Brasil — algo que ajude o time comercial da Produttare a se posicionar com inteligência.

Inclua:
- Qual setor ou perfil de empresa brasileira está mais impactado
- Qual oportunidade prática pode ser explorada pela consultoria
- Como a Produttare pode ajudar (ex: projeto de eficiência, PCP, custos, logística etc.)

Seja direto, objetivo e relevante para o time comercial.

Análises:
{texto}
"""
    # Chama a IA
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CHAVE_API_GEMINI}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        try:
            tendencia = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            tendencia = "Erro ao gerar tendência"
    else:
        tendencia = f"Erro {r.status_code}"

    # Envia por e-mail
    corpo = "📈 <b>Tendência da Semana</b><br><br>" + tendencia.replace("\n", "<br>")
    enviar_email("Radar Produttare - Tendência Industrial da Semana", corpo)
    print("✅ E-mail de tendência semanal enviado!")


# === EXECUÇÃO PRINCIPAL ===

print("🔍 Coletando notícias...")
noticias = coletar_noticias()
analises_completas = []

print("🤖 Analisando com IA...")
for noticia in noticias:
    titulo = noticia['titulo']
    resumo = noticia['resumo']
    link = noticia['link']
    resposta = analisar_noticia(titulo, resumo)
    analises_completas.append({
        "titulo": titulo,
        "link": link,
        "analise": resposta
    })

# === FILTRAR AS TOP 5 MAIS RELEVANTES ===
def extrair_nota_relevancia(texto):
    try:
        linha = [l for l in texto.splitlines() if "Relevância" in l][0]
        nota = int(linha.split(":")[-1].strip().split("/")[0])
        return nota
    except:
        return 0

analises_completas.sort(key=lambda x: extrair_nota_relevancia(x["analise"]), reverse=True)
top5 = analises_completas[:5]

# === FORMATAR E ENVIAR E-MAIL ===
# === SALVAR NO GOOGLE SHEETS ===
salvar_em_sheets(top5)

# === GERAR DIRECIONAMENTO COMERCIAL ===
direcao = gerar_direcionamento(top5)

# === MONTAR E-MAIL COMPLETO ===
corpo_email = (
    "📡 Radar de Oportunidades Industriais Produttare – *Powered by Guilherme Joji*\n\n"
    "📌 DIRECIONAMENTO COMERCIAL DO DIA\n\n" + direcao + "\n\n"
    "====================\n\n"
    "📰 *Top 5 do Dia*\n\n"
)

for item in top5:
    corpo_email += f"🔗 {item['titulo']}\n{item['link']}\n{item['analise']}\n\n---\n\n"

# === ENVIO DO E-MAIL ===
resultado = enviar_email("Radar Produttare - Top 5 Oportunidades do Dia", corpo_email)
print(resultado)

# === EXECUTA ANÁLISE SEMANAL SOMENTE ÀS SEXTAS ===
if datetime.now().weekday() == 4:  # 4 = sexta-feira
    gerar_tendencia_semanal()

# === CHECA SE É FIM DE MÊS OU 01/12 ===
hoje = datetime.now()
ultimo_dia_do_mes = (hoje + timedelta(days=1)).month != hoje.month

# 📤 Enviar análise mensal no último dia do mês
if ultimo_dia_do_mes:
    analise_mensal = gerar_analise_mensal()
    enviar_email("Radar Produttare - Tendência Mensal", analise_mensal)

# 📤 Enviar tendência do ano no dia 01/12
if hoje.day == 1 and hoje.month == 12:
    tendencia_ano = gerar_tendencia_anual()
    enviar_email("Radar Produttare - Tendência para o Ano Seguinte", tendencia_ano)

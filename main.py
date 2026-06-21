from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uuid, os, json, qrcode
from pathlib import Path

app = FastAPI()

BASE_URL = os.getenv("BASE_URL", "https://momentosespeciais-production.up.railway.app")
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
TAMANHO_MAX_MB = 5

for pasta in ["uploads", "qrcodes", "dados"]:
    os.makedirs(pasta, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

DB_PATH = Path("dados/banco.json")

def carregar_banco():
    return json.loads(DB_PATH.read_text(encoding="utf-8")) if DB_PATH.exists() else {}

def salvar_banco(banco):
    DB_PATH.write_text(json.dumps(banco, ensure_ascii=False, indent=2), encoding="utf-8")

TEMAS = {
    "amor": {
        "nome": "Amor & Romance",
        "emoji": "💕",
        "bg": "#0d0608",
        "grad1": "#fff0f3",
        "grad2": "#ffe0e8",
        "cor1": "#c8384f",
        "cor2": "#8b1a30",
        "cor3": "#7a1530",
        "texto": "#4a2030",
        "borda": "#e8b4bc",
        "fundo_carta": "rgba(255,200,210,0.15)",
        "fonte": "Playfair Display",
        "topo": "linear-gradient(90deg,#8b1a30,#c8384f,#e8526a,#c8384f,#8b1a30)",
    },
    "maes": {
        "nome": "Dia das Mães",
        "emoji": "💚",
        "bg": "#030a05",
        "grad1": "#f0fff4",
        "grad2": "#d4f7e0",
        "cor1": "#16a34a",
        "cor2": "#14532d",
        "cor3": "#14532d",
        "texto": "#1a3a25",
        "borda": "#86efac",
        "fundo_carta": "rgba(134,239,172,0.15)",
        "fonte": "Lora",
        "topo": "linear-gradient(90deg,#14532d,#16a34a,#22c55e,#16a34a,#14532d)",
    },
    "aniversario": {
        "nome": "Aniversário",
        "emoji": "🎂",
        "bg": "#0a0700",
        "grad1": "#fffbeb",
        "grad2": "#fef3c7",
        "cor1": "#d97706",
        "cor2": "#78350f",
        "cor3": "#78350f",
        "texto": "#451a03",
        "borda": "#fcd34d",
        "fundo_carta": "rgba(252,211,77,0.15)",
        "fonte": "Playfair Display",
        "topo": "linear-gradient(90deg,#78350f,#d97706,#f59e0b,#d97706,#78350f)",
    },
    "pais": {
        "nome": "Dia dos Pais",
        "emoji": "💙",
        "bg": "#00030a",
        "grad1": "#eff6ff",
        "grad2": "#dbeafe",
        "cor1": "#2563eb",
        "cor2": "#1e3a8a",
        "cor3": "#1e3a8a",
        "texto": "#1e3a5f",
        "borda": "#93c5fd",
        "fundo_carta": "rgba(147,197,253,0.15)",
        "fonte": "Lora",
        "topo": "linear-gradient(90deg,#1e3a8a,#2563eb,#3b82f6,#2563eb,#1e3a8a)",
    },
    "natal": {
        "nome": "Natal",
        "emoji": "🎄",
        "bg": "#05000a",
        "grad1": "#faf5ff",
        "grad2": "#ede9fe",
        "cor1": "#7c3aed",
        "cor2": "#4c1d95",
        "cor3": "#4c1d95",
        "texto": "#2e1065",
        "borda": "#c4b5fd",
        "fundo_carta": "rgba(196,181,253,0.15)",
        "fonte": "Playfair Display",
        "topo": "linear-gradient(90deg,#4c1d95,#7c3aed,#8b5cf6,#7c3aed,#4c1d95)",
    },
    "especial": {
        "nome": "Sem data especial",
        "emoji": "✨",
        "bg": "#000a05",
        "grad1": "#f0fdf4",
        "grad2": "#dcfce7",
        "cor1": "#15803d",
        "cor2": "#052e16",
        "cor3": "#052e16",
        "texto": "#14532d",
        "borda": "#6ee7b7",
        "fundo_carta": "rgba(110,231,183,0.15)",
        "fonte": "Lora",
        "topo": "linear-gradient(90deg,#052e16,#15803d,#22c55e,#15803d,#052e16)",
    },
}

@app.get("/", response_class=HTMLResponse)
def home():
    temas_html = ""
    for key, t in TEMAS.items():
        ativo = 'style="border:2px solid ' + t["cor1"] + '"' if key == "amor" else ""
        temas_html += f"""
        <div class="tema" data-tema="{key}" onclick="selecionarTema(this)"
             style="border-radius:14px;overflow:hidden;cursor:pointer;border:2px solid transparent;transition:transform 0.2s,border-color 0.2s;" {ativo}>
          <div style="background:linear-gradient(135deg,{t['grad1']},{t['grad2']});padding:16px 12px;text-align:center;">
            <div style="font-size:28px;margin-bottom:4px;">{t['emoji']}</div>
            <div style="font-size:13px;font-weight:600;color:{t['cor3']};margin-bottom:2px;">{t['nome']}</div>
          </div>
          <div style="background:{t['cor1']};padding:7px;text-align:center;font-size:11px;color:#fff;font-weight:500;letter-spacing:0.5px;">Selecionar</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💖 Momentos Especiais</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
        body{{min-height:100vh;background:#080308;display:flex;align-items:flex-start;justify-content:center;padding:0 16px 40px;font-family:'Inter',sans-serif}}
        body::before{{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 60% at 20% 10%,rgba(180,30,60,.2) 0%,transparent 60%),radial-gradient(ellipse 60% 80% at 80% 90%,rgba(200,40,80,.15) 0%,transparent 60%);pointer-events:none;z-index:0}}
        .page{{position:relative;z-index:1;max-width:480px;width:100%;padding-top:0}}
        .urgency{{background:linear-gradient(90deg,#8b1a30,#c8384f);padding:11px 16px;border-radius:0 0 14px 14px;text-align:center;margin-bottom:16px}}
        .urgency span{{color:#ffd6df;font-size:13px;letter-spacing:0.3px}}
        .urgency strong{{color:#fff}}
        .card{{background:#fff;border-radius:24px;overflow:hidden;box-shadow:0 20px 60px rgba(200,56,79,.25)}}
        .hero{{background:linear-gradient(135deg,#fff0f3,#ffe0e8);padding:28px 24px 20px;text-align:center}}
        .badge{{display:inline-flex;align-items:center;gap:6px;background:rgba(200,56,79,.1);border:1px solid rgba(200,56,79,.2);border-radius:20px;padding:5px 12px;font-size:12px;color:#c8384f;margin-bottom:14px}}
        .dot{{width:7px;height:7px;background:#22c55e;border-radius:50%;animation:pulse 1.5s infinite}}
        @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
        h1{{font-family:'Playfair Display',serif;font-size:24px;color:#7a1530;line-height:1.3;margin-bottom:8px}}
        .hero-sub{{font-size:14px;color:#a06070;font-style:italic;margin-bottom:18px;line-height:1.6}}
        .frase-especial{{background:rgba(200,56,79,.08);border-left:3px solid #c8384f;border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:18px;text-align:left}}
        .frase-especial p{{font-size:13px;color:#7a1530;font-style:italic;line-height:1.6}}
        .corpo{{padding:24px}}
        .section-title{{font-size:12px;font-weight:600;color:#7a1530;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}}
        .temas-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:20px}}
        .campo{{margin-bottom:16px}}
        label{{display:block;font-size:11px;font-weight:600;color:#555;margin-bottom:5px;letter-spacing:.8px;text-transform:uppercase}}
        input[type=text],textarea{{width:100%;padding:11px 14px;border:1.5px solid #e0e0e0;border-radius:10px;font-family:'Inter',sans-serif;font-size:14px;color:#333;background:#fff;outline:none;transition:border-color .2s,box-shadow .2s}}
        input[type=text]:focus,textarea:focus{{border-color:#c8384f;box-shadow:0 0 0 3px rgba(200,56,79,.1)}}
        textarea{{resize:vertical;min-height:110px}}
        .upload-area{{border:2px dashed #e0c0c8;border-radius:12px;padding:22px;text-align:center;cursor:pointer;background:#fff8f9;position:relative;transition:border-color .2s,background .2s}}
        .upload-area:hover{{border-color:#c8384f;background:#fff0f3}}
        .upload-area input{{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}}
        #preview{{display:none;width:100%;border-radius:8px;margin-top:10px;max-height:180px;object-fit:cover}}
        .beneficios{{display:flex;gap:8px;margin-bottom:18px}}
        .bene{{flex:1;background:#fff8f9;border:1px solid #f0d0d8;border-radius:10px;padding:10px 6px;text-align:center}}
        .bene-icon{{font-size:18px;margin-bottom:3px}}
        .bene-txt{{font-size:10px;color:#a06070;line-height:1.3}}
        .btn{{width:100%;padding:16px;background:linear-gradient(135deg,#c8384f,#e8526a);color:#fff;border:none;border-radius:14px;font-family:'Playfair Display',serif;font-size:17px;cursor:pointer;letter-spacing:.5px;box-shadow:0 6px 20px rgba(200,56,79,.4);transition:opacity .2s,transform .1s}}
        .btn:hover{{opacity:.92;transform:translateY(-1px)}}
        .btn:disabled{{opacity:.6;cursor:not-allowed;transform:none}}
        .btn-sub{{text-align:center;font-size:12px;color:#aaa;margin-top:8px}}
        .prova{{display:flex;align-items:center;gap:10px;margin-top:16px;padding:12px 14px;background:#fff8f9;border-radius:10px;border:1px solid #f0d0d8}}
        .avs{{display:flex}}
        .av{{width:26px;height:26px;border-radius:50%;border:2px solid #fff;margin-right:-7px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;font-weight:600}}
        .prova-txt{{font-size:12px;color:#a06070;line-height:1.4}}
        .prova-txt strong{{color:#7a1530}}
        .contador{{text-align:right;font-size:11px;color:#c8384f;margin-top:3px;opacity:.7}}
    </style>
</head>
<body>
<div class="page">
    <div class="urgency">
        <span>💌 <strong>Momentos Especiais</strong> — Porque amor não precisa de data</span>
    </div>
    <div class="card">
        <div class="hero">
            <div class="badge"><div class="dot"></div><span id="online-count">43 pessoas criando agora</span></div>
            <h1>Crie uma mensagem que nunca será esquecida 💖</h1>
            <p class="hero-sub">Uma página exclusiva com foto, carta e QR Code — pronta em minutos</p>
            <div class="frase-especial">
                <p>"Não precisa de uma data especial para dizer o quanto você ama alguém. O melhor momento é agora."</p>
            </div>
        </div>

        <div class="corpo">
            <div class="section-title">🎨 Escolha o tema</div>
            <div class="temas-grid" id="temas-grid">
                {temas_html}
            </div>

            <div class="campo">
                <label>📸 Foto especial</label>
                <div class="upload-area">
                    <input type="file" id="foto" accept="image/*" onchange="previewFoto(this)">
                    <div id="up-content">
                        <div style="font-size:28px;margin-bottom:6px">📷</div>
                        <div style="font-size:13px;color:#a06070">Toque para escolher uma foto<br><small>JPG, PNG ou GIF · Máx. 5MB</small></div>
                    </div>
                    <img id="preview" alt="Preview">
                </div>
            </div>

            <div class="campo">
                <label>💌 Para quem é?</label>
                <input type="text" id="destinatario" placeholder="Nome de quem vai receber" maxlength="60">
            </div>

            <div class="campo">
                <label>✍️ Sua mensagem</label>
                <textarea id="carta" placeholder="Escreva do coração..." maxlength="2000" oninput="document.getElementById('cont').textContent=this.value.length"></textarea>
                <div class="contador"><span id="cont">0</span>/2000</div>
            </div>

            <div class="campo">
                <label>💕 Seu nome</label>
                <input type="text" id="remetente" placeholder="Seu nome (opcional)" maxlength="60">
            </div>

            <div class="beneficios">
                <div class="bene"><div class="bene-icon">🔗</div><div class="bene-txt">Link exclusivo para compartilhar</div></div>
                <div class="bene"><div class="bene-icon">📱</div><div class="bene-txt">QR Code para imprimir</div></div>
                <div class="bene"><div class="bene-icon">♾️</div><div class="bene-txt">Página permanente</div></div>
            </div>

            <button class="btn" id="btn" onclick="criar()">💖 Criar minha mensagem especial</button>
            <div class="btn-sub">🔒 100% seguro e gratuito para testar</div>

            <div class="prova">
                <div class="avs">
                    <div class="av" style="background:linear-gradient(135deg,#e8526a,#c8384f)">M</div>
                    <div class="av" style="background:linear-gradient(135deg,#8b1a30,#c8384f)">J</div>
                    <div class="av" style="background:linear-gradient(135deg,#c8384f,#a8425c)">A</div>
                </div>
                <div class="prova-txt"><strong>+3.200 pessoas</strong> já surpreenderam<br>alguém especial com Momentos Especiais</div>
            </div>

            <div id="resultado" style="display:none;margin-top:24px;background:linear-gradient(135deg,#fff0f3,#ffe8ed);border:1.5px solid #e8b4bc;border-radius:14px;padding:24px;text-align:center">
                <div style="font-size:40px;margin-bottom:10px">🎉</div>
                <h2 style="font-family:'Playfair Display',serif;color:#7a1530;margin-bottom:8px">Mensagem criada!</h2>
                <p style="font-size:13px;color:#a06070;margin-bottom:14px">Compartilhe o link ou QR Code com quem você ama 💕</p>
                <div id="linkBox" onclick="copiar()" style="background:#fff;border:1px solid #e8b4bc;border-radius:8px;padding:10px 14px;font-size:13px;color:#c8384f;word-break:break-all;margin-bottom:12px;cursor:pointer">—</div>
                <img id="qr-img" src="" style="width:150px;height:150px;border:4px solid #fff;border-radius:10px;box-shadow:0 4px 15px rgba(0,0,0,.1);margin:0 auto 12px;display:block" alt="QR Code">
                <button onclick="copiar()" style="background:#fff;color:#c8384f;border:1.5px solid #e8b4bc;border-radius:8px;padding:9px 20px;font-size:14px;cursor:pointer;margin:4px;font-family:'Inter',sans-serif">📋 Copiar link</button>
                <a id="btnAbrir" href="#" target="_blank"><button style="background:#c8384f;color:#fff;border:none;border-radius:8px;padding:9px 20px;font-size:14px;cursor:pointer;margin:4px;font-family:'Inter',sans-serif">🔗 Ver página</button></a>
                <p id="avisoCopiado" style="display:none;font-size:12px;color:#c8384f;margin-top:6px">✔ Link copiado!</p>
            </div>
        </div>
    </div>
</div>

<script>
let temaSelecionado = 'amor';

function selecionarTema(el) {{
    document.querySelectorAll('.tema').forEach(t => t.style.borderColor = 'transparent');
    temaSelecionado = el.dataset.tema;
    el.style.borderColor = '#333';
}}

function previewFoto(input) {{
    const file = input.files[0]; if (!file) return;
    const r = new FileReader();
    r.onload = e => {{
        document.getElementById('preview').src = e.target.result;
        document.getElementById('preview').style.display = 'block';
        document.getElementById('up-content').style.display = 'none';
    }};
    r.readAsDataURL(file);
}}

async function criar() {{
    const foto = document.getElementById('foto').files[0];
    const carta = document.getElementById('carta').value.trim();
    const btn = document.getElementById('btn');
    if (!foto) {{ alert('Por favor, escolha uma foto! 📸'); return; }}
    if (!carta) {{ alert('Por favor, escreva uma mensagem! 💌'); return; }}
    btn.disabled = true; btn.textContent = '⏳ Criando sua mensagem...';
    const form = new FormData();
    form.append('file', foto); form.append('carta', carta);
    form.append('nome_destinatario', document.getElementById('destinatario').value.trim());
    form.append('nome_remetente', document.getElementById('remetente').value.trim());
    form.append('tema', temaSelecionado);
    try {{
        const res = await fetch('/criar', {{method:'POST',body:form}});
        const data = await res.json();
        if (data.status === 'ok') {{
            document.getElementById('linkBox').textContent = data.pagina;
            document.getElementById('qr-img').src = data.qr_code;
            document.getElementById('btnAbrir').href = data.pagina;
            document.getElementById('resultado').style.display = 'block';
            document.getElementById('resultado').scrollIntoView({{behavior:'smooth'}});
        }} else {{ alert('Erro: ' + (data.detail || data.mensagem || 'Tente novamente.')); }}
    }} catch(e) {{ alert('Erro de conexão. Tente novamente.'); }}
    finally {{ btn.disabled = false; btn.textContent = '💖 Criar minha mensagem especial'; }}
}}

function copiar() {{
    const link = document.getElementById('linkBox').textContent;
    navigator.clipboard.writeText(link).then(() => {{
        const a = document.getElementById('avisoCopiado');
        a.style.display = 'block';
        setTimeout(() => a.style.display = 'none', 2500);
    }});
}}

// Contador animado
const counts = [38,41,43,45,42,44,47,43,46,48];
let ci = 0;
setInterval(() => {{
    ci = (ci+1) % counts.length;
    document.getElementById('online-count').textContent = counts[ci] + ' pessoas criando agora';
}}, 4000);
</script>
</body>
</html>"""


@app.post("/criar")
async def criar(
    file: UploadFile,
    carta: str = Form(...),
    nome_remetente: str = Form(default=""),
    nome_destinatario: str = Form(default=""),
    tema: str = Form(default="amor"),
):
    if file.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido.")
    conteudo = await file.read()
    if len(conteudo) > TAMANHO_MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo: 5MB.")
    carta_limpa = carta.strip()
    if not carta_limpa:
        raise HTTPException(status_code=400, detail="A carta não pode estar vazia.")
    if tema not in TEMAS:
        tema = "amor"

    codigo = str(uuid.uuid4())[:8]
    exts = {"image/jpeg":"jpg","image/png":"png","image/webp":"webp","image/gif":"gif"}
    ext = exts.get(file.content_type, "jpg")

    with open(f"uploads/{codigo}.{ext}", "wb") as f:
        f.write(conteudo)

    banco = carregar_banco()
    banco[codigo] = {
        "carta": carta_limpa,
        "nome_remetente": nome_remetente.strip(),
        "nome_destinatario": nome_destinatario.strip(),
        "extensao": ext,
        "tema": tema,
    }
    salvar_banco(banco)

    url = f"{BASE_URL}/p/{codigo}"
    img_qr = qrcode.make(url)
    img_qr.save(f"qrcodes/{codigo}.png")

    return {"status":"ok","codigo":codigo,"pagina":url,"qr_code":f"{BASE_URL}/qrcode/{codigo}"}


@app.get("/qrcode/{codigo}")
def get_qrcode(codigo: str):
    caminho = f"qrcodes/{codigo}.png"
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="QR Code não encontrado.")
    return FileResponse(caminho, media_type="image/png")


@app.get("/p/{codigo}", response_class=HTMLResponse)
def pagina(codigo: str):
    banco = carregar_banco()
    dados = banco.get(codigo)
    if not dados:
        return _pagina_erro("Página não encontrada", "Este link não existe ou expirou.")
    ext = dados.get("extensao", "jpg")
    if not os.path.exists(f"uploads/{codigo}.{ext}"):
        return _pagina_erro("Imagem não encontrada", "A imagem desta mensagem foi removida.")

    tema_key = dados.get("tema", "amor")
    t = TEMAS.get(tema_key, TEMAS["amor"])
    nome_dest = dados.get("nome_destinatario", "")
    nome_rem = dados.get("nome_remetente", "")
    carta = dados["carta"]
    titulo = f"Para {nome_dest} {t['emoji']}" if nome_dest else f"{t['emoji']} Uma mensagem especial"
    fonte = t['fonte']
cor2 = t['cor2']
assinatura = f"<p style='font-family:{fonte},serif;font-size:15px;color:{cor2};text-align:right;margin-top:8px;font-style:italic'>Com amor, {nome_rem} 💕</p>" if nome_rem else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{titulo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
    <style>
        *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
        body{{min-height:100vh;background:{t['bg']};display:flex;align-items:center;justify-content:center;padding:24px 16px;font-family:'{t['fonte']}',Georgia,serif;overflow-x:hidden}}
        body::before{{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 60% at 20% 10%,{t['cor1']}33 0%,transparent 60%),radial-gradient(ellipse 60% 80% at 80% 90%,{t['cor1']}22 0%,transparent 60%);pointer-events:none;z-index:0}}
        .envelope{{position:relative;z-index:1;background:linear-gradient(160deg,{t['grad1']},{t['grad2']});max-width:420px;width:100%;border-radius:4px 4px 28px 28px;box-shadow:0 2px 0 {t['cor1']},0 4px 0 {t['cor2']},0 30px 60px rgba(0,0,0,.5);overflow:hidden;animation:r .8s cubic-bezier(.22,1,.36,1) both}}
        @keyframes r{{from{{opacity:0;transform:translateY(40px) scale(.96)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
        .topo{{background:{t['topo']};padding:10px;text-align:center;letter-spacing:4px;font-size:13px;color:rgba(255,255,255,.9);font-family:'{t['fonte']}',serif;font-style:italic}}
        .foto-wrapper{{padding:24px 24px 0;position:relative}}
        .foto-frame{{border-radius:6px;overflow:hidden;box-shadow:0 8px 24px {t['cor1']}44,0 0 0 3px {t['borda']},0 0 0 6px #fff}}
        .foto-frame img{{width:100%;display:block;border-radius:4px}}
        .coracao{{position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);width:36px;height:36px;background:{t['cor1']};clip-path:path('M18 32 C18 32 2 22 2 12 C2 6.5 6.5 2 12 2 C14.5 2 17 3.5 18 5.5 C19 3.5 21.5 2 24 2 C29.5 2 34 6.5 34 12 C34 22 18 32 18 32 Z');box-shadow:0 4px 12px {t['cor1']}66;animation:p 1.8s ease-in-out infinite}}
        @keyframes p{{0%,100%{{transform:translateX(-50%) scale(1)}}50%{{transform:translateX(-50%) scale(1.12)}}}}
        .conteudo{{padding:36px 28px 28px;text-align:center}}
        .titulo{{font-family:'{t['fonte']}',serif;font-size:22px;color:{t['cor3']};margin-bottom:20px;line-height:1.3}}
        .divisor{{display:flex;align-items:center;gap:10px;margin:0 auto 20px;width:80%;color:{t['cor1']};font-size:13px;opacity:.6}}
        .divisor::before,.divisor::after{{content:'';flex:1;height:1px;background:currentColor}}
        .carta{{font-size:16px;line-height:1.9;color:{t['texto']};white-space:pre-line;font-style:italic;text-align:left;padding:20px;background:{t['fundo_carta']};border-left:3px solid {t['cor1']};border-radius:0 8px 8px 0;margin-bottom:20px}}
        .rodape{{background:{t['topo']};padding:10px;text-align:center;font-size:18px;letter-spacing:6px;opacity:.85}}
    </style>
</head>
<body>
    <div class="envelope">
        <div class="topo">momentos especiais</div>
        <div class="foto-wrapper">
            <div class="foto-frame"><img src="/uploads/{codigo}.{ext}" alt="Foto especial"></div>
            <div class="coracao"></div>
        </div>
        <div class="conteudo">
            <h1 class="titulo">{titulo}</h1>
            <div class="divisor">{t['emoji']}</div>
            <div class="carta">{carta}</div>
            {assinatura}
        </div>
        <div class="rodape">{t['emoji']} ♥ {t['emoji']}</div>
    </div>
</body>
</html>"""


def _pagina_erro(titulo, mensagem):
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Erro</title>
<style>body{{background:#0d0608;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}}.box{{text-align:center;padding:40px}}h1{{font-size:28px;margin-bottom:12px}}p{{opacity:.7}}</style>
</head><body><div class="box"><div style="font-size:48px">💔</div><h1>{titulo}</h1><p>{mensagem}</p></div></body></html>"""

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os
import json
import qrcode
from pathlib import Path

app = FastAPI()

# ─── Configuração ────────────────────────────────────────────────────────────
BASE_URL = "https://momentosespeciais-production.up.railway.app" # ⚠️ Troque pelo seu link real
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
TAMANHO_MAX_MB = 5

# ─── Pastas ───────────────────────────────────────────────────────────────────
for pasta in ["uploads", "qrcodes", "dados"]:
    os.makedirs(pasta, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ─── Persistência simples em JSON ─────────────────────────────────────────────
DB_PATH = Path("dados/banco.json")

def carregar_banco() -> dict:
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_banco(banco: dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=2)

# ─── Rotas ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💖 Crie sua mensagem especial</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            min-height: 100vh;
            background: #1a0a10;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 16px;
            font-family: 'Lora', Georgia, serif;
        }

        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 60% at 20% 10%, rgba(180,30,60,0.25) 0%, transparent 60%),
                radial-gradient(ellipse 60% 80% at 80% 90%, rgba(200,40,80,0.2) 0%, transparent 60%);
            pointer-events: none;
            z-index: 0;
        }

        .card {
            position: relative;
            z-index: 1;
            background: linear-gradient(160deg, #fff8f8 0%, #fff0f3 50%, #ffe8ed 100%);
            max-width: 480px;
            width: 100%;
            border-radius: 4px 4px 28px 28px;
            box-shadow:
                0 2px 0 #c8637a,
                0 4px 0 #a8425c,
                0 30px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            animation: revelar 0.7s cubic-bezier(0.22,1,0.36,1) both;
        }

        @keyframes revelar {
            from { opacity: 0; transform: translateY(30px) scale(0.97); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
        }

        .topo {
            background: linear-gradient(90deg, #8b1a30, #c8384f, #e8526a, #c8384f, #8b1a30);
            padding: 12px;
            text-align: center;
            letter-spacing: 4px;
            font-size: 13px;
            color: rgba(255,220,225,0.9);
            font-family: 'Playfair Display', serif;
            font-style: italic;
        }

        .corpo {
            padding: 32px 32px 28px;
        }

        h1 {
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            color: #7a1530;
            text-align: center;
            margin-bottom: 6px;
        }

        .subtitulo {
            text-align: center;
            font-size: 14px;
            color: #a06070;
            margin-bottom: 28px;
            font-style: italic;
        }

        .campo {
            margin-bottom: 18px;
        }

        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #7a1530;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        input[type="text"],
        textarea {
            width: 100%;
            padding: 12px 14px;
            border: 1.5px solid #e8b4bc;
            border-radius: 10px;
            font-family: 'Lora', serif;
            font-size: 15px;
            color: #4a2030;
            background: #fff;
            transition: border-color 0.2s, box-shadow 0.2s;
            outline: none;
        }

        input[type="text"]:focus,
        textarea:focus {
            border-color: #c8384f;
            box-shadow: 0 0 0 3px rgba(200,56,79,0.12);
        }

        textarea {
            resize: vertical;
            min-height: 120px;
        }

        .upload-area {
            border: 2px dashed #e8b4bc;
            border-radius: 10px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s, background 0.2s;
            background: #fff;
            position: relative;
        }

        .upload-area:hover {
            border-color: #c8384f;
            background: #fff8f9;
        }

        .upload-area input[type="file"] {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
            width: 100%;
            height: 100%;
        }

        .upload-icone { font-size: 32px; margin-bottom: 8px; }

        .upload-texto {
            font-size: 14px;
            color: #a06070;
            font-style: italic;
        }

        #preview {
            display: none;
            width: 100%;
            border-radius: 8px;
            margin-top: 12px;
            max-height: 200px;
            object-fit: cover;
        }

        .contador {
            text-align: right;
            font-size: 12px;
            color: #c8384f;
            margin-top: 4px;
            opacity: 0.7;
        }

        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #c8384f, #e8526a);
            color: white;
            border: none;
            border-radius: 12px;
            font-family: 'Playfair Display', serif;
            font-size: 17px;
            cursor: pointer;
            margin-top: 8px;
            letter-spacing: 1px;
            transition: opacity 0.2s, transform 0.1s;
            box-shadow: 0 4px 15px rgba(200,56,79,0.4);
        }

        .btn:hover  { opacity: 0.92; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        /* Resultado */
        #resultado {
            display: none;
            margin-top: 24px;
            background: linear-gradient(135deg, #fff0f3, #ffe8ed);
            border: 1.5px solid #e8b4bc;
            border-radius: 14px;
            padding: 24px;
            text-align: center;
            animation: revelar 0.5s ease both;
        }

        #resultado h2 {
            font-family: 'Playfair Display', serif;
            color: #7a1530;
            font-size: 20px;
            margin-bottom: 14px;
        }

        .link-box {
            background: white;
            border: 1px solid #e8b4bc;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #c8384f;
            word-break: break-all;
            margin-bottom: 12px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .link-box:hover { background: #fff5f7; }

        #qr-img {
            width: 160px;
            height: 160px;
            border: 4px solid white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            margin: 8px auto 12px;
            display: block;
        }

        .btn-copiar {
            background: white;
            color: #c8384f;
            border: 1.5px solid #e8b4bc;
            border-radius: 8px;
            padding: 9px 20px;
            font-size: 14px;
            cursor: pointer;
            margin: 4px;
            font-family: 'Lora', serif;
            transition: background 0.15s;
        }
        .btn-copiar:hover { background: #fff0f3; }

        .rodape {
            background: linear-gradient(90deg, #8b1a30, #c8384f, #8b1a30);
            padding: 10px;
            text-align: center;
            font-size: 18px;
            letter-spacing: 6px;
        }

        .aviso { font-size: 12px; color: #a06070; margin-top: 6px; }
    </style>
</head>
<body>
<div class="card">
    <div class="topo">amor &amp; carinho</div>

    <div class="corpo">
        <h1>💖 Crie sua mensagem</h1>
        <p class="subtitulo">Uma surpresa inesquecível para quem você ama</p>

        <div class="campo">
            <label>📸 Foto do casal</label>
            <div class="upload-area" id="uploadArea">
                <input type="file" id="foto" accept="image/*" onchange="previewFoto(this)">
                <div class="upload-icone">📷</div>
                <div class="upload-texto">Toque aqui para escolher uma foto<br><small>JPG, PNG ou GIF · Máx. 5MB</small></div>
            </div>
            <img id="preview" alt="Preview">
        </div>

        <div class="campo">
            <label>💌 Para quem é?</label>
            <input type="text" id="destinatario" placeholder="Nome de quem vai receber" maxlength="60">
        </div>

        <div class="campo">
            <label>✍️ Sua mensagem</label>
            <textarea id="carta" placeholder="Escreva sua mensagem de amor aqui..." maxlength="2000" oninput="atualizarContador()"></textarea>
            <div class="contador"><span id="cont">0</span>/2000 caracteres</div>
        </div>

        <div class="campo">
            <label>💕 Seu nome</label>
            <input type="text" id="remetente" placeholder="Seu nome (opcional)" maxlength="60">
        </div>

        <button class="btn" id="btnEnviar" onclick="criarCartao()">💖 Criar mensagem especial</button>

        <div id="resultado">
            <h2>✅ Mensagem criada!</h2>
            <p style="font-size:14px;color:#a06070;margin-bottom:12px;">Compartilhe o link ou QR Code com quem você ama 💕</p>
            <div class="link-box" id="linkBox" onclick="copiarLink()">—</div>
            <img id="qr-img" src="" alt="QR Code">
            <br>
            <button class="btn-copiar" onclick="copiarLink()">📋 Copiar link</button>
            <a id="btnAbrir" href="#" target="_blank"><button class="btn-copiar">🔗 Abrir página</button></a>
            <p class="aviso" id="avisoCopiado" style="display:none;color:#c8384f;">✔ Link copiado!</p>
        </div>
    </div>

    <div class="rodape">💕 ♥ 💕</div>
</div>

<script>
    function previewFoto(input) {
        const file = input.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = e => {
            const img = document.getElementById('preview');
            img.src = e.target.result;
            img.style.display = 'block';
            document.querySelector('.upload-icone').style.display = 'none';
            document.querySelector('.upload-texto').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    function atualizarContador() {
        document.getElementById('cont').textContent =
            document.getElementById('carta').value.length;
    }

    async function criarCartao() {
        const foto        = document.getElementById('foto').files[0];
        const carta       = document.getElementById('carta').value.trim();
        const destinatario = document.getElementById('destinatario').value.trim();
        const remetente   = document.getElementById('remetente').value.trim();
        const btn         = document.getElementById('btnEnviar');

        if (!foto)  { alert('Por favor, escolha uma foto! 📸'); return; }
        if (!carta) { alert('Por favor, escreva uma mensagem! 💌'); return; }

        btn.disabled    = true;
        btn.textContent = '⏳ Criando sua mensagem...';

        const form = new FormData();
        form.append('file', foto);
        form.append('carta', carta);
        form.append('nome_destinatario', destinatario);
        form.append('nome_remetente', remetente);

        try {
            const res  = await fetch('/criar', { method: 'POST', body: form });
            const data = await res.json();

            if (data.status === 'ok') {
                document.getElementById('linkBox').textContent = data.pagina;
                document.getElementById('qr-img').src = data.qr_code;
                document.getElementById('btnAbrir').href = data.pagina;
                document.getElementById('resultado').style.display = 'block';
                document.getElementById('resultado').scrollIntoView({ behavior: 'smooth' });
            } else {
                alert('Erro: ' + (data.detail || data.mensagem || 'Tente novamente.'));
            }
        } catch (e) {
            alert('Erro de conexão. Verifique se o servidor está rodando.');
        } finally {
            btn.disabled    = false;
            btn.textContent = '💖 Criar mensagem especial';
        }
    }

    function copiarLink() {
        const link = document.getElementById('linkBox').textContent;
        navigator.clipboard.writeText(link).then(() => {
            const aviso = document.getElementById('avisoCopiado');
            aviso.style.display = 'block';
            setTimeout(() => aviso.style.display = 'none', 2500);
        });
    }
</script>
</body>
</html>"""


@app.post("/criar")
async def criar(
    file: UploadFile,
    carta: str = Form(...),
    nome_remetente: str = Form(default=""),
    nome_destinatario: str = Form(default=""),
):
    # Validar tipo de arquivo
    if file.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não permitido: {file.content_type}. Use JPG, PNG, WEBP ou GIF."
        )

    # Validar tamanho
    conteudo = await file.read()
    if len(conteudo) > TAMANHO_MAX_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Máximo permitido: {TAMANHO_MAX_MB}MB."
        )

    # Validar carta
    carta_limpa = carta.strip()
    if not carta_limpa:
        raise HTTPException(status_code=400, detail="A carta não pode estar vazia.")
    if len(carta_limpa) > 2000:
        raise HTTPException(status_code=400, detail="A carta é muito longa. Máximo: 2000 caracteres.")

    # Gerar código único
    codigo = str(uuid.uuid4())[:8]

    # Detectar extensão correta
    extensoes = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    ext = extensoes.get(file.content_type, "jpg")
    caminho_img = f"uploads/{codigo}.{ext}"

    # Salvar imagem
    with open(caminho_img, "wb") as f:
        f.write(conteudo)

    # Salvar no banco
    banco = carregar_banco()
    banco[codigo] = {
        "carta": carta_limpa,
        "nome_remetente": nome_remetente.strip(),
        "nome_destinatario": nome_destinatario.strip(),
        "extensao": ext,
    }
    salvar_banco(banco)

    # Gerar QR Code
    url = f"{BASE_URL}/p/{codigo}"
    caminho_qr = f"qrcodes/{codigo}.png"
    img_qr = qrcode.make(url)
    img_qr.save(caminho_qr)

    return {
        "status": "ok",
        "codigo": codigo,
        "pagina": url,
        "qr_code": f"{BASE_URL}/qrcode/{codigo}",
    }


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
    caminho_img = f"uploads/{codigo}.{ext}"

    if not os.path.exists(caminho_img):
        return _pagina_erro("Imagem não encontrada", "A imagem desta mensagem foi removida.")

    nome_dest = dados.get("nome_destinatario", "")
    nome_rem = dados.get("nome_remetente", "")
    carta = dados["carta"]

    titulo = f"Para {nome_dest} 💖" if nome_dest else "💖 Uma mensagem especial"
    assinatura = f"<p class='assinatura'>Com amor, {nome_rem} 💕</p>" if nome_rem else ""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            min-height: 100vh;
            background: #1a0a10;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            font-family: 'Lora', Georgia, serif;
            overflow-x: hidden;
        }}

        /* Pétalas de fundo */
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse 80% 60% at 20% 10%, rgba(180, 30, 60, 0.25) 0%, transparent 60%),
                radial-gradient(ellipse 60% 80% at 80% 90%, rgba(200, 40, 80, 0.2) 0%, transparent 60%),
                radial-gradient(ellipse 40% 40% at 60% 40%, rgba(255, 100, 130, 0.08) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}

        .envelope {{
            position: relative;
            z-index: 1;
            background: linear-gradient(160deg, #fff8f8 0%, #fff0f3 50%, #ffe8ed 100%);
            max-width: 420px;
            width: 100%;
            border-radius: 4px 4px 28px 28px;
            box-shadow:
                0 2px 0 #c8637a,
                0 4px 0 #a8425c,
                0 30px 60px rgba(0,0,0,0.5),
                0 0 0 1px rgba(200, 100, 120, 0.2);
            overflow: hidden;
            animation: revelar 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}

        @keyframes revelar {{
            from {{ opacity: 0; transform: translateY(40px) scale(0.96); }}
            to   {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        /* Faixa superior decorativa */
        .topo {{
            background: linear-gradient(90deg, #8b1a30, #c8384f, #e8526a, #c8384f, #8b1a30);
            padding: 10px;
            text-align: center;
            letter-spacing: 4px;
            font-size: 13px;
            color: rgba(255,220,225,0.9);
            font-family: 'Playfair Display', serif;
            font-style: italic;
        }}

        .foto-wrapper {{
            padding: 24px 24px 0;
            position: relative;
        }}

        .foto-frame {{
            position: relative;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(140, 30, 50, 0.3), 0 0 0 3px #e8b4bc, 0 0 0 6px #fff;
        }}

        .foto-frame img {{
            width: 100%;
            display: block;
            border-radius: 4px;
        }}

        .coracao-central {{
            position: absolute;
            bottom: -18px;
            left: 50%;
            transform: translateX(-50%);
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #e8526a, #c8384f);
            clip-path: path('M18 32 C18 32 2 22 2 12 C2 6.5 6.5 2 12 2 C14.5 2 17 3.5 18 5.5 C19 3.5 21.5 2 24 2 C29.5 2 34 6.5 34 12 C34 22 18 32 18 32 Z');
            box-shadow: 0 4px 12px rgba(200, 56, 79, 0.5);
            animation: pulsar 1.8s ease-in-out infinite;
        }}

        @keyframes pulsar {{
            0%, 100% {{ transform: translateX(-50%) scale(1); }}
            50%       {{ transform: translateX(-50%) scale(1.12); }}
        }}

        .conteudo {{
            padding: 36px 28px 28px;
            text-align: center;
        }}

        .titulo {{
            font-family: 'Playfair Display', serif;
            font-size: 22px;
            color: #7a1530;
            margin-bottom: 20px;
            line-height: 1.3;
        }}

        .divisor {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 auto 20px;
            width: 80%;
            color: #c8384f;
            font-size: 13px;
            opacity: 0.6;
        }}
        .divisor::before, .divisor::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: currentColor;
        }}

        .carta {{
            font-size: 16px;
            line-height: 1.9;
            color: #4a2030;
            white-space: pre-line;
            font-style: italic;
            text-align: left;
            padding: 20px;
            background: rgba(255, 200, 210, 0.15);
            border-left: 3px solid #e8526a;
            border-radius: 0 8px 8px 0;
            margin-bottom: 20px;
        }}

        .assinatura {{
            font-family: 'Playfair Display', serif;
            font-size: 15px;
            color: #a83050;
            text-align: right;
            margin-top: 8px;
            font-style: italic;
        }}

        .rodape {{
            background: linear-gradient(90deg, #8b1a30, #c8384f, #8b1a30);
            padding: 10px;
            text-align: center;
            font-size: 18px;
            letter-spacing: 6px;
            opacity: 0.85;
        }}
    </style>
</head>
<body>
    <div class="envelope">
        <div class="topo">amor &amp; carinho</div>

        <div class="foto-wrapper">
            <div class="foto-frame">
                <img src="/uploads/{codigo}.{ext}" alt="Foto especial">
            </div>
            <div class="coracao-central"></div>
        </div>

        <div class="conteudo">
            <h1 class="titulo">{titulo}</h1>
            <div class="divisor">♥</div>
            <div class="carta">{carta}</div>
            {assinatura}
        </div>

        <div class="rodape">💕 ♥ 💕</div>
    </div>
</body>
</html>"""


def _pagina_erro(titulo: str, mensagem: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Erro</title>
    <style>
        body {{ background:#1a0a10; color:#fff; font-family:sans-serif;
               display:flex; align-items:center; justify-content:center; min-height:100vh; }}
        .box {{ text-align:center; padding:40px; }}
        h1 {{ font-size:28px; margin-bottom:12px; }}
        p  {{ opacity:.7; }}
    </style>
</head>
<body>
    <div class="box">
        <div style="font-size:48px">💔</div>
        <h1>{titulo}</h1>
        <p>{mensagem}</p>
    </div>
</body>
</html>"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import uuid
import yt_dlp

app = Flask(__name__)
app.secret_key = "videohelp-dev-key"

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PLATFORMS = {
    "instagram": {
        "name": "Instagram",
        "color": "instagram",
        "steps": [
            "Abra o vídeo ou Reel no Instagram.",
            "Toque em Compartilhar.",
            "Escolha “Copiar link”.",
            "Volte para o VideoHelp e toque em “OK, já copiei o link”."
        ]
    },
    "facebook": {
        "name": "Facebook",
        "color": "facebook",
        "steps": [
            "Abra o vídeo no Facebook.",
            "Toque em Compartilhar.",
            "Escolha “Copiar link”.",
            "Volte para o VideoHelp e toque em “OK, já copiei o link”."
        ]
    },
    "tiktok": {
        "name": "TikTok",
        "color": "tiktok",
        "steps": [
            "Abra o vídeo no TikTok.",
            "Toque em Compartilhar.",
            "Escolha “Copiar link”.",
            "Volte para o VideoHelp e toque em “OK, já copiei o link”."
        ]
    }
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/instrucoes/<platform>")
def instructions(platform):
    if platform not in PLATFORMS:
        return redirect(url_for("home"))
    return render_template("instructions.html", platform=PLATFORMS[platform], key=platform)

@app.route("/baixar/<platform>", methods=["GET", "POST"])
def downloader(platform):
    if platform not in PLATFORMS:
        return redirect(url_for("home"))

    if request.method == "POST":
        video_url = request.form.get("video_url", "").strip()

        if not video_url:
            flash("Cole o link do vídeo primeiro.")
            return redirect(url_for("downloader", platform=platform))

        # O site aceita apenas URLs públicas. Não tente usar links privados,
        # conteúdo protegido por login ou qualquer forma de DRM.
        allowed_hosts = {
            "instagram": ("instagram.com", "www.instagram.com"),
            "facebook": ("facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch"),
            "tiktok": ("tiktok.com", "www.tiktok.com", "vm.tiktok.com")
        }

        if not any(host in video_url.lower() for host in allowed_hosts[platform]):
            flash(f"Esse link não parece ser um link do {PLATFORMS[platform]['name']}.")
            return redirect(url_for("downloader", platform=platform))

        job_id = str(uuid.uuid4())
        output_template = os.path.join(DOWNLOAD_DIR, job_id + ".%(ext)s")

        try:
            options = {
                "outtmpl": output_template,
                "format": "best[ext=mp4]/best",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "restrictfilenames": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    # Algumas combinações de formato/extensão podem alterar o nome.
                    candidates = [
                        os.path.join(DOWNLOAD_DIR, f)
                        for f in os.listdir(DOWNLOAD_DIR)
                        if f.startswith(job_id + ".")
                    ]
                    if not candidates:
                        raise FileNotFoundError("Arquivo baixado não foi localizado.")
                    filename = candidates[0]

            return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

        except Exception as exc:
            # Não exibimos detalhes técnicos para o visitante.
            app.logger.exception("Falha ao baixar vídeo: %s", exc)
            flash("Não foi possível baixar esse vídeo. O link pode ser privado, indisponível ou não ser compatível.")
            return redirect(url_for("downloader", platform=platform))

    return render_template("downloader.html", platform=PLATFORMS[platform], key=platform)

if __name__ == "__main__":
    app.run(debug=True)

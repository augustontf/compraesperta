"""Lê as últimas ofertas públicas do canal do Telegram e grava ofertas.json para a página."""
import json
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

CANAL = "compraesperta_ofertas"
QTD = 6


def preco(txt, rotulo):
    m = re.search(rotulo + r"\s*R\$\s*([\d\.]+,\d{2})", txt)
    return m.group(1) if m else ""


def main():
    r = requests.get(f"https://t.me/s/{CANAL}", timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 (compatible; CompraEspertaBot/1.0)"})
    r.raise_for_status()
    sopa = BeautifulSoup(r.text, "html.parser")
    ofertas = []
    for msg in reversed(sopa.select(".tgme_widget_message")):
        texto_el = msg.select_one(".tgme_widget_message_text")
        foto_el = msg.select_one(".tgme_widget_message_photo_wrap")
        if not texto_el or not foto_el:
            continue
        texto = texto_el.get_text("\n")
        titulo = next((l.replace("👉", "").strip() for l in texto.split("\n") if l.strip().startswith("👉")), "")
        link = next((a["href"] for a in texto_el.select("a[href]") if "shope" in a["href"]), "")
        m_img = re.search(r"url\('([^']+)'\)", foto_el.get("style", ""))
        por = preco(texto, "Por")
        if not (titulo and link and m_img and por):
            continue
        desc = re.search(r"\((\d+)% OFF\)", texto)
        data = msg.select_one("time[datetime]")
        ofertas.append({
            "titulo": titulo[:90],
            "de": preco(texto, "De"),
            "por": por,
            "off": desc.group(1) if desc else "",
            "imagem": m_img.group(1),
            "link": link,
            "quando": data["datetime"] if data else "",
        })
        if len(ofertas) >= QTD:
            break
    if not ofertas:
        print("Nenhuma oferta encontrada; mantendo o arquivo anterior.")
        return 0
    saida = {"atualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ofertas": ofertas}
    with open("ofertas.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print(f"{len(ofertas)} ofertas gravadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

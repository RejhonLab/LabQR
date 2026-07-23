from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote, urlparse

import qrcode
from qrcode.constants import ERROR_CORRECT_M


BASE_DIR = Path(__file__).resolve().parent
PAGES_FILE = BASE_DIR / "pages.json"
QR_DIR = BASE_DIR / "QR"

# UPRAV TYTO DVĚ HODNOTY:
GITHUB_USER = "RejhonLab"
REPOSITORY = "LabQR"


def normalize_id(value: str) -> str:
    page_id = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]+", page_id):
        raise ValueError(
            "ID smí obsahovat pouze písmena A–Z, číslice, pomlčku a podtržítko."
        )
    return page_id


def validate_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError("Odkaz musí být úplná adresa začínající http:// nebo https://.")
    return url


def load_pages() -> dict[str, str]:
    if not PAGES_FILE.exists():
        return {}

    with PAGES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("pages.json musí obsahovat objekt ve tvaru ID: URL.")

    return {str(key).upper(): str(value) for key, value in data.items()}


def save_pages(pages: dict[str, str]) -> None:
    ordered_pages = dict(sorted(pages.items()))
    with PAGES_FILE.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(ordered_pages, file, ensure_ascii=False, indent=2)
        file.write("\n")


def build_redirect_url(page_id: str) -> str:
    if GITHUB_USER == "TVUJ_GITHUB_LOGIN":
        raise ValueError(
            "Nejprve v create_qr.py nastav proměnnou GITHUB_USER."
        )

    return (
        f"https://{GITHUB_USER}.github.io/{REPOSITORY}/"
        f"?id={quote(page_id)}"
    )


def create_qr(page_id: str, redirect_url: str) -> Path:
    QR_DIR.mkdir(exist_ok=True)
    output = QR_DIR / f"{page_id}.png"

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=16,
        border=4,
    )
    qr.add_data(redirect_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    image.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Přidá OneNote odkaz do pages.json a vytvoří QR kód."
    )
    parser.add_argument("id", help="Krátké ID, například AFM-001")
    parser.add_argument("url", help="Celý odkaz na stránku OneNote")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Přepíše existující ID.",
    )
    args = parser.parse_args()

    page_id = normalize_id(args.id)
    target_url = validate_url(args.url)
    pages = load_pages()

    if page_id in pages and not args.overwrite:
        raise SystemExit(
            f"ID {page_id} již existuje. Pro přepsání přidej --overwrite."
        )

    pages[page_id] = target_url
    save_pages(pages)

    redirect_url = build_redirect_url(page_id)
    qr_path = create_qr(page_id, redirect_url)

    print(f"ID:          {page_id}")
    print(f"QR adresa:   {redirect_url}")
    print(f"QR soubor:   {qr_path}")
    print("Nyní nahraj změněný pages.json a QR obrázek na GitHub.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Chyba: {exc}") from exc

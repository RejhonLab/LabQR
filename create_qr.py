from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

import qrcode
from qrcode.constants import ERROR_CORRECT_M


BASE_DIR = Path(__file__).resolve().parent
PAGES_FILE = BASE_DIR / "pages.json"
QR_DIR = BASE_DIR / "QR"

# Uprav podle svého repozitáře:
GITHUB_USER = "RejhonLab"
REPOSITORY = "LabQR"


def normalize_id(value: str) -> str:
    """Zkontroluje a sjednotí ID stránky."""
    page_id = value.strip().upper()

    if not re.fullmatch(r"[A-Z0-9_-]+", page_id):
        raise ValueError(
            "ID smí obsahovat pouze písmena A–Z, číslice, pomlčku "
            "a podtržítko."
        )

    return page_id


def validate_url(value: str) -> str:
    """Zkontroluje, že jde o úplnou HTTP/HTTPS adresu."""
    url = value.strip()
    parsed = urlparse(url)

    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError(
            "Odkaz musí být úplná adresa začínající "
            "http:// nebo https://."
        )

    return url


def load_pages() -> dict[str, str]:
    """Načte existující odkazy z pages.json."""
    if not PAGES_FILE.exists():
        return {}

    with PAGES_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "pages.json musí obsahovat objekt ve tvaru ID: URL."
        )

    return {
        str(key).strip().upper(): str(value).strip()
        for key, value in data.items()
    }


def save_pages(pages: dict[str, str]) -> None:
    """Uloží odkazy seřazené podle ID."""
    ordered_pages = dict(sorted(pages.items()))

    with PAGES_FILE.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(
            ordered_pages,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


def build_redirect_url(page_id: str) -> str:
    """Vytvoří krátkou GitHub Pages adresu."""
    return (
        f"https://{GITHUB_USER}.github.io/{REPOSITORY}/"
        f"?id={quote(page_id)}"
    )


def create_qr(page_id: str, redirect_url: str) -> Path:
    """Vytvoří lokální PNG QR kód."""
    QR_DIR.mkdir(exist_ok=True)

    output_path = QR_DIR / f"{page_id}.png"

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=16,
        border=4,
    )

    qr.add_data(redirect_url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )
    image.save(output_path)

    return output_path


def run_git(
    arguments: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Spustí Git příkaz ve složce projektu."""
    command = ["git", *arguments]

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
    )

    if check and result.returncode != 0:
        error_message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Příkaz {' '.join(command)} selhal:\n{error_message}"
        )

    return result


def check_git_repository() -> None:
    """Ověří, že se skript nachází v Git repozitáři."""
    result = run_git(
        ["rev-parse", "--is-inside-work-tree"],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Složka {BASE_DIR} není Git repozitář."
        )


def ensure_clean_merge_state() -> None:
    """Zabrání spuštění během nevyřešeného merge konfliktu."""
    result = run_git(
        ["diff", "--name-only", "--diff-filter=U"],
        check=False,
    )

    unresolved_files = result.stdout.strip()

    if unresolved_files:
        raise RuntimeError(
            "V Git repozitáři jsou nevyřešené konflikty:\n"
            f"{unresolved_files}\n"
            "Nejprve je vyřeš a vytvoř commit."
        )


def git_has_changes_for_pages() -> bool:
    """Zjistí, zda se změnil soubor pages.json."""
    result = run_git(
        ["status", "--porcelain", "--", "pages.json"],
        check=False,
    )

    return bool(result.stdout.strip())


def commit_and_push(page_id: str) -> None:
    """
    Přidá pouze pages.json, vytvoří commit a nahraje ho na GitHub.

    Složka QR se nepřidává.
    """
    check_git_repository()
    ensure_clean_merge_state()

    if not git_has_changes_for_pages():
        print("pages.json se nezměnil, není co commitovat.")
        return

    run_git(["add", "pages.json"])

    commit_message = f"Add LabQR link {page_id}"
    run_git(["commit", "-m", commit_message])

    print(f"Vytvořen commit: {commit_message}")

    push_result = run_git(
        ["push"],
        check=False,
    )

    if push_result.returncode != 0:
        error_message = (
            push_result.stderr.strip()
            or push_result.stdout.strip()
        )

        raise RuntimeError(
            "Commit byl vytvořen, ale push se nezdařil.\n"
            f"{error_message}\n\n"
            "Po odstranění problému spusť ručně:\n"
            "git push"
        )

    print("Změna byla úspěšně nahrána na GitHub.")


def ask_for_value(prompt: str, existing: str | None = None) -> str:
    """Načte hodnotu z terminálu."""
    if existing:
        return existing

    return input(prompt).strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Přidá OneNote odkaz, vytvoří QR kód "
            "a nahraje pages.json na GitHub."
        )
    )

    parser.add_argument(
        "id",
        nargs="?",
        help="Krátké ID, například AFM-2026-001",
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="Celý HTTPS odkaz na stránku OneNote",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Přepíše existující ID.",
    )

    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Nevytvoří commit ani push na GitHub.",
    )

    args = parser.parse_args()

    raw_id = ask_for_value(
        "Zadej ID, například AFM-2026-001: ",
        args.id,
    )
    page_id = normalize_id(raw_id)

    raw_url = ask_for_value(
        "Vlož celý HTTPS odkaz na stránku OneNote: ",
        args.url,
    )
    target_url = validate_url(raw_url)

    pages = load_pages()

    if page_id in pages and not args.overwrite:
        current_url = pages[page_id]

        print(f"\nID {page_id} již existuje.")
        print(f"Současný odkaz: {current_url}")

        confirmation = input(
            "Chceš tento odkaz přepsat? [a/N]: "
        ).strip().lower()

        if confirmation not in {"a", "ano", "y", "yes"}:
            raise SystemExit("Operace byla zrušena.")

    pages[page_id] = target_url
    save_pages(pages)

    redirect_url = build_redirect_url(page_id)
    qr_path = create_qr(page_id, redirect_url)

    print()
    print(f"ID:         {page_id}")
    print(f"QR adresa:  {redirect_url}")
    print(f"QR soubor:  {qr_path}")
    print(f"Cílová URL: {target_url}")
    print()

    if args.no_push:
        print(
            "Soubor pages.json byl změněn, "
            "ale commit ani push nebyly provedeny."
        )
        return

    commit_and_push(page_id)

    print()
    print("Hotovo.")
    print(
        "GitHub Pages může potřebovat krátkou chvíli "
        "na zveřejnění nové verze."
    )


if __name__ == "__main__":
    try:
        main()
    except (
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
    ) as error:
        print(f"\nChyba: {error}", file=sys.stderr)
        raise SystemExit(1) from error
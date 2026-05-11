"""
fetch_sigpac_atom.py
====================
Descarga los recintos SIGPAC de Galicia desde el servicio ATOM del FEGA.

El servicio ATOM tiene esta jerarquía de feeds XML:
  Feed raíz  →  Feed provincia  →  Feed municipio  →  ficheros ZIP/GML descargables

Uso rápido:
    # Descarga todos los municipios de Galicia (puede tardar 30-60 min)
    python fetch_sigpac_atom.py --output-dir data/sigpac_raw

    # Solo una provincia (más rápido para probar)
    python fetch_sigpac_atom.py --provincias 36 --output-dir data/sigpac_raw

    # Solo un municipio concreto (prueba inmediata)
    python fetch_sigpac_atom.py --provincias 36 --municipios 36038 --output-dir data/sigpac_raw

Tras la descarga ejecuta load_sigpac_postgis.py para cargar a PostGIS.

Requisitos:
    pip install httpx tenacity lxml
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
LOGGER = logging.getLogger("fetch_sigpac_atom")

# Feed raíz del servicio ATOM del FEGA
ATOM_ROOT = "https://www.fega.gob.es/orig/atomfeed.xml"

# Códigos INE de las cuatro provincias gallegas
PROVINCIAS_GALICIA = ["15", "27", "32", "36"]

# Namespaces usados en los feeds ATOM del FEGA
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "inspire_dls": "http://inspire.ec.europa.eu/schemas/inspire_dls/1.0",
    "georss": "http://www.georss.org/georss",
}

# Pausa entre descargas de municipios para no saturar el servidor
DELAY_BETWEEN_MUNICIPIOS = 1.5  # segundos

# ---------------------------------------------------------------------------
# Helpers de red con reintentos
# ---------------------------------------------------------------------------


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _fetch_bytes(client: httpx.AsyncClient, url: str) -> bytes:
    response = await client.get(url, follow_redirects=True)
    response.raise_for_status()
    return response.content


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    reraise=True,
)
async def _fetch_xml(client: httpx.AsyncClient, url: str) -> ET.Element:
    response = await client.get(url, follow_redirects=True)
    response.raise_for_status()
    return ET.fromstring(response.content)


# ---------------------------------------------------------------------------
# Parseo de feeds ATOM
# ---------------------------------------------------------------------------


def _get_text(element: ET.Element, tag: str, ns: dict[str, str]) -> str:
    el = element.find(tag, ns)
    return el.text.strip() if el is not None and el.text else ""


def _parse_province_feeds(root: ET.Element) -> dict[str, str]:
    """
    Del feed raíz extrae {código_provincia: url_feed_provincia}.
    Las entradas tienen <title> con el código de provincia (p.ej. '15').
    """
    feeds: dict[str, str] = {}
    for entry in root.findall("atom:entry", NS):
        title = _get_text(entry, "atom:title", NS)
        link_el = entry.find("atom:link[@rel='alternate']", NS)
        if link_el is None:
            link_el = entry.find("atom:link", NS)
        if link_el is not None:
            href = link_el.attrib.get("href", "")
            # El título suele ser "Recintos provincia XX" o solo "XX"
            # Extraemos el código numérico al final
            code = title.strip().split()[-1].zfill(2)
            if href:
                feeds[code] = href
    return feeds


def _parse_municipio_feeds(root: ET.Element) -> list[dict[str, Any]]:
    """
    Del feed de provincia extrae lista de municipios con sus URLs de descarga.
    Cada entrada tiene múltiples <link> con rel='section' apuntando a los ZIPs.
    """
    municipios: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", NS):
        title = _get_text(entry, "atom:title", NS)
        # Links de descarga: ZIP con recintos, elementos del paisaje, etc.
        download_links: list[str] = []
        for link in entry.findall("atom:link", NS):
            rel = link.attrib.get("rel", "")
            href = link.attrib.get("href", "")
            if rel in ("section", "enclosure", "alternate") and href.endswith(".zip"):
                download_links.append(href)
        if download_links:
            municipios.append({"title": title, "links": download_links})
    return municipios


def _extract_municipio_code(title: str) -> str:
    """Intenta extraer el código INE del municipio del título del feed."""
    # Formato habitual: "Recintos 15001 A Coruña" o "15001"
    parts = title.strip().split()
    for part in parts:
        if part.isdigit() and len(part) == 5:
            return part
    return title.strip().replace(" ", "_")[:20]


# ---------------------------------------------------------------------------
# Lógica principal de descarga
# ---------------------------------------------------------------------------


async def download_municipio(
    client: httpx.AsyncClient,
    municipio: dict[str, Any],
    output_dir: Path,
    provincia_code: str,
) -> list[Path]:
    """Descarga los ZIPs de un municipio y extrae los GML/SHP."""
    code = _extract_municipio_code(municipio["title"])
    mun_dir = output_dir / f"prov_{provincia_code}" / f"mun_{code}"

    # Coger solo el primer ZIP (recintos) — el más importante
    # Puedes cambiar a municipio["links"] para descargar todos
    links_to_download = municipio["links"][:1]

    downloaded: list[Path] = []
    for url in links_to_download:
        filename = url.split("/")[-1].split("?")[0] or f"{code}_recintos.zip"
        zip_path = mun_dir / filename

        if zip_path.exists():
            LOGGER.debug("Ya existe, saltando: %s", zip_path)
            downloaded.append(zip_path)
            continue

        mun_dir.mkdir(parents=True, exist_ok=True)
        try:
            LOGGER.info("Descargando %s → %s", url, zip_path.name)
            data = await _fetch_bytes(client, url)
            zip_path.write_bytes(data)
            downloaded.append(zip_path)

            # Extraer el ZIP
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(mun_dir)
            LOGGER.info("  Extraído: %s (%d KB)", zip_path.name, len(data) // 1024)

        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("  Error descargando %s: %s", url, exc)

    return downloaded


async def download_provincia(
    provincia_code: str,
    provincia_feed_url: str,
    output_dir: Path,
    municipios_filter: list[str] | None,
    semaphore: asyncio.Semaphore,
) -> int:
    """Descarga todos los municipios de una provincia."""
    LOGGER.info("=== Provincia %s — feed: %s", provincia_code, provincia_feed_url)

    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            prov_root = await _fetch_xml(client, provincia_feed_url)
        except Exception as exc:
            LOGGER.error("No se pudo leer el feed de provincia %s: %s", provincia_code, exc)
            return 0

        municipios = _parse_municipio_feeds(prov_root)
        LOGGER.info("  %d municipios encontrados en provincia %s", len(municipios), provincia_code)

        total = 0
        for mun in municipios:
            code = _extract_municipio_code(mun["title"])
            if municipios_filter and code not in municipios_filter:
                continue

            async with semaphore:
                paths = await download_municipio(client, mun, output_dir, provincia_code)
                if paths:
                    total += 1
                await asyncio.sleep(DELAY_BETWEEN_MUNICIPIOS)

    return total


async def run(
    output_dir: Path,
    provincias_filter: list[str] | None,
    municipios_filter: list[str] | None,
    max_concurrent: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(max_concurrent)

    LOGGER.info("Leyendo feed raíz ATOM: %s", ATOM_ROOT)
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            root_xml = await _fetch_xml(client, ATOM_ROOT)
        except Exception as exc:
            LOGGER.error(
                "No se pudo leer el feed raíz del FEGA.\n"
                "Comprueba conectividad o abre %s en el navegador para aceptar condiciones.\n"
                "Error: %s",
                ATOM_ROOT,
                exc,
            )
            return

    province_feeds = _parse_province_feeds(root_xml)
    LOGGER.info("Provincias en feed raíz: %s", sorted(province_feeds.keys()))

    target_provincias = provincias_filter or PROVINCIAS_GALICIA
    tasks = []
    for pcode in target_provincias:
        feed_url = province_feeds.get(pcode)
        if not feed_url:
            # Intentar URL directa como fallback
            feed_url = f"https://www.fega.gob.es/orig/atomfeed_{pcode}.xml"
            LOGGER.warning("Provincia %s no en feed raíz, probando URL directa: %s", pcode, feed_url)
        tasks.append(
            download_provincia(pcode, feed_url, output_dir, municipios_filter, semaphore)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)
    total = sum(r for r in results if isinstance(r, int))
    LOGGER.info("=== Descarga completada: %d municipios procesados ===", total)
    LOGGER.info("Ficheros en: %s", output_dir.resolve())
    LOGGER.info("Siguiente paso: python load_sigpac_postgis.py --input-dir %s", output_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descarga recintos SIGPAC de Galicia vía servicio ATOM del FEGA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output-dir",
        default="data/sigpac_raw",
        help="Directorio donde guardar los ZIPs y GMLs descargados (default: data/sigpac_raw)",
    )
    parser.add_argument(
        "--provincias",
        nargs="+",
        default=None,
        metavar="COD",
        help="Códigos de provincia a descargar (default: 15 27 32 36 — toda Galicia)",
    )
    parser.add_argument(
        "--municipios",
        nargs="+",
        default=None,
        metavar="COD",
        help="Filtrar por códigos INE de municipio (5 dígitos, p.ej. 36038)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=2,
        help="Descargas simultáneas máximas (default: 2 — no saturar el servidor)",
    )
    args = parser.parse_args()

    provincias = [p.zfill(2) for p in args.provincias] if args.provincias else None

    asyncio.run(
        run(
            output_dir=Path(args.output_dir),
            provincias_filter=provincias,
            municipios_filter=args.municipios,
            max_concurrent=args.concurrent,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
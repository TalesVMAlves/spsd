"""Aponta imagens duplicadas em um diretório, inclusive cópias rotacionadas.

Uso:
    uv run python scripts/check_duplicatas.py            # usa IMAGES_DIR
    uv run python scripts/check_duplicatas.py <diretorio>
"""

import argparse
import hashlib
import sys
from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable
from pathlib import Path

from PIL import Image

IMAGES_DIR = Path("data/raw/imagens")

EXTENSOES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}

ROTACOES = (
    None,
    Image.Transpose.ROTATE_90,
    Image.Transpose.ROTATE_180,
    Image.Transpose.ROTATE_270,
)


def listar_imagens(diretorio: Path) -> list[Path]:
    """Todas as imagens do diretório e subdiretórios, em ordem estável."""
    return sorted(
        p for p in diretorio.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSOES
    )


def agrupar_por(
    itens: Iterable, chave: Callable[[object], Hashable | None]
) -> list[list]:
    """Agrupa itens pela chave e devolve só os grupos com 2 ou mais elementos.

    Itens cuja chave é None (ex.: arquivo ilegível) são ignorados.
    """
    grupos = defaultdict(list)
    for item in itens:
        k = chave(item)
        if k is not None:
            grupos[k].append(item)
    return [g for g in grupos.values() if len(g) > 1]


def chave_cabecalho(caminho: Path) -> tuple | None:
    """Modo de cor e dimensões ordenadas, lidos só do cabeçalho (sem decodificar)."""
    try:
        with Image.open(caminho) as img:
            return img.mode, tuple(sorted(img.size))
    except Exception as erro:  # Pillow levanta vários tipos para arquivos inválidos
        print(f"[aviso] não foi possível ler {caminho}: {erro}", file=sys.stderr)
        return None


def hash_pixels(img: Image.Image) -> bytes:
    """Hash dos pixels, incluindo as dimensões para não confundir 2x8 com 4x4."""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"{img.mode}{img.size}".encode())
    h.update(img.tobytes())
    return h.digest()


def assinatura_canonica(caminho: Path) -> tuple[bytes, int] | None:
    """Menor hash entre as 4 rotações e o índice da rotação que o produziu."""
    try:
        with Image.open(caminho) as img:
            img.load()
            hashes = [
                hash_pixels(img if r is None else img.transpose(r)) for r in ROTACOES
            ]
    except Exception as erro:
        print(
            f"[aviso] não foi possível decodificar {caminho}: {erro}", file=sys.stderr
        )
        return None
    menor = min(hashes)
    return menor, hashes.index(menor)


def encontrar_duplicatas(imagens: list[Path]) -> list[list[tuple[Path, int]]]:
    """Grupos de duplicatas; cada item é (caminho, rotação em graus em relação ao 1º do grupo)."""
    candidatos = [p for grupo in agrupar_por(imagens, chave_cabecalho) for p in grupo]

    assinaturas = {}
    for p in candidatos:
        a = assinatura_canonica(p)
        if a is not None:
            assinaturas[p] = a

    duplicatas = []
    for grupo in agrupar_por(assinaturas, lambda p: assinaturas[p][0]):
        # Se A girada k_a vezes == B girada k_b vezes, então B == A girada (k_a - k_b) vezes.
        k_ref = assinaturas[grupo[0]][1]
        duplicatas.append([(p, ((k_ref - assinaturas[p][1]) % 4) * 90) for p in grupo])
    return duplicatas


def imprimir_relatorio(
    duplicatas: list[list[tuple[Path, int]]], total: int, base: Path
) -> None:
    for i, grupo in enumerate(duplicatas, start=1):
        print(f"\nGrupo {i} ({len(grupo)} arquivos):")
        for j, (caminho, graus) in enumerate(grupo):
            if j == 0:
                rotulo = "original"
            elif graus == 0:
                rotulo = "idêntica"
            else:
                rotulo = f"rotacionada {graus}° (anti-horário)"
            print(f"  {caminho.relative_to(base)}  [{rotulo}]")

    redundantes = sum(len(g) - 1 for g in duplicatas)
    espaco = sum(c.stat().st_size for g in duplicatas for c, _ in g[1:])
    print(
        f"\n{total} imagens analisadas, {len(duplicatas)} grupos de duplicatas, "
        f"{redundantes} arquivos redundantes ({espaco / 1024**2:.1f} MB)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "diretorio",
        nargs="?",
        type=Path,
        default=IMAGES_DIR,
        help=f"diretório de imagens (padrão: {IMAGES_DIR})",
    )
    diretorio = parser.parse_args().diretorio

    if not diretorio.is_dir():
        sys.exit(f"Diretório não encontrado: {diretorio}")

    imagens = listar_imagens(diretorio)
    duplicatas = encontrar_duplicatas(imagens)
    imprimir_relatorio(duplicatas, len(imagens), diretorio)


if __name__ == "__main__":
    main()

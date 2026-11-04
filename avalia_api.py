"""
Módulo para consultar a API do Instituto Avalia e obter dados de concursos e publicações.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

AVALIA_API_BASE = "https://link.avalia.org.br/api"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

def fetch_json(url: str, timeout: int = 15) -> Any:
    """Faz requisição HTTP GET retornando o JSON decodificado."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content = response.read().decode("utf-8", errors="replace")
        return json.loads(content)


def get_concurso_info(concurso_id: int = 619) -> Dict[str, Any]:
    """
    Obtém as informações detalhadas do concurso a partir da API oficial da Avalia.
    Retorna um dicionário com:
      - 'nome': Nome da instituição / concurso
      - 'status': Status do concurso
      - 'edital': Identificador do edital
      - 'publicacoes': Lista de publicações [{id, nome, url}]
      - 'links': Lista de links de acompanhamento [{nome, url, categoria}]
      - 'url_pagina': URL da página web
    """
    url = f"{AVALIA_API_BASE}/concursos/{concurso_id}"
    data = fetch_json(url)

    if isinstance(data, list) and len(data) > 0:
        concurso = data[0]
    elif isinstance(data, dict):
        concurso = data
    else:
        raise ValueError(f"Formato inesperado de resposta da API: {type(data)}")

    # Obter lista de links se existir endpoint dedicado
    links = concurso.get("links", [])
    try:
        links_url = f"{AVALIA_API_BASE}/links/concurso/{concurso_id}"
        extra_links = fetch_json(links_url)
        if isinstance(extra_links, list):
            # Fundir links evitando duplicados
            seen_urls = {l.get("url") for l in links if "url" in l}
            for el in extra_links:
                if el.get("url") not in seen_urls:
                    links.append(el)
                    seen_urls.add(el.get("url"))
    except Exception:
        # Se falhar o endpoint auxiliar, mantém os links do objeto principal
        pass

    return {
        "id": concurso.get("id", concurso_id),
        "concurso_id": concurso_id,
        "nome": concurso.get("nome", f"Concurso {concurso_id}"),
        "status": concurso.get("status", "Em andamento"),
        "edital": concurso.get("edital", ""),
        "tipoProcesso": concurso.get("tipoProcesso", "Concurso público"),
        "publicacoes": concurso.get("publicacoes", []),
        "links": links,
        "url_pagina": f"https://www.avalia.org.br/concursos/{concurso_id}"
    }


if __name__ == "__main__":
    import pprint
    info = get_concurso_info(619)
    print("Concurso:", info["nome"])
    print(f"Total publicações: {len(info['publicacoes'])}")
    print(f"Total links: {len(info['links'])}")
    if info["publicacoes"]:
        print("\nÚltima publicação:")
        pprint.pprint(info["publicacoes"][0])


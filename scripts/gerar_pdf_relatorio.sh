#!/usr/bin/env bash
# Gera relatorios/<nome>.pdf a partir de relatorios/<nome>.md
# Uso: scripts/gerar_pdf_relatorio.sh base_dados
# Requer: pandoc e weasyprint (pip install weasyprint). O CSS fica embutido no HTML
# (scripts/relatorio_estilo.html), então o PDF não depende de caminhos externos.
set -euo pipefail
nome="${1:-base_dados}"
raiz="$(cd "$(dirname "$0")/.." && pwd)"
md="$raiz/relatorios/$nome.md"
html="$raiz/relatorios/.$nome.html"
pdf="$raiz/relatorios/$nome.pdf"
pandoc "$md" --standalone --from markdown+pipe_tables+implicit_figures --to html5 \
  --include-in-header "$raiz/scripts/relatorio_estilo.html" \
  --metadata pagetitle="$(grep -m1 '^title:' "$md" | sed 's/^title: *//; s/^"//; s/"$//')" \
  -o "$html"
python3 - "$html" "$pdf" "$raiz/relatorios/" <<'PY'
import sys
from weasyprint import HTML
html, pdf, base = sys.argv[1:]
HTML(html, base_url=base).write_pdf(pdf)
PY
rm -f "$html"
echo "gerado: $pdf"

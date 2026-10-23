# Imagens de valores · funil Tipo de Viajante (Lielu Turismo)

Todo dia às 5h (Brasília) o GitHub:
1. lê os preços de todas as saídas no site lieluturismo.com.br (`fabrica/ler_site.py`);
2. faz uma imagem por saída: a saída escolhida + 3 viagens com valor parecido (`fabrica/fabrica.py`);
3. publica as imagens e o `index.json` no GitHub Pages.

O n8n manda a imagem certa pelo WhatsApp (API da Clint) quando a pessoa toca em "Receber valores do dia".
Se a leitura do site vier incompleta, nada é publicado e as imagens do dia anterior continuam no ar.

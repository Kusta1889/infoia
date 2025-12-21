# 🤖 infoIA

Bot que recopila noticias de IA de **17 fuentes**, las resume y traduce al español, y publica un digest diario.

🌐 **Ver Digest:** [tu-usuario.github.io/InfoIA](https://tu-usuario.github.io/InfoIA)

## ✨ Características

- 📡 **17 fuentes de IA** (OpenAI, Anthropic, DeepMind, arXiv, HuggingFace, etc.)
- 🔄 **Actualización diaria** a las 8:00 AM (Argentina)
- 🌐 **Resumen en español** con DeepSeek API
- 📊 **6 categorías**: Lanzamientos, Research, Benchmarks, Noticias, Herramientas, Español

## 📂 Categorías

| Emoji | Categoría | Fuentes |
|-------|-----------|---------|
| 🚀 | Lanzamientos de Modelos | OpenAI, Anthropic, DeepMind, LLM Tracker |
| 📄 | Research & Papers | arXiv, HuggingFace Papers, BAIR |
| 📊 | Benchmarks & Rankings | Artificial Analysis, LMArena |
| 📰 | Noticias de Industria | TechCrunch, VentureBeat, The Decoder |
| 🛠️ | Herramientas & APIs | HuggingFace Models |
| 🇪🇸 | En Español | Xataka IA |

## 🚀 Ejecutar Localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
cp .env.example .env
# Editar .env con tu DEEPSEEK_API_KEY

# Ejecutar
python main.py --github-pages
```

## 🔧 GitHub Actions

El workflow se ejecuta automáticamente cada día a las 8:00 AM (Argentina).

Para ejecutar manualmente: **Actions** → **Daily AI News Digest** → **Run workflow**

---

Made with 🤖 by AI News Aggregator

# Ollama: Local Mac and Google Colab

This project uses Ollama through its OpenAI-compatible `/v1` API. The same
application configuration works with an Ollama server on the Mac or one exposed
from Google Colab through ngrok.

## Notebook

Use the prepared [Google Colab notebook](https://colab.research.google.com/drive/1jNm-8W5WVd7KFRtrKBFelFGyvM_trtPd) to install Ollama, start the server, pull models, and create the ngrok tunnel.

## 1. Switch the application

Copy `src/.env.example` to `src/.env` and use one profile at a time:

```env
# Local Mac server
LLM_MODE="OLLAMA"
OLLAMA_API_URL="http://localhost:11434/v1"
```

For an Ollama server running in Colab, keep `LLM_MODE="OLLAMA"` and replace the
URL with the ngrok URL printed by the notebook:

```env
OLLAMA_API_URL="https://your-subdomain.ngrok-free.app/v1"
```

`OLLAMA_API_URL` must end in `/v1`. Do not add the `/api` path: the application
uses the OpenAI-compatible client, not Ollama's native REST client.

To return to OpenAI or another OpenAI-compatible cloud service:

```env
LLM_MODE="CLOUD"
CLOUD_OPENAI_API_KEY="your-key-kept-only-in-.env"
CLOUD_OPENAI_API_URL="" # blank uses OpenAI's default endpoint
```

## 2. Run Ollama locally on macOS

After installing and opening Ollama, pull both the generation and embedding
models:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
ollama serve
```

In another terminal, verify the local API:

```bash
curl http://127.0.0.1:11434/api/version
ollama list
```

If Ollama was installed only in a user directory, ensure the executable is on
your `PATH` before running these commands.

## 3. Run Ollama in Google Colab

Use a GPU runtime in Colab, then run these cells in order.

### Install Ollama

```bash
!apt-get update -qq
!apt-get install -y -qq zstd
!curl -fsSL https://ollama.com/install.sh -o /content/install-ollama.sh
!sh /content/install-ollama.sh
!ollama --version
```

### Start the server and download models

```bash
%%bash
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /content/ollama.out 2>&1 &
sleep 5
curl -f http://127.0.0.1:11434/api/version
ollama pull llama3.2
ollama pull nomic-embed-text
```

If the server was started previously in the same Colab runtime, reuse it rather
than starting a second server. Inspect `/content/ollama.out` when the health
check fails.

### Expose the API with ngrok

Create an ngrok account and copy its auth token. Never commit that token.

```python
!pip -q install pyngrok

from pyngrok import ngrok

ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")
public_url = ngrok.connect(11434).public_url
print(f"Set OLLAMA_API_URL to: {public_url}/v1")
```

Use the printed HTTPS address in `src/.env` on the machine running this project.
The ngrok address changes when the Colab runtime or tunnel is restarted.

## 4. Safety and lifecycle

- An ngrok public URL exposes the model endpoint. Stop the tunnel when it is not
  needed and do not publish the URL.
- Colab runtimes are temporary. Models and the server disappear when the runtime
  is reset.
- Run `ollama pull` for both models after a fresh runtime starts.
- For a remote endpoint, expect higher latency than a local Ollama server.

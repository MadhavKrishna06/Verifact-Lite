"""Local LLM clients with on-disk caching.

Three interchangeable backends, selected in config.yaml:

* ``ollama``            - HTTP /api/chat against a local Ollama server.
* ``llama_cpp_server``  - OpenAI-compatible /v1/chat/completions, as served by
                          ``llama-server`` from llama.cpp.
* ``llama_cpp_python``  - in-process llama-cpp-python bindings over a GGUF file.

No model name is hard-coded: every client is constructed from a config block.
Every call is cached under hash(model + prompt + parameters) so experiments are
repeatable without regenerating anything.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import requests

from .utils import hash_key, load_config, resolve_path

Message = dict  # {"role": "user"|"assistant"|"system", "content": str}


class ModelError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
class CallCache:
    """Content-addressed cache of LLM responses, sharded by key prefix."""

    def __init__(self, directory: str | os.PathLike, enabled: bool = True):
        self.dir = Path(directory)
        self.enabled = enabled
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        if self.enabled:
            self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / key[:2] / f"{key}.json"

    def get(self, key: str) -> str | None:
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.exists():
            with self._lock:
                self.misses += 1
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            with self._lock:
                self.hits += 1
            return payload.get("response")
        except Exception:
            return None

    def put(self, key: str, response: str, meta: dict | None = None) -> None:
        if not self.enabled:
            return
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"response": response, "meta": meta or {}}, fh, ensure_ascii=False)
        tmp.replace(path)

    def stats(self) -> dict:
        return {"hits": self.hits, "misses": self.misses, "enabled": self.enabled}


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
class BaseClient:
    """Common interface: ``chat(messages) -> str`` plus ``complete(prompt)``."""

    def __init__(self, spec: dict, cache: CallCache, backend_cfg: dict | None = None):
        self.spec = spec
        self.alias = spec.get("alias") or spec.get("name") or spec.get("model_id", "model")
        self.name = spec.get("name", self.alias)
        self.model_id = spec["model_id"]
        self.temperature = float(spec.get("temperature", 0.1))
        self.max_tokens = int(spec.get("max_tokens", 2048))
        self.timeout_s = float(spec.get("timeout_s", 600))
        self.weight = float(spec.get("weight", 1.0))
        self.cache = cache
        self.backend_cfg = backend_cfg or {}
        self.calls = 0
        self.total_latency_s = 0.0

    # -- backend hook -------------------------------------------------------
    def _generate(self, messages: list[Message], temperature: float, max_tokens: int) -> str:
        raise NotImplementedError

    # -- public API ---------------------------------------------------------
    def chat(
        self,
        messages: list[Message],
        temperature: float | None = None,
        max_tokens: int | None = None,
        tag: str = "",
    ) -> str:
        temp = self.temperature if temperature is None else float(temperature)
        toks = self.max_tokens if max_tokens is None else int(max_tokens)
        key = hash_key(self.backend_name, self.model_id, messages, temp, toks)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        start = time.time()
        try:
            text = self._generate(messages, temp, toks)
        except requests.RequestException as exc:  # pragma: no cover - network
            raise ModelError(f"{self.backend_name} request failed: {exc}") from exc
        elapsed = time.time() - start
        self.calls += 1
        self.total_latency_s += elapsed

        self.cache.put(
            key,
            text,
            meta={
                "backend": self.backend_name,
                "model_id": self.model_id,
                "temperature": temp,
                "max_tokens": toks,
                "tag": tag,
                "latency_s": round(elapsed, 3),
            },
        )
        return text

    def complete(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    @property
    def backend_name(self) -> str:
        return self.spec.get("backend", "unknown")

    def stats(self) -> dict:
        return {
            "alias": self.alias,
            "name": self.name,
            "model_id": self.model_id,
            "backend": self.backend_name,
            "calls": self.calls,
            "total_latency_s": round(self.total_latency_s, 2),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{type(self).__name__} {self.alias}:{self.model_id}>"


class OllamaClient(BaseClient):
    """Talks to a local Ollama server (llama.cpp under the hood)."""

    def _generate(self, messages: list[Message], temperature: float, max_tokens: int) -> str:
        host = self.backend_cfg.get("host", "http://127.0.0.1:11434").rstrip("/")
        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            # Keep the model resident between calls; swapping a quantized model
            # in and out costs far more than the generation itself.
            "keep_alive": self.backend_cfg.get("keep_alive", "10m"),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "seed": int(self.spec.get("seed", 2024)),
            },
        }
        resp = requests.post(f"{host}/api/chat", json=payload, timeout=self.timeout_s)
        if resp.status_code != 200:
            raise ModelError(f"ollama {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
        return (data.get("message", {}) or {}).get("content", "").strip()


class LlamaCppServerClient(BaseClient):
    """OpenAI-compatible endpoint, e.g. `llama-server -m model.gguf --port 8080`."""

    def _generate(self, messages: list[Message], temperature: float, max_tokens: int) -> str:
        base = self.backend_cfg.get("base_url", "http://127.0.0.1:8080/v1").rstrip("/")
        headers = {"Content-Type": "application/json"}
        api_key = self.backend_cfg.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = requests.post(
            f"{base}/chat/completions", json=payload, headers=headers, timeout=self.timeout_s
        )
        if resp.status_code != 200:
            raise ModelError(f"llama_cpp_server {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


class LlamaCppPythonClient(BaseClient):
    """In-process llama-cpp-python bindings over a local GGUF file."""

    _models: dict[str, Any] = {}

    def _llm(self):
        path = self.backend_cfg.get("model_path") or self.spec.get("model_path")
        if not path:
            raise ModelError("llama_cpp_python backend needs backends.llama_cpp_python.model_path")
        if path in self._models:
            return self._models[path]
        try:
            from llama_cpp import Llama
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelError(
                "llama-cpp-python is not installed. Install it, or set "
                "model.backend to 'ollama' / 'llama_cpp_server' in config.yaml."
            ) from exc
        llm = Llama(
            model_path=str(path),
            n_ctx=int(self.backend_cfg.get("n_ctx", 8192)),
            n_gpu_layers=int(self.backend_cfg.get("n_gpu_layers", 0)),
            verbose=False,
        )
        self._models[path] = llm
        return llm

    def _generate(self, messages: list[Message], temperature: float, max_tokens: int) -> str:
        out = self._llm().create_chat_completion(
            messages=messages, temperature=temperature, max_tokens=max_tokens
        )
        return out["choices"][0]["message"]["content"].strip()


_BACKENDS = {
    "ollama": OllamaClient,
    "llama_cpp_server": LlamaCppServerClient,
    "llama_cpp_python": LlamaCppPythonClient,
}


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def build_client(spec: dict, cfg: dict, cache: CallCache | None = None) -> BaseClient:
    backend = spec.get("backend") or cfg.get("model", {}).get("backend", "ollama")
    if backend not in _BACKENDS:
        raise ModelError(f"unknown backend '{backend}'; expected one of {sorted(_BACKENDS)}")
    cache = cache or build_cache(cfg)
    backend_cfg = (cfg.get("backends") or {}).get(backend, {})
    spec = dict(spec)
    spec["backend"] = backend
    spec.setdefault("seed", (cfg.get("run") or {}).get("seed", 2024))
    return _BACKENDS[backend](spec, cache, backend_cfg)


def build_cache(cfg: dict) -> CallCache:
    cache_cfg = cfg.get("cache") or {}
    return CallCache(
        resolve_path(cfg, cache_cfg.get("dir", "cache")),
        enabled=bool(cache_cfg.get("enabled", True)),
    )


def build_primary(cfg: dict, cache: CallCache | None = None) -> BaseClient:
    spec = dict(cfg["model"])
    spec.setdefault("alias", "primary")
    return build_client(spec, cfg, cache)


def build_generator(cfg: dict, cache: CallCache | None = None) -> BaseClient:
    """Client used to produce the answer under evaluation (generated once)."""
    gen = dict(cfg.get("generation") or {})
    spec = dict(cfg["model"])
    spec.update({k: v for k, v in gen.items() if k in {"model_id", "temperature", "max_tokens"}})
    spec["alias"] = "generator"
    return build_client(spec, cfg, cache)


def build_judges(cfg: dict, cache: CallCache | None = None) -> list[BaseClient]:
    """Build every configured judge. Arbitrary judge counts are supported."""
    cache = cache or build_cache(cfg)
    judges = []
    for spec in cfg.get("judges") or []:
        judges.append(build_client(spec, cfg, cache))
    if not judges:
        judges.append(build_primary(cfg, cache))
    return judges


def available_judges(cfg: dict, cache: CallCache | None = None) -> list[BaseClient]:
    """Judges whose model is actually reachable; skips the rest with a warning.

    This is what makes the second judge optional: if only Qwen is installed the
    pipeline runs single-judge rather than failing.
    """
    cache = cache or build_cache(cfg)
    usable = []
    for judge in build_judges(cfg, cache):
        if probe(judge):
            usable.append(judge)
        else:
            print(f"[warn] judge '{judge.alias}' ({judge.model_id}) unreachable; skipping")
    return usable


def probe(client: BaseClient) -> bool:
    """Cheap reachability check for one client."""
    try:
        out = client.chat(
            [{"role": "user", "content": "Reply with the single word: ok"}],
            temperature=0.0,
            max_tokens=8,
            tag="probe",
        )
        return bool(out)
    except Exception as exc:
        print(f"[warn] probe failed for {client.model_id}: {exc}")
        return False


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    cfg = load_config()
    primary = build_primary(cfg)
    print(primary, "->", primary.complete("Name the capital of France in one word.", max_tokens=16))
    for judge in build_judges(cfg):
        print(judge, "reachable:", probe(judge))

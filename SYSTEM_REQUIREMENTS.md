# System Requirements

mic-answer を動作させるために必要なハードウェア・ソフトウェア仕様。

## ハードウェア要件

### 1. マイク（音声入力デバイス） — 必須

- PortAudio 対応のマイクが必要（`sounddevice` ライブラリ = PortAudio の Python バインディング）
- サンプルレート 16kHz, モノラル, float32 に対応していること
- OS が認識するデフォルト入力デバイスが使用される
- 起動時に 3 秒間の環境ノイズキャリブレーションを行うため、常時入力が取得できる必要がある

### 2. スピーカー / 音声出力デバイス — 必須

- PortAudio 対応の音声出力デバイスが必要
- API から返却される WAV 音声（PCM 16bit）を再生するために使用
- デフォルト出力デバイスが使用される

### 3. CPU — 必須（GPU 不要で動作可能）

- faster-whisper の "medium" モデルを動作させる必要がある
- CPU-only の場合、int8 量子化で動作する
- Whisper medium モデルは約 1.5GB の RAM をモデルだけで消費する
- リアルタイム性を求めるなら 4 コア以上を推奨（数秒の発話を処理するのに CPU だと数秒〜十数秒かかる可能性がある）
- アーキテクチャ: x86_64（ctranslate2 が主にサポート）。ARM64 でも動作するがパフォーマンスに注意

### 4. GPU（NVIDIA CUDA） — 任意（あれば高速化）

- CUDA 対応の場合は自動検出され、float16 等の高速な compute type で推論が行われる
- Whisper medium モデルの GPU 推論には約 2〜3GB の VRAM が必要
- 推奨: NVIDIA GPU（CUDA 12 対応, VRAM 4GB 以上）
- GPU 無しでも CPU フォールバックで動作するため必須ではない

### 5. メモリ（RAM）

- Whisper medium モデル: 約 1.5GB（CPU int8 時）〜 2.5GB
- Python + NumPy + 録音バッファ: 数百 MB
- Web UI モード（FastAPI + Uvicorn）使用時はさらに若干追加

### 6. ストレージ

- Whisper medium モデルのダウンロード: 約 1.5GB（初回起動時に自動ダウンロードされキャッシュされる）
- アプリケーション本体: 数 MB
- ログファイル (`mic-answer.log`): 運用期間に応じて増加

### 7. ネットワーク

- 外部 API サーバーとの HTTP 通信が必要（デフォルト: `http://localhost:8080/chat`）
- モデル初回ダウンロード時にインターネット接続が必要
- API がローカルであれば LAN 内で完結可能

## ソフトウェア要件

- **OS**: Linux（Debian / Ubuntu 系を想定。`setup.sh` で `apt-get install libportaudio2` を実行）
- **Python**: 3.12 以上（型ヒント `X | None` 構文を使用）
- **systemd**: デーモン運用時に必要（`mic-answer.service`）

## まとめ

| 項目 | 最低要件 | 推奨 |
|---|---|---|
| マイク | 16kHz 対応の任意のマイク | — |
| スピーカー | 任意の音声出力 | — |
| CPU | x86_64, 2 コア | 4 コア以上 |
| GPU | 不要 | NVIDIA CUDA 12 対応, VRAM 4GB+ |
| RAM | 4GB | 8GB 以上 |
| ストレージ | 3GB 空き | 5GB 以上空き |
| OS | Linux (Debian / Ubuntu 系) | Ubuntu 22.04+ |
| Python | 3.12+ | 3.12+ |
| ネットワーク | 初回 DL 時にインターネット | 外部 API への接続 |

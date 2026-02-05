# mic-answer

マイク入力を常時監視し、発話を検知して自動で録音・文字起こし・外部API連携を行う常駐型アプリケーション。
受付・窓口での音声入力を想定しています。

## 動作フロー

1. マイク入力を監視（RMS による発話検知）
2. 発話検知後、録音開始
3. 無音が2秒間続いたら録音停止
4. faster-whisper で日本語文字起こし
5. 外部APIへテキスト送信、WAV音声レスポンスを再生
6. 待機状態に戻る

## 必要環境

- Python 3.12+
- CUDA 対応 GPU
- PortAudio (`libportaudio2`)

## セットアップ

```bash
./setup.sh
```

## 実行

```bash
./run.sh
```

Web UI は http://localhost:8000 でアクセスできます。リアルタイムの状態監視、会話ログの確認、設定変更が可能です。

## VRM キャラクター表示

Web UI 上に VRM/GLB 形式の3Dキャラクターを表示できます。音声再生時のリップシンク、まばたき、呼吸アニメーションに対応しています。

### モデルの配置

`static/` ディレクトリに以下のいずれかのファイルを配置してください（上から順に検索されます）。

1. `static/model.vrm`
2. `static/model.glb`

背景画像を設定する場合は `static/bg.jpg` を配置してください。

### モデルの入手

VRM モデルは [VRoid Hub](https://hub.vroid.com/) からダウンロードして使用できます。ダウンロードした `.vrm` ファイルを `static/model.vrm` として配置してください。

## 設定

環境変数で設定を変更できます。

| 変数 | デフォルト値 | 説明 |
|---|---|---|
| `SAMPLE_RATE` | 16000 | サンプリングレート (Hz) |
| `START_THRESHOLD` | 0.02 | 発話検知の音量閾値 (RMS) |
| `SILENCE_THRESHOLD` | 0.01 | 無音判定の音量閾値 (RMS) |
| `SILENCE_DURATION` | 2.0 | 録音停止までの無音秒数 |
| `SEND_API_URL` | http://localhost:8080/chat | 送信先API URL |

## 外部API仕様

### リクエスト

```
POST /chat
Content-Type: application/json

{"text": "こんにちは", "speaker_id": 0}
```

### レスポンス

- `200 OK`
- Body: WAV バイナリ (PCM 16bit)
- Header `X-Response-Text`: URL エンコード済み応答テキスト

## systemd サービス

```bash
sudo cp mic-answer.service /etc/systemd/system/
sudo systemctl enable --now mic-answer
```

※ アプリを `/opt/mic-answer` に配置してください。

## テスト

WAV ファイルを使ってパイプラインをテストできます。

```bash
source .venv/bin/activate
python test_with_file.py test.wav
```

## ライセンス

本プロジェクトは以下のオープンソースライブラリを使用しています。

| ライブラリ | ライセンス | 著作権者 |
|------------|-----------|----------|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | Copyright (c) 2023 SYSTRAN |
| [OpenAI Whisper](https://github.com/openai/whisper) | MIT | Copyright (c) 2022 OpenAI |
| [sounddevice](https://github.com/spatialaudio/python-sounddevice) | MIT | Copyright (c) 2015-2025 Matthias Geier |
| [NumPy](https://github.com/numpy/numpy) | BSD 3-Clause | Copyright (c) 2005-2025, NumPy Developers |
| [requests](https://github.com/psf/requests) | Apache 2.0 | Copyright Kenneth Reitz and Python Software Foundation |
| [FastAPI](https://github.com/tiangolo/fastapi) | MIT | Copyright (c) 2018 Sebastián Ramírez |
| [Uvicorn](https://github.com/encode/uvicorn) | BSD 3-Clause | Copyright © 2017-present, Encode OSS Ltd |
| [websockets](https://github.com/python-websockets/websockets) | BSD 3-Clause | Copyright (c) Aymeric Augustin and contributors |

GPU環境で使用する場合、本ソフトウェアには NVIDIA Corporation が提供するソースコードが含まれます。

詳細は [ライセンス.md](ライセンス.md) を参照してください。

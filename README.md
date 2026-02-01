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

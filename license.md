# ライセンス調査結果

本プロジェクトで使用しているライブラリのライセンスと商用利用に関する調査結果です。

調査日: 2026-02-03

## 商用利用可能なライブラリ

| ライブラリ | ライセンス | 商用利用 | 著作権表示 |
|------------|-----------|----------|------------|
| faster-whisper | MIT | 可 | 必要 |
| OpenAI Whisper (モデル) | MIT | 可 | 必要 |
| sounddevice | MIT | 可 | 必要 |
| numpy | BSD 3-Clause | 可 | 必要 |
| requests | Apache 2.0 | 可 | 必要 |
| fastapi | MIT | 可 | 必要 |
| uvicorn | BSD 3-Clause | 可 | 必要 |
| websockets | BSD 3-Clause | 可 | 必要 |

## 注意が必要なライブラリ

### nvidia-cublas-cu12

**ライセンス**: NVIDIA Proprietary (CUDA Toolkit EULA)

**商用利用**: 条件付きで可能

#### 制限事項

1. **商用利用自体は許可** - GPU加速アプリケーションの開発・配布は可能

2. **再配布の制限** - ランタイムライブラリは配布可能だが、「実質的な追加機能」を持つアプリケーションの一部としてのみ配布可

3. **安全重要システムでの使用禁止** - 以下のシステムでは使用不可:
   - 自動車の安全システム
   - 医療機器
   - 航空宇宙システム
   - その他、故障が人命に関わるシステム

4. **著作権表示が必要** - 配布時に以下の表示が必要:
   > "This software contains source code provided by NVIDIA Corporation."

5. **保証なし** - 責任上限は $10 USD、AS IS での提供

#### 参照

- [NVIDIA CUDA Toolkit EULA](https://docs.nvidia.com/cuda/eula/index.html)

## 推奨事項

### CPU環境のみで運用する場合

`nvidia-cublas-cu12` は不要なため、`requirements.txt` から削除することで NVIDIA 関連のライセンス問題を回避できます。

### GPU環境で商用利用する場合

- 受付・顧客対応シナリオ（本プロジェクトの想定用途）であれば問題なし
- 安全重要システムでないことを確認
- 配布時に必要な著作権表示を行う

### 全ライブラリ共通

MIT / BSD / Apache 2.0 ライセンスのライブラリについては、以下のいずれかの方法で著作権表示を行うことを推奨:

- アプリケーションのドキュメントに記載
- NOTICE ファイルを作成して同梱
- アプリケーション内の「About」や「ライセンス情報」画面に表示

## 著作権表示（必須）

本ソフトウェアを配布する際は、以下の著作権表示を含める必要があります。

### faster-whisper (MIT License)

```
Copyright (c) 2023 SYSTRAN
```

### OpenAI Whisper (MIT License)

```
Copyright (c) 2022 OpenAI
```

### sounddevice (MIT License)

```
Copyright (c) 2015-2025 Matthias Geier
```

### NumPy (BSD 3-Clause License)

```
Copyright (c) 2005-2025, NumPy Developers. All rights reserved.
```

### requests (Apache License 2.0)

```
Copyright Kenneth Reitz and Python Software Foundation
```

### FastAPI (MIT License)

```
Copyright (c) 2018 Sebastián Ramírez
```

### Uvicorn (BSD 3-Clause License)

```
Copyright © 2017-present, Encode OSS Ltd. All rights reserved.
```

### websockets (BSD 3-Clause License)

```
Copyright (c) Aymeric Augustin and contributors
```

### NVIDIA CUDA (配布時のみ)

GPU環境でCUDAライブラリを含めて配布する場合:

```
This software contains source code provided by NVIDIA Corporation.
```

## ライセンス詳細リンク

- [faster-whisper LICENSE](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE)
- [OpenAI Whisper LICENSE](https://github.com/openai/whisper/blob/main/LICENSE)
- [sounddevice LICENSE](https://github.com/spatialaudio/python-sounddevice/blob/master/LICENSE)
- [NumPy LICENSE](https://github.com/numpy/numpy/blob/main/LICENSE.txt)
- [Requests LICENSE](https://github.com/psf/requests/blob/main/LICENSE)
- [FastAPI LICENSE](https://github.com/tiangolo/fastapi/blob/master/LICENSE)
- [Uvicorn LICENSE](https://github.com/encode/uvicorn/blob/master/LICENSE.md)
- [websockets LICENSE](https://github.com/python-websockets/websockets/blob/main/LICENSE)
- [NVIDIA CUDA EULA](https://docs.nvidia.com/cuda/eula/index.html)

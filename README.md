# Mistral OCR script

## 概要 (Overview)

このスクリプトは、Mistral AIのOCR API (`mistral-ocr-latest`) を使用して、指定されたPDFファイルまたはURLからテキストと画像を抽出し、Markdownファイルとして保存します。抽出された画像は、Markdownファイルと同じディレクトリに個別のファイルとして保存されます。

## 機能 (Features)

* PDFファイルまたは公開されているURLをOCR処理の入力として使用できます。
* Mistral AIの最新OCRモデル (`mistral-ocr-latest`) を利用します。
* OCR結果（テキストと画像参照）をMarkdown形式でファイルに出力します。
* OCR処理中に検出された画像を、Markdownファイルと同じディレクトリに保存します。
* 処理の進行状況を `tqdm` で可視化し、進捗バーを表示します。
* 処理の進行状況やエラーをログに出力します。

## 参考にしたサイト

[Mistral OCR: A Guide With Practical Examples | DataCamp](https://www.datacamp.com/tutorial/mistral-ocr)

## 必要なもの (Prerequisites)

* Python 3.7 以上 (推奨)
* Mistral AI APIキー
* 必要なPythonライブラリ:
    * `mistralai`
    * `python-datauri`
    * `tqdm`

## インストール (Installation)

1.  **リポジトリのクローン (Clone the repository):**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
    または、スクリプトファイル (`mistral_ocr.py` とします) を直接ダウンロードします。

2.  **必要なライブラリのインストール (Install required libraries):**
    ```bash
    pip install -r requirements.txt
    ```

## 設定 (Configuration)

Mistral AI APIキーを環境変数 `MISTRAL_API_KEY` に設定する必要があります。

**Linux/macOS:**
```bash
export MISTRAL_API_KEY='YOUR_API_KEY'
```
Windows (Command Prompt):
```bash
set MISTRAL_API_KEY=YOUR_API_KEY
```
Windows (PowerShell):
```bash
$env:MISTRAL_API_KEY='YOUR_API_KEY'
```
YOUR_API_KEY は実際のAPIキーに置き換えてください。セキュリティのため、APIキーを直接スクリプトに書き込まないでください。

## 使い方 (Usage)

スクリプトはコマンドラインから実行します。

### ローカルのPDFファイルを処理する場合:

```bash
python mistral_ocr.py <input_pdf_file> <output_markdown_file>
```
例:
```bash
python mistral_ocr.py my_document.pdf ./output/my_document_ocr.md
```
### URLを指定して処理する場合:
```bash
python mistral_ocr.py <document_url> <output_markdown_file> --url 
```

例:
```bash
python mistral_ocr.py https://example.com/document.pdf ./output/web_document_ocr.md --url 
```

ヘルプ表示:
```bash
python mistral_ocr.py -h
```

## 出力 (Output)

スクリプトは以下のファイルを生成します:
	1.	Markdownファイル: 指定された `<output_markdown_file>` に、OCR結果のテキストがMarkdown形式で保存されます。
	2.	画像ファイル: OCR中に検出された画像が、Markdownファイルと同じディレクトリに保存されます。画像ファイル名は画像のユニークIDに基づいており、Markdown内では相対パスで参照されます。

例:
`output/result.md` を指定した場合、出力は以下のようになります。

```tree
output/
├── result.md        <-- 生成されたMarkdownファイル
├── image_abc123.png <-- 抽出された画像1
└── image_def456.jpg <-- 抽出された画像2
```

注意点 (Notes)
	•	APIキーの管理: Mistral APIキーは機密情報です。環境変数を使用するなど、安全な方法で管理してください。
	•	エラーハンドリング: スクリプトは基本的なエラーハンドリング（ファイルの存在確認、APIエラーなど）を行い、詳細はログに出力します。問題が発生した場合はログを確認してください。
	•	URLのアクセス性: --url オプションを使用する場合、指定するURLは公開されており、Mistralのサーバーからアクセス可能である必要があります。
	•	処理時間: 大きなファイルや多数のページを持つドキュメントの場合、OCR処理には時間がかかることがあります。
	•	ログ表示と進捗バー: ログレベルが高すぎると tqdm のプログレスバーが乱れる場合があります。--log-level DEBUG などを使用することで解決する場合があります。



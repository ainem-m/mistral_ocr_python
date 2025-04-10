# -*- coding: utf-8 -*-

import argparse
import os
import logging
from pathlib import Path
from tqdm import tqdm  # ファイルの先頭で追加

from mistralai import Mistral
import datauri
import sys

# --- ロギング設定 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # 標準出力へ
    ],
)

# --- 定数 ---
MISTRAL_API_KEY_ENV_VAR = "MISTRAL_API_KEY"
OCR_MODEL = "mistral-ocr-latest"


def parse_args() -> argparse.Namespace:
    """
    コマンドライン引数を解析し、設定を保持するオブジェクトを返します。
    --url フラグが存在する場合、最初の引数はURLとして扱われます。

    Returns:
        argparse.Namespace: パースされたコマンドライン引数を保持するオブジェクト。
                            含まれる属性: input_source, output_file, url
    """
    parser = argparse.ArgumentParser(
        description=(
            "Mistral APIを使用してファイルまたはURLからOCR処理を実行し、"
            "結果をMarkdownファイルとして保存します。"
            " --url フラグを指定すると、最初の引数はURLとして扱われます。"
        )
    )
    # 必須引数: 入力ソース (ファイルパスまたはURL)
    # helpメッセージを修正
    parser.add_argument(
        "input_source",
        help="処理対象のPDFファイルパス、または --url が指定された場合はドキュメントのURL",
    )
    # 必須引数: 出力Markdownファイルパス
    parser.add_argument("output_file", help="出力するMarkdownファイルのパス")
    # オプション引数: --url フラグ (値は取らない)
    # action='store_true' に変更し、helpメッセージを修正
    parser.add_argument(
        "--url",
        action="store_true",  # 値を取らないフラグにする
        help="このフラグを指定すると、最初の引数 (input_source) がURLとして扱われます。",
    )
    args = parser.parse_args()
    # argsの属性名を input_source に変更したのでログも修正
    logging.info(
        f"コマンドライン引数を解析しました: input_source='{args.input_source}', output_file='{args.output_file}', url_flag={args.url}"
    )
    return args


def save_image(image: object, output_dir: Path):
    """
    OCRレスポンスに含まれるbase64エンコードされた画像をファイルとして保存します。
    ファイル名は画像IDを使用し、拡張子は付与しません。

    Args:
        image (object): Mistral APIのOCRレスポンス内の画像オブジェクト。
                        'id' と 'image_base64' 属性を持つ想定。
        output_dir (Path): 画像を保存するディレクトリのパス。
    """
    # 保存先のファイルパスを決定 (画像IDをファイル名とし、拡張子はなし)
    output_path = output_dir / image.id
    logging.debug(f"画像保存パスを設定: {output_path}")

    try:
        # Data URIをパースしてデータ部分を取得
        # image_base64 が None や空文字列の場合も考慮 (念のため)
        if not image.image_base64:
            logging.warning(
                f"画像データが空です (ID: {image.id})。ファイルは作成されません。"
            )
            return  # この画像の処理をスキップ

        parsed_uri = datauri.parse(image.image_base64)
        image_data = parsed_uri.data

        # ファイル書き込み
        logging.info(f"画像をファイルに書き込みます: {output_path}")
        with open(output_path, "wb") as file:
            file.write(image_data)
        logging.debug(f"画像 '{output_path.name}' の保存完了。")

    except datauri.DataURIError as e:
        # Data URI自体のパースエラー
        logging.error(
            f"画像Data URIのパースに失敗しました (ID: {image.id}): {e}", exc_info=True
        )
    except IOError as e:
        # ファイル書き込みエラー
        logging.error(
            f"画像ファイル '{output_path}' の書き込み中にエラーが発生しました: {e}",
            exc_info=True,
        )
        # エラーが発生した場合、ユーザーに通知することも検討
        # print(f"警告: 画像ファイル '{output_path}' の書き込みに失敗しました。", file=sys.stderr)
    except Exception as e:
        # その他の予期せぬエラー
        logging.error(
            f"画像 (ID: {image.id}) の保存処理中に予期せぬエラーが発生しました: {e}",
            exc_info=True,
        )


def create_markdown_file(ocr_response: object, output_file: Path):
    """
    OCRレスポンスからMarkdownコンテンツを抽出し、指定されたファイルに書き込みます。
    また、ページ内の画像を同じディレクトリに保存します。
    """
    logging.info(f"OCR結果をMarkdownファイル '{output_file}' に書き込みます...")
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_file, "wt", encoding="utf-8") as f:
            pages = ocr_response.pages
            for i, page in enumerate(
                tqdm(pages, desc="OCRページ処理中", unit="ページ")
            ):
                logging.debug(f"ページ {i + 1}/{len(pages)} のMarkdownを書き込み中...")
                f.write(page.markdown)
                if i < len(pages) - 1:
                    f.write("\n\n")  # ページ間に空行

                if hasattr(page, "images") and page.images:
                    for image in page.images:
                        save_image(image, output_dir)
                else:
                    logging.debug(f"ページ {i + 1} には画像が含まれていません。")

        logging.info(
            f"Markdownファイル '{output_file}' の作成と画像の保存が完了しました。"
        )
    except IOError as e:
        logging.error(
            f"Markdownファイル '{output_file}' の書き込み中にエラーが発生しました: {e}",
            exc_info=True,
        )
        sys.exit(1)
    except Exception as e:
        logging.error(
            f"Markdownファイル作成または画像保存中に予期せぬエラーが発生しました: {e}",
            exc_info=True,
        )
        sys.exit(1)


def main():
    """
    メイン処理関数。
    引数を解析し、Mistral APIクライアントを初期化し、
    ファイルアップロードまたはURL指定に基づいてOCRを実行し、
    結果をMarkdownファイルに保存します。
    """
    logging.info("スクリプト実行開始")
    args = parse_args()
    # 引数名を input_source に変更
    input_source = args.input_source
    output_file_path = Path(args.output_file)
    use_url = args.url  # --url フラグの状態

    # --- APIキーとクライアントの初期化 ---
    try:
        api_key = os.environ[MISTRAL_API_KEY_ENV_VAR]
        logging.info("Mistral APIキーを環境変数から読み込みました。")
        client = Mistral(api_key=api_key)
        logging.info("Mistral APIクライアントを初期化しました。")
    except KeyError:
        logging.error(f"環境変数 '{MISTRAL_API_KEY_ENV_VAR}' が設定されていません。")
        print(
            f"エラー: 環境変数 '{MISTRAL_API_KEY_ENV_VAR}' を設定してください。",
            file=sys.stderr,
        )
        sys.exit(1)  # エラー終了
    except Exception as e:
        logging.error(
            f"Mistral APIクライアントの初期化中にエラーが発生しました: {e}",
            exc_info=True,
        )
        sys.exit(1)  # エラー終了

    document_url = None

    # --- 入力ソースの決定とdocument_urlの取得 ---
    if use_url:
        # --url フラグが指定された場合、input_source をURLとして扱う
        document_url = input_source
        # 簡単なURL形式チェック（オプション）
        if not document_url.startswith(("http://", "https://")):
            logging.warning(
                f"指定された入力ソース '{document_url}' はURL形式ではない可能性がありますが、そのまま使用します。"
            )
        logging.info(
            f"--url フラグが指定されたため、入力ソースをURLとして使用します: {document_url}"
        )
    else:
        # --url フラグがない場合、input_source をファイルパスとして扱う
        pdf_file_path = Path(input_source)
        logging.info(
            f"--url フラグがないため、入力ソースをファイルパスとして扱います: {pdf_file_path}"
        )

        # ファイルの存在と形式をチェック
        if not pdf_file_path.exists() or not pdf_file_path.is_file():
            logging.error(
                f"指定されたファイルが見つからないか、ファイルではありません: '{pdf_file_path}'"
            )
            print(
                f"エラー: '{pdf_file_path}' は有効なファイルではありません。",
                file=sys.stderr,
            )
            sys.exit(1)  # エラー終了

        # --- ファイルアップロードと署名付きURL取得 ---
        try:
            logging.info(
                f"ファイル '{pdf_file_path}' をMistralにアップロードしています..."
            )
            with pdf_file_path.open("rb") as file:
                uploaded_pdf = client.files.upload(
                    file={"file_name": pdf_file_path.name, "content": file},
                    purpose="ocr",
                )
            logging.info(
                f"ファイル '{pdf_file_path}' がアップロードされました。 File ID: {uploaded_pdf.id}"
            )

            logging.info(
                f"アップロードされたファイル (ID: {uploaded_pdf.id}) の署名付きURLを取得しています..."
            )
            signed_url_response = client.files.get_signed_url(file_id=uploaded_pdf.id)
            document_url = signed_url_response.url
            logging.info(f"署名付きURLを取得しました: {document_url[:50]}...")

        except IOError as e:
            logging.error(
                f"ファイル '{pdf_file_path}' の読み込み中にエラーが発生しました: {e}",
                exc_info=True,
            )
            print(
                f"エラー: ファイル '{pdf_file_path}' の読み込み中にエラーが発生しました。",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            logging.error(
                f"ファイル処理中に予期せぬエラーが発生しました: {e}", exc_info=True
            )
            sys.exit(1)

    # document_url が最終的に設定されているか確認
    if not document_url:
        logging.error(
            "OCR処理に必要なドキュメントURLが設定されませんでした。ロジックエラーの可能性があります。"
        )
        sys.exit(1)

    # --- OCR処理の実行 ---
    try:
        logging.info(
            f"ドキュメントURLを使用してOCR処理を開始します (モデル: {OCR_MODEL})..."
        )
        ocr_response = client.ocr.process(
            model=OCR_MODEL,
            document={"type": "document_url", "document_url": document_url},
            include_image_base64=True,
        )
        logging.info(f"OCR処理が完了しました。ページ数: {len(ocr_response.pages)}")

    except Exception as e:
        logging.error(f"OCR処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

    # --- 結果の保存 ---
    try:
        create_markdown_file(ocr_response, output_file=output_file_path)
    except Exception as e:
        # create_markdown_file内でキャッチされなかった/sys.exitされなかったエラー
        logging.error(
            f"結果の保存処理の呼び出し後に予期せぬエラーが発生しました: {e}",
            exc_info=True,
        )
        sys.exit(1)

    logging.info("全ての処理が正常に完了しました。")
    print("Finished all!")  # ユーザー向けの完了メッセージ


if __name__ == "__main__":
    main()

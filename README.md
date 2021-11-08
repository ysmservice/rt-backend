# rt-backend
DiscordのBotであるRTのバックエンドです。  
ウェブページを提供しBotと通信を行いDiscordのOAuthなどを管理します。

## Contributing
`contributing.md`をご覧ください。

## Installation
### 環境
バージョン3.8以上ののPythonとMySQLまたはMariaDBが必要です。
### 必要なモジュールのインストール
`pip install -r requirements.txt`
### 必要な極秘情報ファイルの用意
`auth.template.json`のコピーとして`auth.json`を作りそのファイルに適切な情報を書き込んでください。
### 実行方法
`main.py`を動かすだけです。  
本番時には最後に引数で`production`をつけてください。
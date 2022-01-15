# API
RTののAPIのドキュメントです。

## Base
### ベースURL
`https://rt-bot.com/api`のURLから始まります。
### ベースデータ
```js
{
  "message": "ok" // 普通はokとなるがエラー時はエラー内容が入る。
  "status": 200 // ステータスコードです。
  "data": ... // 叩いたAPIのデータです。これからでてくるAPIのデータが入ります。
}
```

## APIs
### `/account`
現在ログインしているアカウントについての情報を返します。

```js
{
  "login": true, // ログインをしているかどうか
  "user_name": "Takkun#1643" // もしログインしているなら有効なユーザー名
}
```

### `/account/login` **NotAPI**
Discordにログインさせる部分。

### `/account/logout` **NotAPI**
Discordからログアウトさせる部分。

### `/news`
ニュースの一覧を返します。

```js
{
  "1": [
    "サンプル①", // news title
    "2021/06/05" // news date
  ],
  "2": [
    "サンプル②",
    "2021/06/06"
  ],
  "3": [
    "サンプル③",
    "2021/06/07"
  ]
}
```

## `/news/<news_number:int>`
ニュースの詳細データを返します。

```js
{
  "content": "あいうえお...", // ニュース内容
  "date": "2021/06/05", // news date
  "title": "サンプル①" // news title
}
```

## `/help/<group_name>`
ヘルプの一覧を返します。

```js
{
  "1": [
    "help", // コマンド名
    "Botのヘルプコマンド" // コマンドの内容を示す見出し
  ],
  "2": [
    "info",
    "Botの情報を表示"
  ],
  "title": "Bot関連" // コマンドのカテゴリー名
}
```

## `/help/<group_name>/<command_name>`
コマンドの詳細なヘルプ。

```js
{
  "content": "ヘルプコマンド...", // コマンドの説明
  "g-title": "Bot関連", // コマンドのカテゴリー名
}
```

## `/status` **未実装**
RTのステータス。

```js
{
  "cpu": [1.0], // List of cpu utilization
  "disk": [19.8], // List of disk utilization
  "labels": ["06/09 21:50"], // A list of times every 10 minutes from 24 hours ago (See the status function in API_saple/main.py for more information.)
  "memory": [43.5], // List of memory utilization
  "ping": [105], // List of ping values
  "server": [400], // List of number of servers
  "user": [19255], // List of number of users
}
```

# Backend

## Sanic App Types
```
app: sanic.Sanic
app.ctx.bot: DiscordBot for debug
app.ctx.oauth: OAuth 下の方で説明
```

## blueprints
Blueprintsフォルダに作ったPythonファイルまたはフォルダは`main.py`起動時に自動で読み込まれます。  
そして`main.py`は読み込んだファイルの`bp`という名前の変数を読み込みます。  
この変数に`sanic.Blueprint`のインスタンスを入れてください。  
大抵のエンドポイントは`blueprints`フォルダにプログラムを入れましょう。  
もし`app`を必要とするBlueprintを作る場合は`on_load`という関数を作ってください。  
この関数は`bp`を読み込もうとする前に`sanic.Sanic`を渡して呼び出されます。  
またできれば`sanic.Blueprint`ではなく`backend.TypedBlueprint`を使って欲しいです。  
理由はVSCodeやSublime TextそしてEmacsなどのPython拡張を入れたテキストエディタで型補完が効くからです。  
ちなみに`sanic.Sanic`は`backend.TypedSanic`です。

## Discord OAuth
DiscordのOAuthのエンドポイントを作るのに便利なクラス`backend.DiscordOAuth`が`app.ctx.oauth`にあります。  
使用方法は以下のようにデコレータで使います。
```python
# app: backend.TypedSanic

@app.ctx.oauth.require_login()
async def login(request: app.ctx.oauth.TypedRequest):
    print(f"{request.ctx.user.name} has logged in.")
    return sanic.response.text(f"Hi {request.ctx.user.name}.")
```
`app.ctx.oauth.require_login`というデコレータをRouteに付けると、そのRouteにアクセスした際にDiscordのOAuthの認可画面にリダイレクトされるようになります。
ログイン後はそのRouteに渡される`sanic.Request`の`ctx`の`user`すなわち`request.ctx.user`にdiscord.User`が入ります。  
それともし認可画面に行くのをスキップしたい場合はデコレータの引数に`force=True`を入れてください。

## Utils
### DatabaseManager
データベースを少し手軽に操作するためのクラスです。  
このクラスを継承したクラスで作った関数に`cursor`という引数を置けば自動で`aiomysql.Cursor`が渡されます。　　
それと`class.pool`に`aiomysql.Pool`を入れている必要があります。
#### Examples
```python
class DataManager(backend.utils.DatabaseManager):
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    async def get(self, user_id: int, cursor: aiomysql.Cursor = None):
        await cursor.execute(
            "SELECT * FROM Users WHERE UserID = %s;",
            (user_id,)
        )
        return await cursor.fetchone()

...

data = DataManager(pool)
print("Data :", await data.get(user_id))
```
### Cooldown
Routeに何秒に一度までといったようなクールダウンを設定するためのデコレータです。  
以下のように使用します。
```python
@backend.utils.cooldown(bp, 10)
async def test(request: Request):
    ...
```
### api
APIのためのレスポンスを簡単に作るための関数です。
```python
return api(
    "メッセージ", データ, ステータスコード=200, **kwargs
)
```
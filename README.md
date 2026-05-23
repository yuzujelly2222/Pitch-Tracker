# Pitch Tracker

<div id="top"></div>

## プロジェクトについて

Pitch Tracker は、野球の一球ごとの投球データを分析・可視化する Flask ベースのWebアプリケーションです。

DB に保存された投球データをもとに：

- 配球チャート
- 球種割合円グラフ
- 詳細データテーブル
- 打撃成績 / 被打成績

を生成し、投手・打者の傾向分析を行えます。

---

## 使用技術

### Backend

- Python 3.11
- Flask 3.1.3
- SQLAlchemy 2.0.49

### Database

- MariaDB 11.8.6
- mysql-connector-python 9.7.0

### Visualization

- matplotlib 3.10.9
- numpy

### Environment

- Debian GNU/Linux 13

---

## 目次

1. [プロジェクトについて](#プロジェクトについて)
2. [使用技術](#使用技術)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [Database Schema](#database-schema)
5. [開発環境構築](#開発環境構築)
6. [ページ内容](#ページ内容)
7. [トラブルシューティング](#トラブルシューティング)

---

## ディレクトリ構成

```text
project/
├── app.py
├── result.json
├── requirements.txt
├── README.md
├── sql/
│   └── schema.sql
├── static/
│   └── style.css
└── templates/
    └── index.html
```

### ファイル説明

| File | Description |
|---|---|
| app.py | Flaskアプリ本体 |
| result.json | 打席結果分類データ |
| requirements.txt | 使用ライブラリ一覧 |
| README.md | プロジェクト説明 |
| sql/schema.sql | データベース作成用SQL |
| static/style.css | CSSファイル |
| templates/index.html | トップページHTML |

<p align="right">(<a href="#top">トップへ</a>)</p>

---

## Database Schema

### games

| Column | Type | Description |
|---|---|---|
| id | INT | 試合ID |
| stadium | VARCHAR(255) | 球場名 |
| date | DATE | 試合日 |
| home_team | VARCHAR(255) | ホームチーム名 |
| visitor_team | VARCHAR(255) | ビジターチーム名 |

---

### at_bat

| Column | Type | Description |
|---|---|---|
| id | INT | 打席ID |
| game_id | INT | 対応する試合ID |
| inning | INT | イニング |
| batter | VARCHAR(255) | 打者名 |
| pitcher | VARCHAR(255) | 投手名 |

---

### pitches

| Column | Type | Description |
|---|---|---|
| id | INT | 投球ID |
| at_bat_id | INT | 対応する打席ID |
| inning | INT | イニング |
| number_of_pitches | INT | 打席内総投球数 |
| pitch_number | INT | 打席内何球目か |
| pitcher | VARCHAR(255) | 投手名 |
| pitcher_team | VARCHAR(255) | 投手チーム |
| batter | VARCHAR(255) | 打者名 |
| batter_team | VARCHAR(255) | 打者チーム |
| pitch_type | VARCHAR(255) | 球種 |
| speed | INT | 球速(km/h) |
| ball | INT | ボールカウント |
| strike | INT | ストライクカウント |
| outs | INT | アウトカウント |
| result | VARCHAR(255) | 投球結果・打席結果 |
| x | FLOAT | 投球位置X座標 |
| y | FLOAT | 投球位置Y座標 |
| first | INT | 一塁走者有無 (0/1) |
| second | INT | 二塁走者有無 (0/1) |
| third | INT | 三塁走者有無 (0/1) |

---

### 備考

`pitches.result` に対応する結果カテゴリは `result.json` を参照してください。

<p align="right">(<a href="#top">トップへ</a>)</p>

---

## 開発環境構築

### 1. MariaDB をインストール

```bash
sudo apt update
sudo apt install mariadb-server
```

---

### 2. DB とユーザーを作成

MariaDB にログイン：

```bash
sudo mariadb
```

DB・ユーザー作成例：

```sql
CREATE DATABASE baseball;

CREATE USER 'baseball'@'localhost'
IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES
ON baseball.*
TO 'baseball'@'localhost';

FLUSH PRIVILEGES;
```

---

### 3. app.py のDB接続情報を編集

```python
user = "youruser"
password = "yourpassword"
host = "yourhost"
db_name = "yourdbname"
```

---

### 4. schema.sql を実行

```bash
mysql -u USERNAME -p DATABASE_NAME < sql/schema.sql
```

---

### 5. 仮想環境作成

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 6. ライブラリをインストール

```bash
pip install -r requirements.txt
```

---

### 7. DBへデータを入力

`pitches` テーブルへ投球データを入力してください。

---

### 8. 座標範囲を調整

DB 内の座標データに応じて
以下の値を app.py 内で調整してください。

```python
X_MIN = 0
X_MAX = 200

Y_MIN = 0
Y_MAX = 250

STRIKE_X = 40
STRIKE_Y = 50

STRIKE_WIDTH = 120
STRIKE_HEIGHT = 140

ZONE_X = [
    STRIKE_X + STRIKE_WIDTH / 3,
    STRIKE_X + STRIKE_WIDTH / 3 * 2
]

ZONE_Y = [
    STRIKE_Y + STRIKE_HEIGHT / 3,
    STRIKE_Y + STRIKE_HEIGHT / 3 * 2
]
```

---

## 実行方法

ターミナルでプロジェクトフォルダへ移動後：

```bash
source venv/bin/activate
python app.py
```

Flask サーバーが 5000 番ポートで起動します。

<p align="right">(<a href="#top">トップへ</a>)</p>

---

## ページ内容

### `/`

トップページ。

打者分析ページ・投手分析ページへの移動を行います。

---

### `/b_input`

打者分析用検索フォーム。

検索条件：

- 打者名
- ボールカウント
- ストライクカウント
- アウトカウント
- ランナー状況
- 打席終了球のみ

---

### `/b_output`

打者分析結果ページ。

表示内容：

- 配球チャート
- 球種割合円グラフ
- 打席結果テーブル
- 打率
- 出塁率
- 長打率
- OPS

---

### `/p_input`

投手分析用検索フォーム。

検索条件：

- 投手名
- ボールカウント
- ストライクカウント
- アウトカウント
- ランナー状況
- 打席終了球のみ

---

### `/p_output`

投手分析結果ページ。

表示内容：

- 配球チャート
- 球種割合円グラフ
- 投球結果テーブル
- 被打率
- 被出塁率
- 被長打率
- 被OPS

<p align="right">(<a href="#top">トップへ</a>)</p>

---

## トラブルシューティング

現在、既知の問題はありません。

<p align="right">(<a href="#top">トップへ</a>)</p>
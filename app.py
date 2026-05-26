#======================
# ライブラリのインポート
# 及び専用関数の定義
#======================

from flask import Flask, request,render_template,url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, String, Date
import json
import matplotlib.pyplot as plt
import matplotlib.patches as ptc
import matplotlib.font_manager as fm
import numpy as np
import io
import base64

# このプロジェクトで有用なint型キャスト関数
def to_int(k):
    try:
        return int(k)
    except:
        return -1
#==========================
# 投球プロット用のグラフのxy
# 及びストライクゾーンの設定
#==========================
X_MIN = 0
X_MAX = 0

Y_MIN = 0
Y_MAX = 0

# ストライクゾーン
STRIKE_X = 0
STRIKE_Y = 0

STRIKE_WIDTH = 0
STRIKE_HEIGHT = 0

# ゾーン分割位置
ZONE_X = [
    STRIKE_X + STRIKE_WIDTH / 3,
    STRIKE_X + STRIKE_WIDTH / 3 * 2
]

ZONE_Y = [
    STRIKE_Y + STRIKE_HEIGHT / 3,
    STRIKE_Y + STRIKE_HEIGHT / 3 * 2
]

#=======================
# DBORMとmysql(mariaDB)
# の接続
#=======================

user = "youruser"
password = "yourpassword"
host = "yourhost"
db_name = "yourdbname"

# engineの設定
engine = create_engine(
    f'mysql+mysqlconnector://{user}:{password}@{host}/{db_name}'
)

# セッションの作成
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Base
Base = declarative_base()
Base.query = db_session.query_property()

# ゲームごと分割テーブルのクラス
class Games(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    stadium = Column(String(255))
    date = Column(Date)
    home_team = Column(String(255))
    visitor_team = Column(String(255))

# 打席分割ごとのテーブルのクラス
class Bats(Base):
    __tablename__ = "at_bat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer)
    inning = Column(Integer)
    batter = Column(String(255))
    pitcher = Column(String(255))

# 1球ごとのテーブルのクラス
class Pitchs(Base):
    __tablename__ = "pitches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    at_bat_id = Column(Integer)
    inning = Column(Integer)
    number_of_pitches = Column(Integer)
    pitch_number = Column(Integer)

    pitcher = Column(String(255))
    pitcher_team = Column(String(255))

    batter = Column(String(255))
    batter_team = Column(String(255))

    pitch_type = Column(String(255))
    speed = Column(Integer)

    ball = Column(Integer)
    strike = Column(Integer)
    outs = Column(Integer)

    result = Column(String(255))

    x = Column(Float)
    y = Column(Float)

    first = Column(Integer)
    second = Column(Integer)
    third = Column(Integer)



Base.metadata.create_all(bind=engine)

#====================
# 投手と打者の全選手
# (選択肢リストの作成)
#====================

results_b = []
results_p = []
for result in db_session.query(Pitchs).all():
    if not result.batter  in results_b:
        results_b.append(result.batter)
    if not result.pitcher in results_p:
        results_p.append(result.pitcher)

#======================
# 以下メインのappの作成
#======================


app = Flask(__name__)

# トップページ
@app.route('/')
def index():
    return render_template('./index.html')

# 打者側インプットページ
@app.route('/b_input')
def b_input():
    return render_template(
        "form.html",
        results=results_b,
        side="打者",
        page="/b_output"
    )

# 打者側アウトプットページ
@app.route('/b_output', methods=["GET", "POST"])
def b_output():

    if request.method == "GET":
        return "エラー"
    
    # 円グラフ用データリスト 
    table_rows = []
    # POSTメソッドよりデータをゲット
    player = request.form['player']

    bcount = to_int(request.form['bcount'])
    scount = to_int(request.form['scount'])
    ocount = to_int(request.form['ocount'])

    fflag = to_int(request.form['fflag'])
    sflag = to_int(request.form['sflag'])
    tflag = to_int(request.form['tflag'])
    finish_flag = to_int(request.form.get('finish','0'))
    
    # テーブル検索条件リストの作成
    filter_list = [Pitchs.batter == player]

    # 以下で条件を追加
    if 0 <= bcount <= 3:
        filter_list.append(Pitchs.ball == bcount)

    if 0 <= scount <= 2:
        filter_list.append(Pitchs.strike == scount)

    if 0 <= ocount <= 2:
        filter_list.append(Pitchs.outs == ocount)

    if 0 <= fflag <= 1:
        filter_list.append(Pitchs.first == fflag)

    if 0 <= sflag <= 1:
        filter_list.append(Pitchs.second == sflag)

    if 0 <= tflag <= 1:
        filter_list.append(Pitchs.third == tflag)
    
    # Pitchsテーブルよりデータを取得
    sql_data = db_session.query(Pitchs).filter(*filter_list).all()

    # 結果判定用のjson,result.jsonをロード
    with open("result.json", mode="rt", encoding="utf-8") as f:
        all_data = json.load(f)

    # 成績
    hit = 0
    bb = 0
    trun = 0
    at_bat = 0
    all_base = 0
    obp = 0
    avg = 0
    slg = 0
    ops = 0

    # 球種カラー
    pitch_color = {
        "ストレート": "#e74c3c",
        "カットボール": "#e67e22",
        "チェンジアップ": "#2ecc71",
        "フォーク": "#3498db",
        "カーブ": "#9b59b6",
        "スライダー": "#00cec9",
        "シュート": "#fd79a8",
        "シンカー": "#795548",
        "特殊球": "#2d3436"
    }

    pitch_dict = {}
    
    for result in sql_data:
        # result.json検索用のkeyを保存
        key = result.result

        # 終了球のみ検索のとき終了球以外のときcontinueで省く
        if (not all_data[key]["is_terminal"]) and finish_flag:
            continue

        # 初めての変化球の時だけpitch_dictの中に座標用dictを追加
        if result.pitch_type not in pitch_dict:

            pitch_dict[result.pitch_type] = {
                "x": [],
                "y": []
            }
        
        # pitch_dictに座標を追加
        pitch_dict[result.pitch_type]["x"].append(result.x)
        pitch_dict[result.pitch_type]["y"].append(result.y)
        

        #その投球の試合の日付を取得
        date = db_session.query(Games).filter(
            Games.id == db_session.query(Bats).filter(
                Bats.id == result.at_bat_id
            ).first().game_id
        ).first().date

        result_category = all_data[key]["category"]

        # 結果によって行カラーをつける
        if result_category == "hit":
            row_class = "hit"
        elif result_category == "walk":
            row_class = "walk"
        else:
            row_class = "out"

        # 成績計算
        # 打席を加算
        trun += 1

        # 打数計算
        if not (result_category == "walk" or result_category == "sacrifice" or result_category == "sac_bunt_fc" or result_category == "sac_bunt_error"):
            at_bat += 1

        # ヒット数,塁打数計算
        if result_category == "hit":
            hit += 1
            all_base += all_data[key]["base"]

        # 四死球加算
        if result_category == "walk":
            bb += 1
        
        # 球種によって色を付ける
        pitch_style = pitch_color.get(result.pitch_type, "#2d3436")
        # htmlに渡すtable_rowsにデータを追加
        table_rows.append({
            "date": date,
            "pitcher_team": result.pitcher_team,
            "pitcher": result.pitcher,
            "batter_team": result.batter_team,
            "batter": result.batter,
            "count": f"{result.ball}-{result.strike}-{result.outs}",
            "base": f"{result.third}-{result.second}-{result.first}",
            "pitch_type": result.pitch_type,
            "pitch_style": pitch_style,
            "speed": result.speed,
            "result": result.result,
            "row_class": row_class
        })

    # 成績計算
    if trun:
        obp = (hit + bb) / trun

    if at_bat:
        avg = hit / at_bat
        slg = all_base / at_bat

    ops = obp + slg
    #=======================
    #   プロットと円グラフ  
    #=======================
    pitch_colors = {
        'ストレート': '#e74c3c',
        'カットボール': '#e67e22',
        'チェンジアップ': '#2ecc71',
        'フォーク': '#3498db',
        'カーブ': '#9b59b6',
        'スライダー': '#00cec9',
        'シュート': '#fd79a8',
        'シンカー': '#795548',
        '特殊球': '#2d3436',
        None: '#636e72'
    }

    # =========================
    # matplotlib配球図
    # =========================

    # フォントをロード
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_prop = fm.FontProperties(fname=font_path)

    # plt初期化
    fig, ax = plt.subplots(figsize=(8, 8))

    # 背景色を設定
    fig.patch.set_facecolor("#f5f6fa")
    ax.set_facecolor("white")

    # ストライクゾーンを設定
    strike_zone = ptc.Rectangle(
        (STRIKE_X, STRIKE_Y),
        STRIKE_WIDTH,
        STRIKE_HEIGHT,
        fill=False,
        edgecolor="#0984e3",
        linewidth=4
    )
    ax.add_patch(strike_zone)

    # ゾーン分割
    for x in ZONE_X:

        plt.plot(
            [x, x],
            [50, 190],
            color="#74b9ff",
            alpha=0.5
        )

    for y in ZONE_Y:

        plt.plot(
            [STRIKE_X, STRIKE_X + STRIKE_WIDTH],
            [y, y],
            color="#74b9ff",
            alpha=0.5
        )

    # 散布図
    for key in pitch_dict:

        plt.scatter(
            pitch_dict[key]["x"],
            pitch_dict[key]["y"],

            color=pitch_colors.get(key, "#636e72"),

            label="不明" if key is None else key,

            s=120,
            alpha=0.85,

            edgecolors="black",
            linewidths=1.2
        )

    # 軸の上限,軸ラベルを設定
    plt.xlim(X_MIN, X_MAX)
    plt.ylim(Y_MIN, Y_MAX)
    plt.xticks(np.arange(X_MIN, X_MAX + 1, 10))
    plt.yticks(np.arange(Y_MIN, Y_MAX + 1, 10))
    plt.xlabel(
        "横方向",
        fontsize=15,
        fontproperties=font_prop
    )
    plt.ylabel(
        "高さ",
        fontsize=15,
        fontproperties=font_prop
    )

    # タイトルの設定
    plt.title(
        f"{player} 配球チャート",
        fontsize=24,
        fontproperties=font_prop
    )

    # グリッド線の設定
    plt.grid(
        color="#dfe6e9",
        linestyle="--",
        linewidth=0.7,
        alpha=0.8
    )

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # yを反転
    ax.invert_yaxis()

    plt.axis('equal')

    legend = plt.legend(
        prop=font_prop,
        fontsize=12,
        frameon=True,
        fancybox=True,
        shadow=True
    )

    legend.get_frame().set_facecolor("white")

    img = io.BytesIO()

    plt.savefig(
        img,
        format='png',
        dpi=250,
        bbox_inches='tight',
        facecolor=fig.get_facecolor()
    )

    img.seek(0)

    img_base64 = base64.b64encode(
        img.getvalue()
    ).decode("utf-8")

    plt.close()

    # =========================
    # 円グラフデータ
    # =========================

    chart_data = []

    total = 0

    # pitch_dictから参照してデータを設定
    for key in pitch_dict:

        count = len(pitch_dict[key]["x"])

        total += count

        chart_data.append({
            "name": "不明" if key is None else key,
            "count": count,
            "color": pitch_colors.get(key, "#636e72")
        })

    # パーセント計算
    for item in chart_data:

        item["value"] = round(
            item["count"] / total * 100,
            1
        )

    # 降順
    chart_data = sorted(
        chart_data,
        key=lambda x: x["value"],
        reverse=True
    )

    # 小さい割合をその他へ
    new_chart_data = []

    other_count = 0

    for item in chart_data:

        if item["value"] < 3:

            other_count += item["count"]

        else:

            new_chart_data.append(item)

    if other_count > 0:

        new_chart_data.append({
            "name": "その他",
            "count": other_count,
            "value": round(
                other_count / total * 100,
                1
            ),
            "color": "#b2bec3"
        })
    
    return render_template(
    "result.html",
    avg=avg,
    obp=obp,
    slg=slg,
    ops=ops,
    player=player,
    img_base64=img_base64,
    data_list=new_chart_data,
    table_rows=table_rows,
    hi=""
    )

# 投者側インプットページ
@app.route('/p_input')
def p_input():
    return render_template(
        "form.html",
        results=results_p,
        side="投手",
        page="/p_output"
    )

# 投者側アウトプットページ
@app.route('/p_output', methods=["GET", "POST"])
def p_output():

    if request.method == "GET":
        return "エラー"

    # 円グラフ用データリスト
    table_rows = []

    # POSTメソッドよりデータをゲット
    player = request.form['player']

    bcount = to_int(request.form['bcount'])
    scount = to_int(request.form['scount'])
    ocount = to_int(request.form['ocount'])

    fflag = to_int(request.form['fflag'])
    sflag = to_int(request.form['sflag'])
    tflag = to_int(request.form['tflag'])
    finish_flag = to_int(request.form.get('finish', '0'))

    # テーブル検索条件リストの作成
    filter_list = [Pitchs.pitcher == player]

    # 以下で条件を追加
    if 0 <= bcount <= 3:
        filter_list.append(Pitchs.ball == bcount)

    if 0 <= scount <= 2:
        filter_list.append(Pitchs.strike == scount)

    if 0 <= ocount <= 2:
        filter_list.append(Pitchs.outs == ocount)

    if 0 <= fflag <= 1:
        filter_list.append(Pitchs.first == fflag)

    if 0 <= sflag <= 1:
        filter_list.append(Pitchs.second == sflag)

    if 0 <= tflag <= 1:
        filter_list.append(Pitchs.third == tflag)

    # Pitchsテーブルよりデータを取得
    sql_data = db_session.query(Pitchs).filter(*filter_list).all()

    # 結果判定用のjson,result.jsonをロード
    with open("result.json", mode="rt", encoding="utf-8") as f:
        all_data = json.load(f)

    # 成績
    hit = 0
    bb = 0
    trun = 0
    at_bat = 0
    all_base = 0
    obp = 0
    avg = 0
    slg = 0
    ops = 0

    # 球種カラー
    pitch_color = {
        "ストレート": "#e74c3c",
        "カットボール": "#e67e22",
        "チェンジアップ": "#2ecc71",
        "フォーク": "#3498db",
        "カーブ": "#9b59b6",
        "スライダー": "#00cec9",
        "シュート": "#fd79a8",
        "シンカー": "#795548",
        "特殊球": "#2d3436"
    }

    pitch_dict = {}

    for result in sql_data:

        # result.json検索用のkeyを保存
        key = result.result

        # 終了球のみ検索のとき終了球以外のときcontinueで省く
        if (not all_data[key]["is_terminal"]) and finish_flag:
            continue

        # 初めての変化球の時だけpitch_dictの中に座標用dictを追加
        if result.pitch_type not in pitch_dict:

            pitch_dict[result.pitch_type] = {
                "x": [],
                "y": []
            }

        # pitch_dictに座標を追加
        pitch_dict[result.pitch_type]["x"].append(result.x)
        pitch_dict[result.pitch_type]["y"].append(result.y)

        # その投球の試合の日付を取得
        date = db_session.query(Games).filter(
            Games.id == db_session.query(Bats).filter(
                Bats.id == result.at_bat_id
            ).first().game_id
        ).first().date

        result_category = all_data[key]["category"]

        # 行カラー
        if result_category == "hit":
            row_class = "hit"

        elif result_category == "walk":
            row_class = "walk"

        else:
            row_class = "out"

        # 成績計算

        # 打席を加算
        trun += 1

        # 打数計算
        if not (result_category == "walk" or result_category == "sacrifice" or result_category == "sac_bunt_fc" or result_category == "sac_bunt_error"):
            at_bat += 1

        # ヒット数,塁打数計算
        if result_category == "hit":
            hit += 1
            all_base += all_data[key]["base"]

        # 四死球加算
        if result_category == "walk":
            bb += 1

        # 球種によって色を付ける
        pitch_style = pitch_color.get(result.pitch_type, "#2d3436")

        # htmlに渡すtable_rowsにデータを追加
        table_rows.append({
            "date": date,
            "pitcher_team": result.pitcher_team,
            "pitcher": result.pitcher,
            "batter_team": result.batter_team,
            "batter": result.batter,
            "count": f"{result.ball}-{result.strike}-{result.outs}",
            "base": f"{result.third}-{result.second}-{result.first}",
            "pitch_type": result.pitch_type,
            "pitch_style": pitch_style,
            "speed": result.speed,
            "result": result.result,
            "row_class": row_class
        })

    # 成績計算
    if trun:
        obp = (hit + bb) / trun

    if at_bat:
        avg = hit / at_bat
        slg = all_base / at_bat

    ops = obp + slg

    #=======================
    #   プロットと円グラフ
    #=======================

    pitch_colors = {
        'ストレート': '#e74c3c',
        'カットボール': '#e67e22',
        'チェンジアップ': '#2ecc71',
        'フォーク': '#3498db',
        'カーブ': '#9b59b6',
        'スライダー': '#00cec9',
        'シュート': '#fd79a8',
        'シンカー': '#795548',
        '特殊球': '#2d3436',
        None: '#636e72'
    }

    # =========================
    # matplotlib配球図
    # =========================

    # フォントをロード
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_prop = fm.FontProperties(fname=font_path)

    # plt初期化
    fig, ax = plt.subplots(figsize=(8, 8))

    # 背景色を設定
    fig.patch.set_facecolor("#f5f6fa")
    ax.set_facecolor("white")

    # ストライクゾーンを設定
    strike_zone = ptc.Rectangle(
        (STRIKE_X, STRIKE_Y),
        STRIKE_WIDTH,
        STRIKE_HEIGHT,
        fill=False,
        edgecolor="#0984e3",
        linewidth=4
    )

    ax.add_patch(strike_zone)

    # ゾーン分割
    for x in ZONE_X:

        plt.plot(
            [x, x],
            [50, 190],
            color="#74b9ff",
            alpha=0.5
        )

    for y in ZONE_Y:

        plt.plot(
            [STRIKE_X, STRIKE_X + STRIKE_WIDTH],
            [y, y],
            color="#74b9ff",
            alpha=0.5
        )

    # 散布図
    for key in pitch_dict:

        plt.scatter(
            pitch_dict[key]["x"],
            pitch_dict[key]["y"],

            color=pitch_colors.get(key, "#636e72"),

            label="不明" if key is None else key,

            s=120,
            alpha=0.85,

            edgecolors="black",
            linewidths=1.2
        )

    # 軸の上限,軸ラベルを設定
    plt.xlim(X_MIN, X_MAX)
    plt.ylim(Y_MIN, Y_MAX)
    plt.xticks(np.arange(X_MIN, X_MAX + 1, 10))
    plt.yticks(np.arange(Y_MIN, Y_MAX + 1, 10))

    plt.xlabel(
        "横方向",
        fontsize=15,
        fontproperties=font_prop
    )

    plt.ylabel(
        "高さ",
        fontsize=15,
        fontproperties=font_prop
    )

    # タイトルの設定
    plt.title(
        f"{player} 配球チャート",
        fontsize=24,
        fontproperties=font_prop
    )

    # グリッド線の設定
    plt.grid(
        color="#dfe6e9",
        linestyle="--",
        linewidth=0.7,
        alpha=0.8
    )

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # yを反転
    ax.invert_yaxis()

    plt.axis('equal')

    legend = plt.legend(
        prop=font_prop,
        fontsize=12,
        frameon=True,
        fancybox=True,
        shadow=True
    )

    legend.get_frame().set_facecolor("white")

    img = io.BytesIO()

    plt.savefig(
        img,
        format='png',
        dpi=250,
        bbox_inches='tight',
        facecolor=fig.get_facecolor()
    )

    img.seek(0)

    img_base64 = base64.b64encode(
        img.getvalue()
    ).decode("utf-8")

    plt.close()

    # =========================
    # 円グラフデータ
    # =========================

    chart_data = []

    total = 0

    # pitch_dictから参照してデータを設定
    for key in pitch_dict:

        count = len(pitch_dict[key]["x"])

        total += count

        chart_data.append({
            "name": "不明" if key is None else key,
            "count": count,
            "color": pitch_colors.get(key, "#636e72")
        })

    # パーセント計算
    for item in chart_data:

        item["value"] = round(
            item["count"] / total * 100,
            1
        )

    # 降順
    chart_data = sorted(
        chart_data,
        key=lambda x: x["value"],
        reverse=True
    )

    # 小さい割合をその他へ
    new_chart_data = []

    other_count = 0

    for item in chart_data:

        if item["value"] < 3:

            other_count += item["count"]

        else:

            new_chart_data.append(item)

    if other_count > 0:

        new_chart_data.append({
            "name": "その他",
            "count": other_count,
            "value": round(
                other_count / total * 100,
                1
            ),
            "color": "#b2bec3"
        })

    return render_template(
        "result.html",
        avg=avg,
        obp=obp,
        slg=slg,
        ops=ops,
        player=player,
        img_base64=img_base64,
        data_list=new_chart_data,
        table_rows=table_rows,
        hi="被"
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
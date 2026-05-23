from flask import Flask, request, send_file, render_template,url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, String, Date
import json
import matplotlib.pyplot as plt
import matplotlib.patches as ptc
import matplotlib
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np
import io
import base64
def to_int(k):
    try:
        return int(k)
    except:
        return -1
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

class Games(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    stadium = Column(String(255))
    date = Column(Date)
    home_team = Column(String(255))
    visitor_team = Column(String(255))

    def __repr__(self):
        return f"<Games(id={self.id}, stadium={self.stadium})>"


class Bats(Base):
    __tablename__ = "at_bat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer)
    inning = Column(Integer)
    batter = Column(String(255))
    pitcher = Column(String(255))


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
results_b = []
results_p = []
for result in db_session.query(Pitchs).all():
    if not result.batter  in results_b:
        results_b.append(result.batter)
    if not result.pitcher in results_p:
        results_p.append(result.pitcher)
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('./index.html')


@app.route('/b_input')
def b_input():

    bs = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
    <meta charset="UTF-8">
    <title>打者側検索フォーム</title>
    <style>

    body{
        font-family:sans-serif;
        background:#f5f6fa;
        padding:30px;
    }

    .container{
        width:500px;
        margin:auto;
        background:white;
        padding:30px;
        border-radius:20px;
        box-shadow:0 0 15px rgba(0,0,0,0.1);
    }

    h1{
        text-align:center;
        color:#2d3436;
        margin-bottom:30px;
    }

    label{
        font-weight:bold;
        color:#2d3436;
        display:block;
        margin-top:15px;
        margin-bottom:5px;
    }

    select,
    input[type="number"]{
        width:100%;
        padding:12px;
        border:1px solid #dcdde1;
        border-radius:10px;
        font-size:16px;
        box-sizing:border-box;
        transition:0.2s;
    }

    select:focus,
    input[type="number"]:focus{
        border-color:#0984e3;
        outline:none;
        box-shadow:0 0 5px rgba(9,132,227,0.4);
    }

    .base-area{
        display:grid;
        grid-template-columns:1fr 1fr 1fr;
        gap:10px;
    }

    .count-area{
        display:grid;
        grid-template-columns:1fr 1fr 1fr;
        gap:10px;
    }

    input[type="submit"]{
        width:100%;
        margin-top:30px;
        padding:15px;
        border:none;
        border-radius:12px;
        background:#0984e3;
        color:white;
        font-size:18px;
        font-weight:bold;
        cursor:pointer;
        transition:0.2s;
    }

    input[type="submit"]:hover{
        background:#74b9ff;
        transform:scale(1.02);
    }

    .card{
        background:#f8f9fa;
        padding:15px;
        border-radius:15px;
        margin-top:20px;
    }

    </style>

    </head>

    <body>

    <div class="container">

    <h1>打者側フォーム</h1>

    <form action="/b_output" method="post">

    <label for="player">打者選択</label>

    <select name="player" id="player">
    <option value="">--1つ選択してください--</option>
    """

    for name in results_b:
        bs += f'<option value="{name}">{name}</option>'

    bs += """

    </select>

    <div class="card">

        <label>カウント</label>

        <div class="count-area">

            <div>
                <label>ボール</label>
                <input type="number" name="bcount" min="-1" max="3" value="-1">
            </div>

            <div>
                <label>ストライク</label>
                <input type="number" name="scount" min="-1" max="2" value="-1">
            </div>

            <div>
                <label>アウト</label>
                <input type="number" name="ocount" min="-1" max="2" value="-1">
            </div>

        </div>

    </div>

    <div class="card">

        <label>ランナー状況</label>

        <div class="base-area">

            <div>
                <label>1塁</label>
                <input type="number" name="fflag" min="-1" max="1" value="-1">
            </div>

            <div>
                <label>2塁</label>
                <input type="number" name="sflag" min="-1" max="1" value="-1">
            </div>

            <div>
                <label>3塁</label>
                <input type="number" name="tflag" min="-1" max="1" value="-1">
            </div>

        </div>
        <div class="finish">
            <div>
                <label>打席終了球のみ</label>
                <input type="checkbox" name="finish" value="1">
            </div>
        </div>

    </div>

    <input type="submit" value="検索">

    </form>

    </div>

    </body>
    </html>
    """

    return bs

@app.route('/b_output', methods=["GET", "POST"])
def b_output():

    if request.method == "GET":
        return "エラー"

    batter = request.form['player']

    bcount = to_int(request.form['bcount'])
    scount = to_int(request.form['scount'])
    ocount = to_int(request.form['ocount'])

    fflag = to_int(request.form['fflag'])
    sflag = to_int(request.form['sflag'])
    tflag = to_int(request.form['tflag'])
    finish_flag = to_int(request.form.get('finish','0'))
    filter_list = [Pitchs.batter == batter]

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

    sql_data = db_session.query(Pitchs).filter(*filter_list).all()

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

    head_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
    <title>検索結果</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="{ url_for('static', filename='style.css') }">
    </head>
    <body>

    <h1>検索結果</h1>
    """

    table_html="""
    <table>
        <thead>
            <tr>
                <th>日付</th>
                <th>投手チーム</th>
                <th>投手</th>
                <th>打者チーム</th>
                <th>打者</th>
                <th>カウント</th>
                <th>塁状況</th>
                <th>球種</th>
                <th>球速</th>
                <th>結果</th>
            </tr>
        </thead>
        <tbody>
    """
    pitch_dict = {}
    for result in sql_data:
        key = result.result
        if (not all_data[key]["is_terminal"]) and finish_flag:
            continue
        if result.pitch_type not in pitch_dict:

            pitch_dict[result.pitch_type] = {
                "x": [],
                "y": []
            }

        pitch_dict[result.pitch_type]["x"].append(result.x)
        pitch_dict[result.pitch_type]["y"].append(result.y)
        


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
        trun += 1

        if not (result_category == "walk" or result_category == "sacrifice" or result_category == "sac_bunt_fc"):
            at_bat += 1

        if result_category == "hit":
            hit += 1
            all_base += all_data[key]["base"]

        if result_category == "walk":
            bb += 1

        pitch_style = pitch_color.get(result.pitch_type, "#2d3436")

        table_html += f"""
        <tr class="{row_class}">
            <td>{date}</td>
            <td>{result.pitcher_team}</td>
            <td>{result.pitcher}</td>
            <td>{result.batter_team}</td>
            <td>{result.batter}</td>
            <td>{result.ball}-{result.strike}-{result.outs}</td>
            <td>{result.third}-{result.second}-{result.first}</td>

            <td class="pitch" style="color:{pitch_style}">
                {result.pitch_type}
            </td>

            <td>{result.speed}km/h</td>
            <td>{result.result}</td>
        </tr>
        """
    table_html += """
        </tbody>
    </table>
    """

    # 成績計算
    if trun:
        obp = (hit + bb) / trun

    if at_bat:
        avg = hit / at_bat
        slg = all_base / at_bat

    ops = obp + slg

    score_html = f"""
    <div class="score">
        <span>打率: {avg:.3f}</span>
        <span>出塁率: {obp:.3f}</span>
        <span>長打率: {slg:.3f}</span>
        <span>OPS: {ops:.3f}</span>
    </div>
    """

    head_html = head_html.replace("<h1>検索結果</h1>", f"<h1>検索結果</h1>{score_html}")
    table_html += """
    </body>
    </html>
    """
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

    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_prop = fm.FontProperties(fname=font_path)

    fig, ax = plt.subplots(figsize=(8, 8))

    fig.patch.set_facecolor("#f5f6fa")
    ax.set_facecolor("white")

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

    plt.title(
        f"{batter} 配球チャート",
        fontsize=24,
        fontproperties=font_prop
    )

    plt.grid(
        color="#dfe6e9",
        linestyle="--",
        linewidth=0.7,
        alpha=0.8
    )

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

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

    chart_data = new_chart_data

    data_list_str = json.dumps(
        chart_data,
        ensure_ascii=False
    )
    circle_gragh = f"""
    <h1>{batter} 配球分析</h1>

    <div class="main">

        <div class="card chart-card">

            <h2>球種割合</h2>

            <canvas id="pieChart"
                    width="350"
                    height="350">
            </canvas>

            <div class="legend"
                 id="legend">
            </div>

        </div>

        <div class="card plot-card">

            <h2>配球チャート</h2>

            <img
                src="data:image/png;base64,{img_base64}"
            >

        </div>

    </div>

    <script>

    const data = {data_list_str};

    const canvas =
        document.getElementById("pieChart");

    const ctx =
        canvas.getContext("2d");

    const centerX =
        canvas.width / 2;

    const centerY =
        canvas.height / 2;

    const radius = 145;

    // 12時開始
    let startAngle = -Math.PI / 2;

    data.forEach(item => {{

        const sliceAngle =
            (item.value / 100)
            * Math.PI * 2;

        ctx.beginPath();

        ctx.moveTo(
            centerX,
            centerY
        );

        ctx.arc(
            centerX,
            centerY,
            radius,
            startAngle,
            startAngle + sliceAngle
        );

        ctx.closePath();

        ctx.fillStyle =
            item.color;

        ctx.fill();

        ctx.strokeStyle =
            "white";

        ctx.lineWidth = 3;

        ctx.stroke();

        // 小さい要素は外側
        const middleAngle =
            startAngle + sliceAngle / 2;

        const textRadius =
            item.value >= 10 ? 90 : 120;

        const textX =
            centerX
            + Math.cos(middleAngle) * textRadius;

        const textY =
            centerY
            + Math.sin(middleAngle) * textRadius;

        ctx.fillStyle = "white";

        ctx.font =
            "bold 16px sans-serif";

        ctx.textAlign = "center";

        // 5%以上のみ描画
        if(item.value >= 5){{

            ctx.fillText(
                item.value + "%",
                textX,
                textY
            );

        }}

        startAngle += sliceAngle;

    }});

    // ドーナツ化
    ctx.globalCompositeOperation =
        "destination-out";

    ctx.beginPath();

    ctx.arc(
        centerX,
        centerY,
        55,
        0,
        Math.PI * 2
    );

    ctx.fill();

    ctx.globalCompositeOperation =
        "source-over";

    // 中央文字
    ctx.fillStyle = "#2d3436";

    ctx.font = "bold 20px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "球種",
        centerX,
        centerY - 5
    );

    ctx.fillText(
        "割合",
        centerX,
        centerY + 25
    );

    // 凡例
    const legend =
        document.getElementById("legend");

    data.forEach((item, index) => {{

        legend.innerHTML += `

        <div class="item">

            <div class="color"
                 style="background:${{item.color}}">
            </div>

            <div>

                <b>
                    ${{index + 1}}.
                    ${{item.name}}
                </b>

                <br>

                ${{item.count}}球
                (${{item.value}}%)

            </div>

        </div>
        `;
    }});

    </script>
    """
    
    return head_html+circle_gragh+"<br><br>"+table_html

@app.route('/p_input')
def p_input():

    bs = f"""
    <!DOCTYPE html>
    <html lang="ja">

    <head>
    <meta charset="UTF-8">
    <title>投手側検索フォーム</title>
    <link rel="stylesheet" href="{ url_for('static', filename='style.css') }">

    </head>

    <body>

    <div class="container">

    <div class="pitch-icon">⚾</div>

    <h1>投手側検索フォーム</h1>

    <form action="/p_output" method="post">

    <label for="player">投手選択</label>

    <select name="player" id="player">

    <option value="">--1つ選択してください--</option>
    """

    for name in results_p:
        bs += f'<option value="{name}">{name}</option>'

    bs += """

    </select>

    <div class="card">

        <label>カウント条件</label>

        <div class="count-area">

            <div>
                <label>ボール</label>
                <input type="number" name="bcount" min="-1" max="3" value="-1">
            </div>

            <div>
                <label>ストライク</label>
                <input type="number" name="scount" min="-1" max="2" value="-1">
            </div>

            <div>
                <label>アウト</label>
                <input type="number" name="ocount" min="-1" max="2" value="-1">
            </div>

        </div>

    </div>

    <div class="card">

        <label>ランナー条件</label>

        <div class="base-area">

            <div>
                <label>1塁</label>
                <input type="number" name="fflag" min="-1" max="1" value="-1">
            </div>

            <div>
                <label>2塁</label>
                <input type="number" name="sflag" min="-1" max="1" value="-1">
            </div>

            <div>
                <label>3塁</label>
                <input type="number" name="tflag" min="-1" max="1" value="-1">
            </div>

        </div>
        <div class="finish">
            <div>
                <label>打席終了球のみ</label>
                <input type="checkbox" name="finish" value="1">
            </div>
        </div>
    </div>

    <input type="submit" value="配球チャート表示">

    </form>

    </div>

    </body>
    </html>
    """

    return bs


@app.route('/p_output', methods=["GET", "POST"])
def p_output():

    if request.method == "GET":
        return "エラー"

    pitcher = request.form['player']

    bcount = to_int(request.form['bcount'])
    scount = to_int(request.form['scount'])
    ocount = to_int(request.form['ocount'])

    fflag = to_int(request.form['fflag'])
    sflag = to_int(request.form['sflag'])
    tflag = to_int(request.form['tflag'])
    finish_flag = to_int(request.form.get('finish','0'))
    filter_list = [Pitchs.pitcher == pitcher]

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

    sql_data = db_session.query(Pitchs).filter(*filter_list).all()

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

    head_html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
    <title>検索結果</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="{ url_for('static', filename='style.css') }">
    </head>
    <body>

    <h1>検索結果</h1>
    """

    table_html="""
    <table>
        <thead>
            <tr>
                <th>日付</th>
                <th>投手チーム</th>
                <th>投手</th>
                <th>打者チーム</th>
                <th>打者</th>
                <th>カウント</th>
                <th>塁状況</th>
                <th>球種</th>
                <th>球速</th>
                <th>結果</th>
            </tr>
        </thead>
        <tbody>
    """
    pitch_dict = {}
    for result in sql_data:
        key = result.result
        if (not all_data[key]["is_terminal"]) and finish_flag:
            continue
        if result.pitch_type not in pitch_dict:

            pitch_dict[result.pitch_type] = {
                "x": [],
                "y": []
            }

        pitch_dict[result.pitch_type]["x"].append(result.x)
        pitch_dict[result.pitch_type]["y"].append(result.y)
        


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
        trun += 1

        if not (result_category == "walk" or result_category == "sacrifice" or result_category == "sac_bunt_fc"):
            at_bat += 1

        if result_category == "hit":
            hit += 1
            all_base += all_data[key]["base"]

        if result_category == "walk":
            bb += 1

        pitch_style = pitch_color.get(result.pitch_type, "#2d3436")

        table_html += f"""
        <tr class="{row_class}">
            <td>{date}</td>
            <td>{result.pitcher_team}</td>
            <td>{result.pitcher}</td>
            <td>{result.batter_team}</td>
            <td>{result.batter}</td>
            <td>{result.ball}-{result.strike}-{result.outs}</td>
            <td>{result.third}-{result.second}-{result.first}</td>

            <td class="pitch" style="color:{pitch_style}">
                {result.pitch_type}
            </td>

            <td>{result.speed}km/h</td>
            <td>{result.result}</td>
        </tr>
        """
    table_html += """
        </tbody>
    </table>
    """

    # 成績計算
    if trun:
        obp = (hit + bb) / trun

    if at_bat:
        avg = hit / at_bat
        slg = all_base / at_bat

    ops = obp + slg

    score_html = f"""
    <div class="score">
        <span>被打率: {avg:.3f}</span>
        <span>被出塁率: {obp:.3f}</span>
        <span>被長打率: {slg:.3f}</span>
        <span>被OPS: {ops:.3f}</span>
    </div>
    """

    head_html = head_html.replace("<h1>検索結果</h1>", f"<h1>検索結果</h1>{score_html}")
    table_html += """
    </body>
    </html>
    """
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

    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    font_prop = fm.FontProperties(fname=font_path)

    fig, ax = plt.subplots(figsize=(8, 8))

    fig.patch.set_facecolor("#f5f6fa")
    ax.set_facecolor("white")

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

    plt.title(
        f"{pitcher} 配球チャート",
        fontsize=24,
        fontproperties=font_prop
    )

    plt.grid(
        color="#dfe6e9",
        linestyle="--",
        linewidth=0.7,
        alpha=0.8
    )

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

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

    chart_data = new_chart_data

    data_list_str = json.dumps(
        chart_data,
        ensure_ascii=False
    )
    circle_gragh = f"""
    <h1>{pitcher} 配球分析</h1>

    <div class="main">

        <div class="card chart-card">

            <h2>球種割合</h2>

            <canvas id="pieChart"
                    width="350"
                    height="350">
            </canvas>

            <div class="legend"
                 id="legend">
            </div>

        </div>

        <div class="card plot-card">

            <h2>配球チャート</h2>

            <img
                src="data:image/png;base64,{img_base64}"
            >

        </div>

    </div>

    <script>

    const data = {data_list_str};

    const canvas =
        document.getElementById("pieChart");

    const ctx =
        canvas.getContext("2d");

    const centerX =
        canvas.width / 2;

    const centerY =
        canvas.height / 2;

    const radius = 145;

    // 12時開始
    let startAngle = -Math.PI / 2;

    data.forEach(item => {{

        const sliceAngle =
            (item.value / 100)
            * Math.PI * 2;

        ctx.beginPath();

        ctx.moveTo(
            centerX,
            centerY
        );

        ctx.arc(
            centerX,
            centerY,
            radius,
            startAngle,
            startAngle + sliceAngle
        );

        ctx.closePath();

        ctx.fillStyle =
            item.color;

        ctx.fill();

        ctx.strokeStyle =
            "white";

        ctx.lineWidth = 3;

        ctx.stroke();

        // 小さい要素は外側
        const middleAngle =
            startAngle + sliceAngle / 2;

        const textRadius =
            item.value >= 10 ? 90 : 120;

        const textX =
            centerX
            + Math.cos(middleAngle) * textRadius;

        const textY =
            centerY
            + Math.sin(middleAngle) * textRadius;

        ctx.fillStyle = "white";

        ctx.font =
            "bold 16px sans-serif";

        ctx.textAlign = "center";

        // 5%以上のみ描画
        if(item.value >= 5){{

            ctx.fillText(
                item.value + "%",
                textX,
                textY
            );

        }}

        startAngle += sliceAngle;

    }});

    // ドーナツ化
    ctx.globalCompositeOperation =
        "destination-out";

    ctx.beginPath();

    ctx.arc(
        centerX,
        centerY,
        55,
        0,
        Math.PI * 2
    );

    ctx.fill();

    ctx.globalCompositeOperation =
        "source-over";

    // 中央文字
    ctx.fillStyle = "#2d3436";

    ctx.font = "bold 20px sans-serif";

    ctx.textAlign = "center";

    ctx.fillText(
        "球種",
        centerX,
        centerY - 5
    );

    ctx.fillText(
        "割合",
        centerX,
        centerY + 25
    );

    // 凡例
    const legend =
        document.getElementById("legend");

    data.forEach((item, index) => {{

        legend.innerHTML += `

        <div class="item">

            <div class="color"
                 style="background:${{item.color}}">
            </div>

            <div>

                <b>
                    ${{index + 1}}.
                    ${{item.name}}
                </b>

                <br>

                ${{item.count}}球
                (${{item.value}}%)

            </div>

        </div>
        `;
    }});

    </script>
    """
    
    return head_html+circle_gragh+"<br><br>"+table_html
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
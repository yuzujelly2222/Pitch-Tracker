const data = DATA;

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

data.forEach(item => {

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
    if (item.value >= 5) {

        ctx.fillText(
            item.value + "%",
            textX,
            textY
        );
    }

    startAngle += sliceAngle;
});

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

data.forEach((item, index) => {

    legend.innerHTML += `

    <div class="item">

        <div class="color"
             style="background:${item.color}">
        </div>

        <div>

            <b>
                ${index + 1}.
                ${item.name}
            </b>

            <br>

            ${item.count}球
            (${item.value}%)

        </div>

    </div>
    `;
});
const data = DATA;
let combined = data.labels.map((label, i) => ({
    label: label,
    data: data.datasets[0].data[i],
    color: data.datasets[0].backgroundColor[i]
}));

// 降順ソート（大きい → 小さい）
combined.sort((a, b) => b.data - a.data);

// 元に戻す
data.labels = combined.map(v => v.label);
data.datasets[0].data = combined.map(v => v.data);
data.datasets[0].backgroundColor = combined.map(v => v.color);

var ctx = document.getElementById("pieChart");

var myDoughnutChart = new Chart(ctx, {
    type: 'doughnut',
    data: data,
    options: {
        title: {
            display: true,
            text: '球種割合'
        },
        tooltips: {
            callbacks: {
                label: function (tooltipItem, data) {

                    let dataset =
                        data.datasets[tooltipItem.datasetIndex];

                    let total =
                        dataset.data.reduce((a, b) => a + b, 0);

                    let current =
                        dataset.data[tooltipItem.index];

                    let percentage =
                        (current / total * 100).toFixed(1);

                    return (
                        data.labels[tooltipItem.index]
                        + ": "
                        + current
                        + "球 ("
                        + percentage
                        + "%)"
                    );
                }
            }
        }
    }
});
from pathlib import Path

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar, HeatMap, Line, Page, Pie, Sankey, Timeline
from pyecharts.globals import ThemeType


BASE_DIR = Path.cwd()

if (BASE_DIR / "olympic_medal_story" / "data").exists():
    BASE_DIR = BASE_DIR / "olympic_medal_story"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHART_DIR = OUTPUT_DIR / "charts"

ATHLETE_FILE = DATA_DIR / "参赛运动员数据集.xlsx"
MEDAL_FILE = DATA_DIR / "奖牌榜单数据集.xlsx"

MEDAL_COLORS = {
    "金牌": "#D9A441",
    "银牌": "#A7B0BA",
    "铜牌": "#B87333",
}


def chart_init(width="1100px", height="640px"):
    return opts.InitOpts(width=width, height=height, theme=ThemeType.LIGHT, bg_color="#FFFFFF")


def load_data():
    athlete_df = pd.read_excel(ATHLETE_FILE)
    medal_df = pd.read_excel(MEDAL_FILE)

    athlete_df["获奖时间"] = pd.to_datetime(athlete_df["获奖时间"], errors="coerce")
    athlete_df["获奖日期"] = athlete_df["获奖时间"].dt.date
    return athlete_df, medal_df


def medal_top10_bar(medal_df):
    top10 = medal_df.sort_values("奖牌总数", ascending=False).head(10).iloc[::-1]
    nations = top10["国家名称"].tolist()

    bar = (
        Bar(init_opts=chart_init())
        .add_xaxis(nations)
        .add_yaxis(
            "金牌",
            top10["金牌"].tolist(),
            stack="奖牌",
            color=MEDAL_COLORS["金牌"],
            category_gap="45%",
        )
        .add_yaxis(
            "银牌",
            top10["银牌"].tolist(),
            stack="奖牌",
            color=MEDAL_COLORS["银牌"],
            category_gap="45%",
        )
        .add_yaxis(
            "铜牌",
            top10["铜牌"].tolist(),
            stack="奖牌",
            color=MEDAL_COLORS["铜牌"],
            category_gap="45%",
        )
        .reversal_axis()
        .set_series_opts(label_opts=opts.LabelOpts(is_show=True, position="right"))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="东京奥运会奖牌榜 Top 10",
                subtitle="按奖牌总数排序，横向堆叠展示金银铜牌构成",
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            legend_opts=opts.LegendOpts(pos_top="12%", pos_left="center"),
            xaxis_opts=opts.AxisOpts(name="奖牌数量"),
            yaxis_opts=opts.AxisOpts(name="国家"),
        )
    )
    return bar


def project_gold_pie(athlete_df):
    gold_df = athlete_df[athlete_df["获奖名次"].eq("金牌")].copy()
    project_counts = gold_df.groupby("项目名").size().sort_values(ascending=False)
    top_projects = project_counts.head(12)
    other = project_counts.iloc[12:].sum()
    pie_data = list(zip(top_projects.index.tolist(), top_projects.astype(int).tolist()))
    if other:
        pie_data.append(("其他项目", int(other)))

    pie = (
        Pie(init_opts=chart_init())
        .add(
            "",
            pie_data,
            radius=["32%", "68%"],
            center=["45%", "55%"],
            rosetype="radius",
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="各项目金牌分布",
                subtitle="统计不同项目产生的金牌数量，占比越高说明该项目金牌产出更多",
            ),
            legend_opts=opts.LegendOpts(type_="scroll", orient="vertical", pos_left="78%", pos_top="12%"),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c} 枚 ({d}%)"),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
    )
    return pie


def medal_time_line(athlete_df):
    daily_counts = (
        athlete_df.dropna(subset=["获奖日期"])
        .groupby("获奖日期")
        .size()
        .sort_index()
    )

    line = (
        Line(init_opts=chart_init(height="620px"))
        .add_xaxis([str(day) for day in daily_counts.index])
        .add_yaxis(
            "每日奖牌产出总数",
            daily_counts.astype(int).tolist(),
            is_smooth=True,
            symbol_size=8,
            linestyle_opts=opts.LineStyleOpts(width=3),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.18),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="获奖时间与奖牌数量关系折线图",
                subtitle="按获奖日期汇总每日奖牌产出，观察赛程后期奖牌数量变化",
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)],
            xaxis_opts=opts.AxisOpts(name="日期", axislabel_opts=opts.LabelOpts(rotate=35)),
            yaxis_opts=opts.AxisOpts(name="奖牌数量"),
        )
    )
    return line


def subproject_rank_heatmap(athlete_df):
    gold_top5 = (
        athlete_df[athlete_df["获奖名次"].eq("金牌")]
        .groupby("子项目名称")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    ranks = ["金牌", "银牌", "铜牌"]
    pivot = (
        athlete_df[athlete_df["子项目名称"].isin(gold_top5)]
        .pivot_table(index="获奖名次", columns="子项目名称", values="运动员", aggfunc="count", fill_value=0)
        .reindex(index=ranks, columns=gold_top5, fill_value=0)
    )
    heat_data = []
    for x_index, subproject in enumerate(gold_top5):
        for y_index, rank in enumerate(ranks):
            heat_data.append([x_index, y_index, int(pivot.loc[rank, subproject])])

    heatmap = (
        HeatMap(init_opts=chart_init(height="620px"))
        .add_xaxis(gold_top5)
        .add_yaxis("获奖次数", ranks, heat_data, label_opts=opts.LabelOpts(is_show=True, position="inside"))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="子项目获奖名次分布热力图",
                subtitle="选取金牌数量最多的 5 个子项目，比较金银铜名次分布",
            ),
            visualmap_opts=opts.VisualMapOpts(min_=0, max_=int(pivot.max().max()), orient="horizontal", pos_left="center"),
            tooltip_opts=opts.TooltipOpts(position="top"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=20)),
            yaxis_opts=opts.AxisOpts(name="获奖名次"),
        )
    )
    return heatmap


def gold_medal_timeline(athlete_df):
    gold_df = athlete_df[athlete_df["获奖名次"].eq("金牌")].dropna(subset=["获奖日期"])
    daily_projects = (
        gold_df.groupby(["获奖日期", "项目名"])
        .size()
        .reset_index(name="金牌数")
        .sort_values(["获奖日期", "金牌数"], ascending=[True, False])
    )

    timeline = Timeline(init_opts=chart_init(height="620px"))
    for day, group in daily_projects.groupby("获奖日期"):
        top_group = group.head(10).iloc[::-1]
        bar = (
            Bar()
            .add_xaxis(top_group["项目名"].tolist())
            .add_yaxis("金牌数", top_group["金牌数"].astype(int).tolist(), color=MEDAL_COLORS["金牌"])
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True, position="right"))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{day} 金牌项目时间轴"),
                xaxis_opts=opts.AxisOpts(name="金牌数"),
                yaxis_opts=opts.AxisOpts(name="项目"),
            )
        )
        timeline.add(bar, str(day))

    timeline.add_schema(
        play_interval=1200,
        is_auto_play=False,
        is_loop_play=False,
        pos_bottom="2%",
        label_opts=opts.LabelOpts(rotate=35),
    )
    return timeline


def country_project_sankey(athlete_df):
    gold_df = athlete_df[athlete_df["获奖名次"].eq("金牌")]
    top_countries = gold_df.groupby("国家").size().sort_values(ascending=False).head(8).index.tolist()
    top_projects = gold_df.groupby("项目名").size().sort_values(ascending=False).head(8).index.tolist()
    flow_df = (
        gold_df[gold_df["国家"].isin(top_countries) & gold_df["项目名"].isin(top_projects)]
        .groupby(["国家", "项目名"])
        .size()
        .reset_index(name="value")
    )
    nodes = [{"name": name} for name in top_countries + top_projects]
    links = [
        {"source": row["国家"], "target": row["项目名"], "value": int(row["value"])}
        for _, row in flow_df.iterrows()
    ]

    sankey = (
        Sankey(init_opts=chart_init(height="680px"))
        .add(
            "金牌流向",
            nodes,
            links,
            linestyle_opt=opts.LineStyleOpts(opacity=0.35, curve=0.5, color="source"),
            label_opts=opts.LabelOpts(position="right"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="金牌国家与项目关联桑基图",
                subtitle="展示主要国家的金牌集中在哪些项目上",
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )
    return sankey


def write_summary(athlete_df, medal_df):
    top_country = medal_df.sort_values("奖牌总数", ascending=False).iloc[0]
    gold_projects = athlete_df[athlete_df["获奖名次"].eq("金牌")].groupby("项目名").size().sort_values(ascending=False)
    daily_counts = athlete_df.dropna(subset=["获奖日期"]).groupby("获奖日期").size().sort_index()
    gold_top5 = (
        athlete_df[athlete_df["获奖名次"].eq("金牌")]
        .groupby("子项目名称")
        .size()
        .sort_values(ascending=False)
        .head(5)
    )

    summary = f"""# 东京奥运会奖牌数据可视化实验说明

## 数据来源

- `data/奖牌榜单数据集.xlsx`：共 {len(medal_df)} 个国家或地区的奖牌榜数据。
- `data/参赛运动员数据集.xlsx`：共 {len(athlete_df)} 条运动员获奖记录，包含国家、项目、子项目、获奖时间和获奖名次。

## 图表与结论

1. **各国奖牌总数 Top 10 柱状图**：美国以 {int(top_country['奖牌总数'])} 枚奖牌排在第一，其中金牌 {int(top_country['金牌'])} 枚、银牌 {int(top_country['银牌'])} 枚、铜牌 {int(top_country['铜牌'])} 枚；中国、日本、英国等国家也位于第一梯队。
2. **各项目金牌分布饼图**：金牌产出最多的项目是 `{gold_projects.index[0]}`，共有 {int(gold_projects.iloc[0])} 枚金牌，说明该项目小项多、奖牌密集。
3. **获奖时间与奖牌数量折线图**：每日奖牌数在 {daily_counts.idxmax()} 达到峰值，共产生 {int(daily_counts.max())} 条获奖记录，体现出赛程后期多个项目集中决赛的特点。
4. **子项目获奖名次分布热力图**：金牌最多的 5 个子项目为 {", ".join(gold_top5.index.tolist())}，热力图可以看出这些子项目中不同名次的竞争强度。
5. **运动员获奖金牌时间轴**：按日期展示每天金牌主要来自哪些项目，便于观察不同赛程阶段的项目变化。
6. **桑基图**：补充展示主要国家和主要项目之间的金牌关联，可以看出优势国家的奖牌来源项目更集中。

## 运行方法

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python olympic_medal_story/olympic_medal_story.py
```

运行后图表会保存到 `olympic_medal_story/output/charts/`，汇总页面为 `olympic_medal_story/output/charts/东京奥运会奖牌数据可视化总览.html`。
"""
    (OUTPUT_DIR / "实验说明.md").write_text(summary, encoding="utf-8")


def main():
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    athlete_df, medal_df = load_data()

    charts = {
        "图1_各国奖牌总数Top10柱状图.html": medal_top10_bar(medal_df),
        "图2_各项目金牌分布饼图.html": project_gold_pie(athlete_df),
        "图3_获奖时间与奖牌数量关系折线图.html": medal_time_line(athlete_df),
        "图4_子项目获奖名次分布热力图.html": subproject_rank_heatmap(athlete_df),
        "图5_运动员获奖金牌时间轴.html": gold_medal_timeline(athlete_df),
        "图6_金牌国家与项目关联桑基图.html": country_project_sankey(athlete_df),
    }

    page = Page(page_title="东京奥运会奖牌数据可视化总览", layout=Page.SimplePageLayout)
    for filename, chart in charts.items():
        chart.render(str(CHART_DIR / filename))
        page.add(chart)

    page.render(str(CHART_DIR / "东京奥运会奖牌数据可视化总览.html"))
    write_summary(athlete_df, medal_df)

    print("图表已生成：")
    for filename in charts:
        print(f"- {CHART_DIR / filename}")
    print(f"- {CHART_DIR / '东京奥运会奖牌数据可视化总览.html'}")
    print(f"说明文档：{OUTPUT_DIR / '实验说明.md'}")


if __name__ == "__main__":
    main()

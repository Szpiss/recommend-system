from pathlib import Path

import pandas as pd
from pyecharts.charts import Bar, HeatMap, Line, Page, Pie


base_dir = Path.cwd()
data_file = None

for folder in [
    base_dir,
    base_dir / "data",
    base_dir / "uploads",
    base_dir / "olympic_medal_story" / "data",
]:
    if folder.exists():
        for file_path in folder.glob("*.xlsx"):
            try:
                columns = set(pd.read_excel(file_path, nrows=1).columns)
            except Exception:
                continue
            need = {"国家", "获奖时间", "项目名", "子项目名称", "运动员", "获奖名次"}
            if need.issubset(columns):
                data_file = file_path
                break
    if data_file is not None:
        break

if data_file is None:
    raise FileNotFoundError("没有找到参赛运动员数据集.xlsx，请把数据集上传到当前目录、data目录或uploads目录。")

output_dir = base_dir / "output" / "charts"
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(data_file)
df["获奖时间"] = pd.to_datetime(df["获奖时间"], errors="coerce")
df["获奖日期"] = df["获奖时间"].dt.date


# 图1：各国奖牌总数 Top10 柱状图
medal_table = df.pivot_table(
    index="国家",
    columns="获奖名次",
    values="运动员",
    aggfunc="count",
    fill_value=0,
)

for col in ["金牌", "银牌", "铜牌"]:
    if col not in medal_table.columns:
        medal_table[col] = 0

medal_table = medal_table[["金牌", "银牌", "铜牌"]]
medal_table["奖牌总数"] = medal_table["金牌"] + medal_table["银牌"] + medal_table["铜牌"]
top10 = medal_table.sort_values("奖牌总数", ascending=False).head(10).iloc[::-1]

bar = Bar()
bar.add_xaxis(top10.index.tolist())
bar.add_yaxis("金牌", top10["金牌"].astype(int).tolist(), stack="奖牌")
bar.add_yaxis("银牌", top10["银牌"].astype(int).tolist(), stack="奖牌")
bar.add_yaxis("铜牌", top10["铜牌"].astype(int).tolist(), stack="奖牌")
bar.reversal_axis()
bar.render(str(output_dir / "图1_各国奖牌总数Top10柱状图.html"))


# 图2：各项目金牌分布饼图
gold_df = df[df["获奖名次"] == "金牌"]
project_counts = gold_df.groupby("项目名").size().sort_values(ascending=False)
pie_data = list(zip(project_counts.head(12).index.tolist(), project_counts.head(12).astype(int).tolist()))
other_count = int(project_counts.iloc[12:].sum())
if other_count > 0:
    pie_data.append(("其他项目", other_count))

pie = Pie()
pie.add("金牌数量", pie_data)
pie.render(str(output_dir / "图2_各项目金牌分布饼图.html"))


# 图3：获奖时间与奖牌数量关系折线图
daily_counts = df.dropna(subset=["获奖日期"]).groupby("获奖日期").size().sort_index()
line = Line()
line.add_xaxis([str(day) for day in daily_counts.index])
line.add_yaxis("每日奖牌产出总数", daily_counts.astype(int).tolist())
line.render(str(output_dir / "图3_获奖时间与奖牌数量关系折线图.html"))


# 图4：子项目获奖名次分布热力图
top_sub = gold_df.groupby("子项目名称").size().sort_values(ascending=False).head(5).index.tolist()
ranks = ["金牌", "银牌", "铜牌"]
rank_table = df[df["子项目名称"].isin(top_sub)].pivot_table(
    index="获奖名次",
    columns="子项目名称",
    values="运动员",
    aggfunc="count",
    fill_value=0,
)
rank_table = rank_table.reindex(index=ranks, columns=top_sub, fill_value=0)

heat_data = []
for x, sub_name in enumerate(top_sub):
    for y, rank_name in enumerate(ranks):
        heat_data.append([x, y, int(rank_table.loc[rank_name, sub_name])])

heatmap = HeatMap()
heatmap.add_xaxis(top_sub)
heatmap.add_yaxis("获奖次数", ranks, heat_data)
heatmap.render(str(output_dir / "图4_子项目获奖名次分布热力图.html"))


# 汇总页面
page = Page()
page.add(bar, pie, line, heatmap)
page.render(str(output_dir / "东京奥运会奖牌数据可视化总览.html"))

print("完成：已生成4张图和1个汇总页面")
print(output_dir / "东京奥运会奖牌数据可视化总览.html")

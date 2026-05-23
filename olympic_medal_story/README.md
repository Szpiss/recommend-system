# 东京奥运会奖牌数据可视化实验

本目录用于完成“Data Storyteller（叙事）”阶段的数据可视化实验。实验基于两份 Excel 数据：

- `data/奖牌榜单数据集.xlsx`
- `data/参赛运动员数据集.xlsx`

## 实验内容

脚本会生成 6 个可交互 HTML 图表：

1. 各国奖牌总数 Top 10 柱状图
2. 各项目金牌分布饼图
3. 获奖时间与奖牌数量关系折线图
4. 子项目获奖名次分布热力图
5. 运动员获奖金牌时间轴
6. 金牌国家与项目关联桑基图

## 运行方法

在仓库根目录运行：

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python olympic_medal_story/olympic_medal_story.py
```

生成结果位于：

- `output/charts/东京奥运会奖牌数据可视化总览.html`
- `output/charts/图1_各国奖牌总数Top10柱状图.html`
- `output/charts/图2_各项目金牌分布饼图.html`
- `output/charts/图3_获奖时间与奖牌数量关系折线图.html`
- `output/charts/图4_子项目获奖名次分布热力图.html`
- `output/charts/图5_运动员获奖金牌时间轴.html`
- `output/charts/图6_金牌国家与项目关联桑基图.html`
- `output/实验说明.md`

## 简要结论

奖牌榜 Top10 可以看出美国、中国、日本等国家整体奖牌实力较强；项目金牌分布说明奖牌更容易集中在小项数量较多的项目；日期折线图显示奖牌产出随赛程推进有明显波动；热力图和桑基图可以进一步观察子项目竞争情况以及国家优势项目。

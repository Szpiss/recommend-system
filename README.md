# recommend-system

这个仓库用于保存基于用户邻域的 Top-N 推荐系统实验作业。

## 文件结构

- `实验代码.py`：推荐系统实验主程序
- `实验报告.md`：实验报告
- `作业说明.md`：作业说明与数据集文件解释
- `数据集/u.data`：MovieLens 100K 评分数据
- `数据集/u.item`：MovieLens 100K 电影信息数据

## 运行方式

```bash
python3 实验代码.py
```

如果需要调整参数，可以执行：

```bash
python3 实验代码.py --topk 30 --topn 10 --sample-user 10
```

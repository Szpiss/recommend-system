from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"


def load_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    users = pd.read_csv(data_dir / "BX-Users.csv", sep=";", encoding="latin-1")
    books = pd.read_csv(
        data_dir / "BX-Books.csv",
        sep=";",
        encoding="latin-1",
        on_bad_lines="skip",
        low_memory=False,
    )
    ratings = pd.read_csv(data_dir / "BX-Book-Ratings.csv", sep=";", encoding="latin-1")

    users.columns = [col.strip('"') for col in users.columns]
    books.columns = [col.strip('"') for col in books.columns]
    ratings.columns = [col.strip('"') for col in ratings.columns]
    return users, books, ratings


def clean_data(
    users: pd.DataFrame,
    books: pd.DataFrame,
    ratings: pd.DataFrame,
    min_user_ratings: int,
    min_book_ratings: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    users = users.copy()
    books = books.copy()
    ratings = ratings.copy()

    books["Book-Title"] = books["Book-Title"].astype(str).str.replace("&amp;", "&", regex=False)
    books["Book-Author"] = books["Book-Author"].fillna("未知作者")
    users["Age"] = pd.to_numeric(users["Age"], errors="coerce")
    users.loc[~users["Age"].between(5, 90), "Age"] = pd.NA

    ratings = ratings[ratings["Book-Rating"] > 0].copy()
    ratings = ratings.drop_duplicates(subset=["User-ID", "ISBN"], keep="last")
    raw_explicit_ratings = int(len(ratings))

    user_counts = ratings["User-ID"].value_counts()
    book_counts = ratings["ISBN"].value_counts()

    ratings = ratings[ratings["User-ID"].isin(user_counts[user_counts >= min_user_ratings].index)]
    ratings = ratings[ratings["ISBN"].isin(book_counts[book_counts >= min_book_ratings].index)]

    books = books.drop_duplicates(subset=["ISBN"], keep="first")
    users = users.drop_duplicates(subset=["User-ID"], keep="first")

    stats = {
        "raw_users": int(users["User-ID"].nunique()),
        "raw_books": int(books["ISBN"].nunique()),
        "raw_explicit_ratings": raw_explicit_ratings,
        "filtered_users": int(ratings["User-ID"].nunique()),
        "filtered_books": int(ratings["ISBN"].nunique()),
        "filtered_ratings": int(len(ratings)),
    }
    return users, books, ratings, stats


def get_book_stats(ratings: pd.DataFrame) -> pd.DataFrame:
    stats = ratings.groupby("ISBN")["Book-Rating"].agg(["count", "mean"]).reset_index()
    stats.columns = ["ISBN", "rating_count", "avg_rating"]
    return stats


def get_popular_books(
    ratings: pd.DataFrame,
    books: pd.DataFrame,
    top_n: int,
    min_count: int = 30,
) -> pd.DataFrame:
    popular = get_book_stats(ratings)
    popular = popular[popular["rating_count"] >= min_count]
    popular = popular.merge(books[["ISBN", "Book-Title", "Book-Author"]], on="ISBN", how="left")
    popular = popular.sort_values(["avg_rating", "rating_count"], ascending=[False, False])
    popular = popular.drop_duplicates(subset=["Book-Title"], keep="first")
    return popular.head(top_n).reset_index(drop=True)


def centered_cosine_similarity(group: pd.DataFrame) -> float:
    left = group["Book-Rating"].to_numpy(dtype=float)
    right = group["target_rating"].to_numpy(dtype=float)
    left = left - left.mean()
    right = right - right.mean()

    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    if denominator == 0:
        return 0.0
    return float(np.dot(left, right) / denominator)


def recommend_for_user(
    user_id: int,
    ratings: pd.DataFrame,
    books: pd.DataFrame,
    top_n: int,
    top_k_neighbors: int,
    min_overlap: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target = ratings[ratings["User-ID"] == user_id][["ISBN", "Book-Rating"]].copy()
    target = target.rename(columns={"Book-Rating": "target_rating"})
    if target.empty:
        return pd.DataFrame(), pd.DataFrame()

    seen_books = set(target["ISBN"])
    user_mean = ratings.groupby("User-ID")["Book-Rating"].mean()
    merged = ratings.merge(target, on="ISBN", how="inner")
    merged = merged[merged["User-ID"] != user_id]

    neighbor_rows: list[dict[str, float | int]] = []
    for neighbor_id, group in merged.groupby("User-ID"):
        if len(group) < min_overlap:
            continue
        similarity = centered_cosine_similarity(group)
        if similarity <= 0.1:
            continue
        neighbor_rows.append(
            {
                "User-ID": int(neighbor_id),
                "similarity": similarity,
                "overlap_count": int(len(group)),
                "neighbor_mean": float(user_mean.loc[neighbor_id]),
            }
        )

    if not neighbor_rows:
        return pd.DataFrame(), pd.DataFrame()

    neighbors = pd.DataFrame(neighbor_rows)
    neighbors = neighbors.sort_values(["similarity", "overlap_count"], ascending=[False, False])
    neighbors = neighbors.head(top_k_neighbors).reset_index(drop=True)

    target_mean = float(target["target_rating"].mean())
    candidate_rows = ratings[ratings["User-ID"].isin(neighbors["User-ID"])].copy()
    candidate_rows = candidate_rows.merge(
        neighbors[["User-ID", "similarity", "neighbor_mean"]],
        on="User-ID",
        how="left",
    )
    candidate_rows = candidate_rows[~candidate_rows["ISBN"].isin(seen_books)]
    if candidate_rows.empty:
        return neighbors, pd.DataFrame()

    candidate_rows["deviation"] = candidate_rows["Book-Rating"] - candidate_rows["neighbor_mean"]
    candidate_rows["weighted_dev"] = candidate_rows["similarity"] * candidate_rows["deviation"]

    scored = (
        candidate_rows.groupby("ISBN")
        .agg(
            weighted_dev=("weighted_dev", "sum"),
            similarity_sum=("similarity", "sum"),
            neighbor_count=("User-ID", "nunique"),
        )
        .reset_index()
    )
    scored = scored[scored["neighbor_count"] >= 2]
    if scored.empty:
        return neighbors, pd.DataFrame()

    scored["predicted_rating"] = target_mean + scored["weighted_dev"] / scored["similarity_sum"]
    scored["predicted_rating"] = scored["predicted_rating"].clip(1, 10)

    scored = scored.merge(get_book_stats(ratings), on="ISBN", how="left")
    scored = scored.merge(books[["ISBN", "Book-Title", "Book-Author"]], on="ISBN", how="left")
    scored = scored.sort_values(
        ["predicted_rating", "neighbor_count", "rating_count"],
        ascending=[False, False, False],
    )
    scored = scored.drop_duplicates(subset=["Book-Title"], keep="first")
    scored = scored.head(top_n).reset_index(drop=True)
    return neighbors, scored


def choose_demo_user(
    ratings: pd.DataFrame,
    books: pd.DataFrame,
    top_n: int,
    top_k_neighbors: int,
    min_overlap: int,
) -> int:
    user_counts = ratings["User-ID"].value_counts()
    for user_id in user_counts.index[:80]:
        _, recommendations = recommend_for_user(
            int(user_id),
            ratings,
            books,
            top_n=top_n,
            top_k_neighbors=top_k_neighbors,
            min_overlap=min_overlap,
        )
        if len(recommendations) >= min(5, top_n):
            return int(user_id)
    return int(user_counts.index[0])


def format_recommendations(df: pd.DataFrame, score_column: str) -> list[str]:
    lines: list[str] = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        score = float(row[score_column])
        lines.append(
            f"{idx}. {row['Book-Title']} | 作者: {row['Book-Author']} | "
            f"分数: {score:.2f} | 评分人数: {int(row['rating_count'])}"
        )
    return lines


def save_output(
    output_path: Path,
    demo_user: int,
    personalized: pd.DataFrame,
    popular: pd.DataFrame,
    stats: dict[str, int],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "图书推荐系统运行结果",
        "",
        "一、数据清洗后规模",
        f"用户数: {stats['filtered_users']}",
        f"图书数: {stats['filtered_books']}",
        f"评分数: {stats['filtered_ratings']}",
        "",
        f"二、默认演示用户: {demo_user}",
        "",
        "三、个性化推荐结果",
    ]

    if personalized.empty:
        lines.append("当前没有生成个性化推荐结果。")
    else:
        lines.extend(format_recommendations(personalized, "predicted_rating"))

    lines.extend(["", "四、热门图书推荐"])
    lines.extend(format_recommendations(popular, "avg_rating"))
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(
    demo_user: int,
    personalized: pd.DataFrame,
    popular: pd.DataFrame,
    stats: dict[str, int],
    output_path: Path,
) -> None:
    print("========== 图书推荐系统实验 ==========")
    print(f"原始用户数: {stats['raw_users']}")
    print(f"原始图书数: {stats['raw_books']}")
    print(f"原始显式评分数: {stats['raw_explicit_ratings']}")
    print(f"清洗后用户数: {stats['filtered_users']}")
    print(f"清洗后图书数: {stats['filtered_books']}")
    print(f"清洗后评分数: {stats['filtered_ratings']}")
    print(f"默认演示用户: {demo_user}")

    print("\n【个性化推荐】")
    if personalized.empty:
        print("没有生成个性化推荐，建议换一个用户，或者直接看热门推荐。")
    else:
        for line in format_recommendations(personalized, "predicted_rating"):
            print(line)

    print("\n【热门图书推荐】")
    for line in format_recommendations(popular, "avg_rating"):
        print(line)

    print(f"\n结果已保存到: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="简单图书推荐系统")
    parser.add_argument("--user-id", type=int, default=None, help="指定推荐用户")
    parser.add_argument("--topn", type=int, default=10, help="推荐结果数量")
    parser.add_argument("--topk-neighbors", type=int, default=20, help="相似用户数量")
    parser.add_argument("--min-user-ratings", type=int, default=10, help="用户最少评分次数")
    parser.add_argument("--min-book-ratings", type=int, default=20, help="图书最少评分次数")
    parser.add_argument("--min-overlap", type=int, default=5, help="相似用户最少共同评分数")
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_DIR / "demo_result.txt"),
        help="结果输出文件",
    )
    args = parser.parse_args()

    users, books, ratings = load_data(DATA_DIR)
    users, books, ratings, stats = clean_data(
        users,
        books,
        ratings,
        min_user_ratings=args.min_user_ratings,
        min_book_ratings=args.min_book_ratings,
    )

    demo_user = args.user_id
    if demo_user is None:
        demo_user = choose_demo_user(
            ratings,
            books,
            top_n=args.topn,
            top_k_neighbors=args.topk_neighbors,
            min_overlap=args.min_overlap,
        )

    _, personalized = recommend_for_user(
        demo_user,
        ratings,
        books,
        top_n=args.topn,
        top_k_neighbors=args.topk_neighbors,
        min_overlap=args.min_overlap,
    )
    popular = get_popular_books(ratings, books, top_n=args.topn)
    output_path = Path(args.output)

    print_summary(demo_user, personalized, popular, stats, output_path)
    save_output(output_path, demo_user, personalized, popular, stats)


if __name__ == "__main__":
    main()

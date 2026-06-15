import os
import pickle
import warnings
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import normalize
except ImportError:
    HashingVectorizer = None
    NearestNeighbors = None
    normalize = None

warnings.filterwarnings('ignore')


class RecommendationSystem:
    MODEL_DIR = 'models'
    EMBEDDINGS_FILE = os.path.join(MODEL_DIR, 'item_embeddings.npy')
    FAISS_INDEX_FILE = os.path.join(MODEL_DIR, 'faiss_index.bin')
    SIMILARITY_FILE = os.path.join(MODEL_DIR, 'similarity_matrix.pkl')
    ITEMS_DF_FILE = os.path.join(MODEL_DIR, 'items_df.pkl')
    UNIQUE_ITEMS_DF_FILE = os.path.join(MODEL_DIR, 'unique_items_df.pkl')
    ITEM_MAPPING_FILE = os.path.join(MODEL_DIR, 'item_mapping.pkl')
    USER_INDEX_FILE = os.path.join(MODEL_DIR, 'user_history_index.pkl')
    TRAIN_USERS_FILE = os.path.join(MODEL_DIR, 'train_users.pkl')
    TEST_USERS_FILE = os.path.join(MODEL_DIR, 'test_users.pkl')
    NEIGHBORS_FILE = os.path.join(MODEL_DIR, 'neighbors_model.pkl')

    def __init__(self, data_path: str, force_retrain: bool = False):
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        self.max_rows = int(os.environ.get('RS_MAX_ROWS', '50000'))
        self.embedding_model_name = os.environ.get(
            'RS_EMBEDDING_MODEL',
            'paraphrase-multilingual-MiniLM-L12-v2'
        )
        self.embedding_batch_size = int(os.environ.get('RS_EMBEDDING_BATCH_SIZE', '64'))
        self.similarity_top_k = int(os.environ.get('RS_SIMILARITY_TOP_K', '30'))
        self.neighbor_model: Optional[NearestNeighbors] = None

        if self._check_model_exists() and not force_retrain:
            print("检测到已训练模型，正在加载...")
            self._load_model()
            print("✓ 模型加载完成")
        else:
            if force_retrain:
                print("强制重新训练模式")
            else:
                print("未检测到已训练模型，开始训练...")

            print("正在加载数据...")
            self.items_df = self._load_and_clean_data(data_path)
            print(f"✓ 数据加载完成: {len(self.items_df)} 条记录")

            print("正在划分训练集与测试集...")
            self.train_users, self.test_users = self._split_train_test()
            print(f"✓ 训练集: {len(self.train_users)} 个用户")
            print(f"✓ 测试集: {len(self.test_users)} 个用户")

            print("正在构建唯一商品池...")
            self.unique_items_df, self.item_mapping = self._create_unique_items()
            print(f"✓ 唯一商品池: {len(self.unique_items_df)} 个商品")

            self.num_items = len(self.unique_items_df)

            print("正在构建用户历史索引...")
            self.user_history_index = self._build_user_history_index()
            print(f"✓ 用户历史索引: {len(self.user_history_index)} 个用户")

            print("正在生成商品嵌入...")
            self.item_embeddings = self._generate_embeddings()

            print("正在构建Faiss索引...")
            self.faiss_index = self._build_faiss_index()

            print("正在构建相似度矩阵...")
            self.similarity_matrix = self._build_similarity_matrix()

            print("正在保存模型...")
            self._save_model()
            print("✓ 模型保存完成")

        print("✓ 推荐系统初始化完成")

    def _check_model_exists(self) -> bool:
        required_files = [
            self.EMBEDDINGS_FILE,
            self.SIMILARITY_FILE, self.ITEMS_DF_FILE,
            self.UNIQUE_ITEMS_DF_FILE, self.ITEM_MAPPING_FILE,
            self.USER_INDEX_FILE, self.TRAIN_USERS_FILE, self.TEST_USERS_FILE
        ]
        if not all(os.path.exists(f) for f in required_files):
            return False
        return os.path.exists(self.FAISS_INDEX_FILE) or os.path.exists(self.NEIGHBORS_FILE)

    def _save_model(self):
        np.save(self.EMBEDDINGS_FILE, self.item_embeddings)
        if faiss is not None and self.faiss_index is not None:
            faiss.write_index(self.faiss_index, self.FAISS_INDEX_FILE)
        elif self.neighbor_model is not None:
            with open(self.NEIGHBORS_FILE, 'wb') as f:
                pickle.dump(self.neighbor_model, f)

        with open(self.SIMILARITY_FILE, 'wb') as f:
            pickle.dump(self.similarity_matrix, f)
        with open(self.ITEMS_DF_FILE, 'wb') as f:
            pickle.dump(self.items_df, f)
        with open(self.UNIQUE_ITEMS_DF_FILE, 'wb') as f:
            pickle.dump(self.unique_items_df, f)
        with open(self.ITEM_MAPPING_FILE, 'wb') as f:
            pickle.dump(self.item_mapping, f)
        with open(self.USER_INDEX_FILE, 'wb') as f:
            pickle.dump(self.user_history_index, f)
        with open(self.TRAIN_USERS_FILE, 'wb') as f:
            pickle.dump(self.train_users, f)
        with open(self.TEST_USERS_FILE, 'wb') as f:
            pickle.dump(self.test_users, f)

    def _load_model(self):
        self.item_embeddings = np.load(self.EMBEDDINGS_FILE)
        self.faiss_index = None
        self.neighbor_model = None

        if faiss is not None and os.path.exists(self.FAISS_INDEX_FILE):
            self.faiss_index = faiss.read_index(self.FAISS_INDEX_FILE)
        elif os.path.exists(self.NEIGHBORS_FILE):
            with open(self.NEIGHBORS_FILE, 'rb') as f:
                self.neighbor_model = pickle.load(f)
        else:
            self.faiss_index = self._build_faiss_index()

        with open(self.SIMILARITY_FILE, 'rb') as f:
            self.similarity_matrix = pickle.load(f)
        with open(self.ITEMS_DF_FILE, 'rb') as f:
            self.items_df = pickle.load(f)
        with open(self.UNIQUE_ITEMS_DF_FILE, 'rb') as f:
            self.unique_items_df = pickle.load(f)
        with open(self.ITEM_MAPPING_FILE, 'rb') as f:
            self.item_mapping = pickle.load(f)
        with open(self.USER_INDEX_FILE, 'rb') as f:
            self.user_history_index = pickle.load(f)
        with open(self.TRAIN_USERS_FILE, 'rb') as f:
            self.train_users = pickle.load(f)
        with open(self.TEST_USERS_FILE, 'rb') as f:
            self.test_users = pickle.load(f)

        self.num_items = len(self.unique_items_df)

    def _load_and_clean_data(self, data_path: str) -> pd.DataFrame:
        usecols = [
            'userName', 'verified', 'itemName', 'description', 'image', 'brand',
            'feature', 'category', 'price', 'rating', 'reviewTime', 'summary',
            'reviewText', 'vote'
        ]
        read_kwargs = {'usecols': usecols, 'encoding': 'utf-8', 'on_bad_lines': 'skip'}
        if self.max_rows > 0:
            read_kwargs['nrows'] = self.max_rows

        df = pd.read_csv(data_path, **read_kwargs)
        df = df.drop_duplicates().reset_index(drop=True)

        text_defaults = {
            'userName': 'unknown_user',
            'itemName': 'Unknown Item',
            'brand': 'Unknown Brand',
            'category': 'Unknown',
            'feature': '[]',
            'description': '[]',
            'image': '[]',
            'summary': '',
            'reviewText': ''
        }
        for col, default in text_defaults.items():
            df[col] = df[col].fillna(default).astype(str).str.strip()
            df.loc[df[col] == '', col] = default

        df['price'] = (
            df['price'].fillna('0')
            .astype(str)
            .str.replace(r'[^0-9.]', '', regex=True)
            .replace('', '0')
        )
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0.0)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0.0).clip(1, 5)
        df['verified'] = df['verified'].astype(str).str.lower().isin(['true', '1', 'yes'])
        df['vote'] = pd.to_numeric(df['vote'], errors='coerce').fillna(0).astype(int)
        df['reviewTime'] = pd.to_datetime(df['reviewTime'], errors='coerce')
        df['reviewTime'] = df['reviewTime'].fillna(pd.Timestamp('1970-01-01'))

        df = df[(df['itemName'] != 'Unknown Item') & (df['userName'] != 'unknown_user')]
        df = df.reset_index(drop=True)
        df.insert(0, 'itemId', df.index.astype(int))
        return df

    def _split_train_test(self, test_ratio: float = 0.2) -> Tuple[List[str], List[str]]:
        users = self.items_df['userName'].dropna().unique().tolist()
        rng = np.random.default_rng(42)
        rng.shuffle(users)

        test_size = max(1, int(len(users) * test_ratio)) if len(users) > 1 else 0
        test_users = users[:test_size]
        train_users = users[test_size:]
        return train_users, test_users

    def _create_unique_items(self) -> Tuple[pd.DataFrame, Dict[int, int]]:
        working = self.items_df.copy()
        working['item_key'] = (
            working['itemName'].str.lower().str.strip() + '|' +
            working['brand'].str.lower().str.strip()
        )
        representative = (
            working.sort_values(['rating', 'reviewTime'], ascending=[False, False])
            .drop_duplicates('item_key', keep='first')
            .copy()
            .reset_index(drop=True)
        )
        representative.insert(0, 'uniqueItemId', representative.index.astype(int))

        key_to_unique = dict(zip(representative['item_key'], representative['uniqueItemId']))
        item_mapping = {
            int(row.itemId): int(key_to_unique[row.item_key])
            for row in working[['itemId', 'item_key']].itertuples(index=False)
        }

        unique_df = representative.drop(columns=['item_key'])
        self.items_df['uniqueItemId'] = self.items_df['itemId'].map(item_mapping).astype(int)
        return unique_df, item_mapping

    def _build_user_history_index(self) -> Dict[str, List[Dict]]:
        user_history = defaultdict(list)

        for row in self.items_df.sort_values('reviewTime').itertuples(index=False):
            user_history[row.userName].append({
                'timestamp': row.reviewTime.isoformat(),
                'action': 'click',
                'item_id': int(row.itemId),
                'unique_item_id': int(row.uniqueItemId),
                'rating': float(row.rating),
                'price': float(row.price),
                'category': row.category
            })

        user_history = dict(user_history)
        return user_history

    def _generate_embeddings(self) -> np.ndarray:
        texts = (
            self.unique_items_df['itemName'].fillna('') + ' ' +
            self.unique_items_df['brand'].fillna('') + ' ' +
            self.unique_items_df['category'].fillna('') + ' ' +
            self.unique_items_df['feature'].fillna('')
        ).tolist()

        if not texts:
            return np.zeros((0, 384), dtype='float32')

        if SentenceTransformer is not None and os.environ.get('RS_USE_SENTENCE_TRANSFORMER', '1') == '1':
            model = SentenceTransformer(self.embedding_model_name)
            embeddings = model.encode(
                texts,
                batch_size=self.embedding_batch_size,
                show_progress_bar=True,
                normalize_embeddings=True
            )
            return np.asarray(embeddings, dtype='float32')

        if HashingVectorizer is not None and normalize is not None:
            vectorizer = HashingVectorizer(
                n_features=384,
                alternate_sign=False,
                norm=None,
                ngram_range=(1, 2)
            )
            embeddings = vectorizer.transform(texts).astype('float32')
            embeddings = normalize(embeddings, norm='l2', copy=False)
            return embeddings.toarray().astype('float32')

        rng = np.random.default_rng(42)
        embeddings = rng.normal(size=(len(texts), 384)).astype('float32')
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.maximum(norms, 1e-8)

    def _build_faiss_index(self):
        dimension = self.item_embeddings.shape[1] if len(self.item_embeddings) > 0 else 384
        if faiss is not None:
            index = faiss.IndexFlatIP(dimension)
            if len(self.item_embeddings) > 0:
                index.add(self.item_embeddings.astype('float32'))
            return index

        if NearestNeighbors is None:
            return None

        self.neighbor_model = NearestNeighbors(metric='cosine', algorithm='brute')
        if len(self.item_embeddings) > 0:
            self.neighbor_model.fit(self.item_embeddings)
        index = None
        return index

    def _build_similarity_matrix(self) -> Dict[int, List[tuple]]:
        similarity_dict = {}
        if self.num_items == 0:
            return similarity_dict

        k = min(self.similarity_top_k + 1, self.num_items)
        if faiss is not None and self.faiss_index is not None:
            scores, indices = self.faiss_index.search(self.item_embeddings.astype('float32'), k)
            for item_id, (item_scores, item_indices) in enumerate(zip(scores, indices)):
                similar_items = []
                for score, candidate_id in zip(item_scores, item_indices):
                    candidate_id = int(candidate_id)
                    if candidate_id == item_id or candidate_id < 0:
                        continue
                    similar_items.append((candidate_id, float(max(score, 0.0))))
                similarity_dict[item_id] = similar_items
            return similarity_dict

        if self.neighbor_model is not None:
            distances, indices = self.neighbor_model.kneighbors(self.item_embeddings, n_neighbors=k)
            for item_id, (item_distances, item_indices) in enumerate(zip(distances, indices)):
                similar_items = []
                for distance, candidate_id in zip(item_distances, item_indices):
                    candidate_id = int(candidate_id)
                    if candidate_id == item_id:
                        continue
                    similar_items.append((candidate_id, float(max(1.0 - distance, 0.0))))
                similarity_dict[item_id] = similar_items
        return similarity_dict

    def recommend(self, user_id: str, n: int = 300,
                   user_history: List[Dict] = None) -> List[Dict]:
        user_history = user_history or self.user_history_index.get(user_id, [])
        if not user_history:
            return self._get_random_items(n)

        seen_unique_ids = set()
        candidate_scores = defaultdict(float)
        ordered_history = list(reversed(user_history[-50:]))

        for position, behavior in enumerate(ordered_history):
            unique_id = behavior.get('unique_item_id')
            if unique_id is None and behavior.get('item_id') in self.item_mapping:
                unique_id = self.item_mapping.get(int(behavior.get('item_id')))
            if unique_id is None:
                continue

            unique_id = int(unique_id)
            seen_unique_ids.add(unique_id)
            recency_weight = 1.0 / (1.0 + position * 0.12)
            rating_weight = float(behavior.get('rating', 5.0)) / 5.0
            weight = recency_weight * max(rating_weight, 0.2)

            for candidate_id, similarity in self.similarity_matrix.get(unique_id, []):
                if candidate_id in seen_unique_ids:
                    continue
                candidate_scores[candidate_id] += similarity * weight

        ranked_ids = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        recommended_items = []
        max_score = ranked_ids[0][1] if ranked_ids else 1.0

        for unique_item_id, score in ranked_ids[:n]:
            row = self.unique_items_df.iloc[int(unique_item_id)].to_dict()
            row['similarity'] = round(float(score / max(max_score, 1e-8)), 4)
            recommended_items.append(row)

        if len(recommended_items) < n:
            filler = self._get_random_items(n - len(recommended_items), exclude=list(seen_unique_ids))
            recommended_items.extend(filler)

        return recommended_items[:n]

    def _get_random_items(self, n: int, exclude: List[int] = None) -> List[Dict]:
        exclude = exclude or []
        valid_exclude = []

        for x in exclude:
            try:
                x_int = int(x)
                if 0 <= x_int < len(self.unique_items_df):
                    valid_exclude.append(x_int)
            except:
                pass

        available = self.unique_items_df[
            ~self.unique_items_df['uniqueItemId'].isin(valid_exclude)
        ]

        if len(available) == 0:
            available = self.unique_items_df

        sample_size = min(n, len(available))
        items = available.sample(n=sample_size, replace=False).to_dict('records')

        for item in items:
            item['similarity'] = 0.0

        return items

    def get_all_users(self) -> List[str]:
        return list(self.user_history_index.keys())

    def get_train_users(self) -> List[str]:
        return self.train_users

    def get_test_users(self) -> List[str]:
        return self.test_users

    def get_user_history_from_csv(self, user_name: str) -> List[Dict]:
        return self.user_history_index.get(user_name, [])

    def get_search_suggestions(self, user_id: str, n: int = 5,
                               user_history: List[Dict] = None) -> List[str]:
        if len(self.unique_items_df) > 0:
            return self.unique_items_df['category'].value_counts().head(n).index.tolist()
        return []

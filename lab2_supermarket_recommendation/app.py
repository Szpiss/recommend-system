import random
import os
import warnings
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify


warnings.filterwarnings('ignore')

# 导入推荐模块
try:
    from recommendation_module import RecommendationSystem
    MODULE_LOADED = True
except ImportError as e:
    print(f"警告: 推荐模块未加载 - {e}")
    MODULE_LOADED = False

app = Flask(__name__)


class SupermarketRecommendationApp:
    def __init__(self, data_path='amazon_reviews.csv'):
        self.data_path = data_path
        self.current_user_id = "user_001"
        self.current_user_name = None
        self.user_behaviors = {}
        self.df = None
        self.rec_system = None

        # 初始化推荐系统
        if MODULE_LOADED:
            try:
                print("正在初始化推荐系统...")
                self.rec_system = RecommendationSystem(data_path)
                self.df = self.rec_system.items_df
                print("✓ 推荐系统初始化成功")

                # 获取所有真实用户
                self.all_users = self.rec_system.get_all_users()
                print(f"✓ 加载了 {len(self.all_users)} 个真实用户")

            except FileNotFoundError:
                print(f"✗ 错误: 找不到数据文件 '{data_path}'")
                raise
            except Exception as e:
                print(f"✗ 推荐系统初始化失败: {e}")
                print(traceback.format_exc())
                raise
        else:
            print("✗ 推荐模块未加载，系统无法启动")
            raise ImportError("recommendation_module.py 加载失败")

    def get_random_items(self, n=300):
        """随机获取商品（兜底策略）"""
        if self.df is None or len(self.df) == 0:
            return []
        sample_size = min(n, len(self.df))
        items = self.df.sample(n=sample_size).to_dict('records')
        for item in items:
            item['similarity'] = 0.0
        return items

    def get_recommendations(self, user_id, n=300):
        """
        获取推荐商品

        Args:
            user_id: 用户ID
            n: 推荐数量

        Returns:
            推荐商品列表（包含相似度）
        """
        if self.rec_system is not None:
            try:
                print(f"\n[推荐请求] 用户: {user_id}, 数量: {n}")
                user_history = self.get_merged_user_history(user_id)
                print(f"  用户历史记录数: {len(user_history)}")

                recommended_items = self.rec_system.recommend(
                    user_id=user_id,
                    n=n,
                    user_history=user_history
                )

                print(f"  推荐结果数: {len(recommended_items)}")
                similarities = [item.get('similarity', 0) for item in recommended_items]
                if similarities:
                    print(f"  相似度范围: {min(similarities):.3f} - {max(similarities):.3f}")

                return recommended_items

            except Exception as e:
                print(f"❌ 推荐算法执行失败: {e}")
                print(traceback.format_exc())
                return self.get_random_items(n)
        else:
            return self.get_random_items(n)

    def get_merged_user_history(self, user_id):
        merged_history = []

        if self.current_user_name:
            csv_history = self.rec_system.get_user_history_from_csv(self.current_user_name)
            merged_history.extend(csv_history)

        session_history = self.user_behaviors.get(user_id, [])
        merged_history.extend(session_history)

        return merged_history

    def get_user_history_items(self, user_id, limit=20):
        history = self.get_merged_user_history(user_id)

        history_item_ids = []
        for h in reversed(history):
            if h.get('action') == 'click' and h.get('item_id') is not None:
                history_item_ids.append(h['item_id'])
                if len(history_item_ids) >= limit:
                    break

        if not history_item_ids:
            return []

        history_items = self.df[self.df['itemId'].isin(history_item_ids)].to_dict('records')

        item_dict = {item['itemId']: item for item in history_items}
        ordered_items = [item_dict[item_id] for item_id in history_item_ids if item_id in item_dict]

        return ordered_items

    def switch_to_random_user(self):
        if not self.all_users:
            return None, None, 0

        random_user_name = random.choice(self.all_users)
        random_user_id = f"csv_user_{hash(random_user_name) % 10000}"

        self.current_user_id = random_user_id
        self.current_user_name = random_user_name
        self.user_behaviors[random_user_id] = []
        csv_history = self.rec_system.get_user_history_from_csv(random_user_name)

        return random_user_id, random_user_name, len(csv_history)

    def record_behavior(self, user_id, action, item_id=None):
        if user_id not in self.user_behaviors:
            self.user_behaviors[user_id] = []

        behavior = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'item_id': item_id
        }

        self.user_behaviors[user_id].append(behavior)

        if len(self.user_behaviors[user_id]) > 50:
            self.user_behaviors[user_id] = self.user_behaviors[user_id][-50:]

    def get_user_profile(self, user_id):
        history = self.get_merged_user_history(user_id)

        profile = {
            'user_id': user_id,
            'user_name': self.current_user_name or 'Unknown',
            'total_behaviors': len(history),
            'recent_views': []
        }

        for h in reversed(history):
            if h.get('action') == 'click' and h.get('item_id') is not None:
                profile['recent_views'].append(h['item_id'])
                if len(profile['recent_views']) >= 10:
                    break

        return profile


try:
    app_instance = SupermarketRecommendationApp()
except Exception as e:
    print("\n" + "=" * 60)
    print("系统启动失败！")
    print("=" * 60)
    print(f"错误信息: {e}")
    print("\n请检查:")
    print("1. amazon_reviews.csv 文件是否存在")
    print("2. recommendation_module.py 文件是否正确")
    print("3. 必要的Python包是否已安装")
    print("=" * 60)
    exit(1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    user_id = request.args.get('user_id', app_instance.current_user_id)
    n = int(request.args.get('n', 300))

    items = app_instance.get_recommendations(user_id, n)

    return jsonify({
        'success': True,
        'count': len(items),
        'items': items,
        'user_id': user_id
    })


@app.route('/api/history', methods=['GET'])
def api_history():
    user_id = request.args.get('user_id', app_instance.current_user_id)
    limit = int(request.args.get('limit', 20))

    history_items = app_instance.get_user_history_items(user_id, limit)

    return jsonify({
        'success': True,
        'count': len(history_items),
        'items': history_items,
        'user_id': user_id
    })


@app.route('/api/record-behavior', methods=['POST'])
def api_record_behavior():
    data = request.json

    app_instance.record_behavior(
        user_id=data.get('user_id', app_instance.current_user_id),
        action=data.get('action'),
        item_id=data.get('item_id')
    )

    return jsonify({'success': True})


@app.route('/api/user-profile', methods=['GET'])
def api_user_profile():
    user_id = request.args.get('user_id', app_instance.current_user_id)
    profile = app_instance.get_user_profile(user_id)

    return jsonify({
        'success': True,
        'profile': profile
    })


@app.route('/api/switch-user', methods=['POST'])
def api_switch_user():
    user_id, user_name, history_count = app_instance.switch_to_random_user()

    if user_id:
        return jsonify({
            'success': True,
            'user_id': user_id,
            'user_name': user_name,
            'history_count': history_count,
            'message': f'已切换到用户: {user_name} (历史记录: {history_count}条)'
        })
    else:
        return jsonify({
            'success': False,
            'message': '没有可用的用户'
        })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    print("\n" + "=" * 60)
    print("并夕夕推荐系统启动成功！")
    print("=" * 60)
    print(f"数据集: {len(app_instance.df)} 个商品")
    print(f"用户数: {len(app_instance.all_users)} 个真实用户")
    print(f"推荐模块: 已加载 ✓")
    print("=" * 60)
    print(f"\n访问地址: http://127.0.0.1:{port}")

    app.run(debug=True, host='0.0.0.0', port=port)

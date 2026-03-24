"""スマートチャンク分割ロジックのテスト

動画の長さに応じた自動分割戦略のテスト。
ルール:
    - 15分以下（<=900秒）: 分割しない
    - 15分超〜30分以下（901〜1800秒）: 2分割
    - 30分超〜60分以下（1801〜3600秒）: 3分割
    - 60分超〜90分以下（3601〜5400秒）: 4分割
    - 90分超（5401秒〜）: 5分割
"""
import pytest
from src.video_chunker import calculate_chunk_strategy


class TestCalculateChunkStrategy:
    """calculate_chunk_strategy() のテスト"""

    def test_no_chunking_under_15min(self):
        """15分以下の動画は分割しない"""
        result = calculate_chunk_strategy(duration_seconds=600)  # 10分
        assert result["should_chunk"] is False
        assert result["num_chunks"] == 1

    def test_2_chunks_for_15_to_30min(self):
        """15分超〜30分以下の動画は2分割"""
        result = calculate_chunk_strategy(duration_seconds=1200)  # 20分
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 2

    def test_3_chunks_for_30_to_60min(self):
        """30分超〜60分以下の動画は3分割"""
        result = calculate_chunk_strategy(duration_seconds=2400)  # 40分
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 3

    def test_4_chunks_for_60_to_90min(self):
        """60分超〜90分以下の動画は4分割"""
        result = calculate_chunk_strategy(duration_seconds=4200)  # 70分
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 4

    def test_5_chunks_for_over_90min(self):
        """90分超の動画は5分割"""
        result = calculate_chunk_strategy(duration_seconds=6000)  # 100分
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 5

    def test_chunk_duration_is_balanced(self):
        """各チャンクが均等に近い長さになること"""
        # 30分（1800秒）→ 2分割 → 各900秒（15分）
        result = calculate_chunk_strategy(duration_seconds=1800)
        assert result["chunk_duration_seconds"] == 900

    def test_boundary_15min_exact(self):
        """境界値: ちょうど15分（900秒）は分割しない"""
        result = calculate_chunk_strategy(duration_seconds=900)
        assert result["should_chunk"] is False
        assert result["num_chunks"] == 1

    def test_boundary_30min_exact(self):
        """境界値: ちょうど30分（1800秒）は2分割"""
        result = calculate_chunk_strategy(duration_seconds=1800)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 2


class TestChunkDurationCalculation:
    """チャンク長の計算テスト（補助テスト）"""

    def test_chunk_duration_for_20min_video(self):
        """20分の動画: 2分割 → 各10分（600秒）"""
        result = calculate_chunk_strategy(duration_seconds=1200)
        assert result["chunk_duration_seconds"] == 600

    def test_chunk_duration_for_45min_video(self):
        """45分の動画: 3分割 → 各15分（900秒）"""
        result = calculate_chunk_strategy(duration_seconds=2700)
        assert result["chunk_duration_seconds"] == 900

    def test_chunk_duration_for_no_split(self):
        """分割なしの場合、chunk_duration_secondsは動画全体の長さ"""
        result = calculate_chunk_strategy(duration_seconds=600)
        assert result["chunk_duration_seconds"] == 600

    def test_chunk_duration_for_70min_video(self):
        """70分の動画: 4分割 → 各約17.5分（1050秒）"""
        result = calculate_chunk_strategy(duration_seconds=4200)
        assert result["chunk_duration_seconds"] == 1050

    def test_chunk_duration_for_100min_video(self):
        """100分の動画: 5分割 → 各20分（1200秒）"""
        result = calculate_chunk_strategy(duration_seconds=6000)
        assert result["chunk_duration_seconds"] == 1200

    def test_boundary_60min_exact(self):
        """境界値: ちょうど60分（3600秒）は3分割"""
        result = calculate_chunk_strategy(duration_seconds=3600)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 3

    def test_boundary_90min_exact(self):
        """境界値: ちょうど90分（5400秒）は4分割"""
        result = calculate_chunk_strategy(duration_seconds=5400)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 4


class TestBoundaryJustOver:
    """境界値「ちょうど超え」テスト（+1秒で次の分割段階に移行）"""

    def test_boundary_901_seconds(self):
        """901秒（15分+1秒）は2分割に移行"""
        result = calculate_chunk_strategy(duration_seconds=901)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 2

    def test_boundary_1801_seconds(self):
        """1801秒（30分+1秒）は3分割に移行"""
        result = calculate_chunk_strategy(duration_seconds=1801)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 3

    def test_boundary_3601_seconds(self):
        """3601秒（60分+1秒）は4分割に移行"""
        result = calculate_chunk_strategy(duration_seconds=3601)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 4

    def test_boundary_5401_seconds(self):
        """5401秒（90分+1秒）は5分割に移行"""
        result = calculate_chunk_strategy(duration_seconds=5401)
        assert result["should_chunk"] is True
        assert result["num_chunks"] == 5


class TestEdgeCases:
    """異常系・エッジケーステスト"""

    def test_zero_duration_raises_error(self):
        """0秒の動画はValueErrorを送出"""
        with pytest.raises(ValueError):
            calculate_chunk_strategy(duration_seconds=0)

    def test_negative_duration_raises_error(self):
        """負の値はValueErrorを送出"""
        with pytest.raises(ValueError):
            calculate_chunk_strategy(duration_seconds=-100)

    def test_very_short_video(self):
        """1秒の動画は分割しない"""
        result = calculate_chunk_strategy(duration_seconds=1)
        assert result["should_chunk"] is False
        assert result["num_chunks"] == 1
        assert result["chunk_duration_seconds"] == 1

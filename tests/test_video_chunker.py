"""動画チャンク化ロジックのテスト"""
import pytest
from src.video_chunker import VideoChunker, ChunkInfo, get_video_duration

# ffmpegの有無をチェック
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False


class TestVideoChunker:
    """動画を時間軸で分割する機能のテスト"""

    @pytest.fixture
    def chunker(self):
        """VideoChunkerインスタンス（デフォルト: 5分チャンク）"""
        return VideoChunker(chunk_duration_seconds=300)

    @pytest.fixture
    def mock_video_30min(self, tmp_path):
        """30分のダミー動画ファイル"""
        video_path = tmp_path / "video_30min.mp4"
        video_path.write_bytes(b"dummy 30min video")
        # メタデータとして動画長を記録（実際の動画解析はモック）
        return str(video_path), 1800  # 30分 = 1800秒

    @pytest.fixture
    def mock_video_4min(self, tmp_path):
        """4分のダミー動画ファイル（5分未満）"""
        video_path = tmp_path / "video_4min.mp4"
        video_path.write_bytes(b"dummy 4min video")
        return str(video_path), 240  # 4分 = 240秒

    def test_chunk_30min_video_into_6_chunks(self, chunker, mock_video_30min):
        """正常系: 30分動画を5分単位で6チャンクに分割"""
        video_path, duration = mock_video_30min

        # 実行（durationを渡す - 実際の実装では動画から自動取得）
        chunks = chunker.create_chunks(video_path, duration)

        # 検証
        assert len(chunks) == 6
        assert chunks[0].start_time == 0
        assert chunks[0].end_time == 300
        assert chunks[0].duration == 300
        assert chunks[5].start_time == 1500
        assert chunks[5].end_time == 1800
        assert chunks[5].duration == 300

    def test_chunk_short_video_single_chunk(self, chunker, mock_video_4min):
        """境界値: 動画長が5分未満の場合（1チャンクのみ）"""
        video_path, duration = mock_video_4min

        # 実行
        chunks = chunker.create_chunks(video_path, duration)

        # 検証
        assert len(chunks) == 1
        assert chunks[0].start_time == 0
        assert chunks[0].end_time == 240
        assert chunks[0].duration == 240

    def test_chunk_exactly_5min_video(self, chunker, tmp_path):
        """境界値: 動画長が5分ちょうど（1チャンク）"""
        video_path = tmp_path / "video_5min.mp4"
        video_path.write_bytes(b"dummy 5min video")
        duration = 300  # 5分 = 300秒

        # 実行
        chunks = chunker.create_chunks(str(video_path), duration)

        # 検証
        assert len(chunks) == 1
        assert chunks[0].start_time == 0
        assert chunks[0].end_time == 300
        assert chunks[0].duration == 300

    def test_chunk_32min_video_with_remainder(self, chunker, tmp_path):
        """境界値: 動画長が32分（6チャンク + 2分の端数）"""
        video_path = tmp_path / "video_32min.mp4"
        video_path.write_bytes(b"dummy 32min video")
        duration = 1920  # 32分 = 1920秒

        # 実行
        chunks = chunker.create_chunks(str(video_path), duration)

        # 検証: 6チャンク（5分×6） + 1チャンク（2分）= 7チャンク
        assert len(chunks) == 7
        assert chunks[6].start_time == 1800
        assert chunks[6].end_time == 1920
        assert chunks[6].duration == 120  # 端数2分

    def test_chunk_file_not_found(self, chunker):
        """異常系: 動画ファイルが存在しない"""
        nonexistent_file = "/path/to/nonexistent.mp4"

        # 実行と検証
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            chunker.create_chunks(nonexistent_file, 1800)

    def test_chunk_unsupported_format(self, chunker, tmp_path):
        """異常系: サポート外の拡張子（.avi等）"""
        # 注意: 今回の実装では.aviもサポートする予定だが、
        # テストとしては将来的にサポート外になる可能性を考慮
        # ここでは.wmvをサポート外と仮定
        unsupported_file = tmp_path / "video.wmv"
        unsupported_file.write_bytes(b"dummy")

        # 実行と検証
        with pytest.raises(ValueError, match="Unsupported video format"):
            chunker.create_chunks(str(unsupported_file), 1800)


class TestGetVideoDuration:
    """動画長取得機能のテスト"""

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg-python not installed")
    def test_get_video_duration_mock(self, mocker, tmp_path):
        """正常系: 動画の長さを取得（モック）"""
        # ダミー動画ファイル作成
        video_path = tmp_path / "test_video.mp4"
        video_path.write_bytes(b"dummy video data")

        # ffmpeg.probeをモック化
        mock_probe = mocker.patch('ffmpeg.probe')
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'video', 'duration': '1800.0'}
            ],
            'format': {'duration': '1800.5'}
        }

        # 実行
        duration = get_video_duration(str(video_path))

        # 検証
        assert duration == 1800  # 1800.5秒 → 1800秒（整数）
        mock_probe.assert_called_once_with(str(video_path))

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg-python not installed")
    def test_get_video_duration_file_not_found(self):
        """異常系: ファイルが存在しない"""
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            get_video_duration("/path/to/nonexistent.mp4")

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg-python not installed")
    def test_get_video_duration_ffmpeg_error(self, mocker, tmp_path):
        """異常系: ffprobeの実行エラー"""
        video_path = tmp_path / "broken_video.mp4"
        video_path.write_bytes(b"corrupted data")

        # ffmpeg.probeがエラーを投げるようにモック
        import ffmpeg
        mock_probe = mocker.patch('ffmpeg.probe')
        mock_probe.side_effect = ffmpeg.Error('ffprobe', '', b'Invalid data')

        # 実行と検証
        with pytest.raises(RuntimeError, match="Failed to get video duration"):
            get_video_duration(str(video_path))


class TestChunkInfo:
    """ChunkInfo データクラスのテスト"""

    def test_chunk_info_creation(self):
        """ChunkInfo インスタンス作成"""
        chunk = ChunkInfo(
            chunk_id=0,
            start_time=0,
            end_time=300,
            duration=300,
            video_path="/path/to/video.mp4"
        )

        assert chunk.chunk_id == 0
        assert chunk.start_time == 0
        assert chunk.end_time == 300
        assert chunk.duration == 300
        assert chunk.video_path == "/path/to/video.mp4"

    def test_chunk_info_repr(self):
        """ChunkInfo の文字列表現"""
        chunk = ChunkInfo(
            chunk_id=1,
            start_time=300,
            end_time=600,
            duration=300,
            video_path="/path/to/video.mp4"
        )

        repr_str = repr(chunk)
        assert "ChunkInfo" in repr_str
        assert "chunk_id=1" in repr_str

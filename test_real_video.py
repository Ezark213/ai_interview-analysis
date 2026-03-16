"""
実動画での動作確認スクリプト

Iteration-07: ローカルホスト実装と限定的PoC
このスクリプトは、実動画1件でシステムが正常に動作するかを確認します。
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Windows環境でUTF-8出力を有効化
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# .env読み込み
load_dotenv()

from src.chunked_analyzer import ChunkedVideoAnalyzer
from src.video_chunker import VideoChunker, get_video_duration
from src.chunk_integrator import ChunkIntegrator


def main():
    print("=" * 80)
    print("実動画での動作確認")
    print("=" * 80)
    
    # APIキー確認
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        sys.exit(1)
    
    print(f"✓ API Key: {api_key[:10]}...")
    
    # 動画ファイルパス
    video_path = r"C:\Users\yiwao\Downloads\【面談】TS様-20260206_193310-会議の録音 (1).mp4"
    
    if not Path(video_path).exists():
        print(f"ERROR: Video file not found: {video_path}")
        sys.exit(1)
    
    print(f"✓ Video file found: {video_path}")
    file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
    print(f"  File size: {file_size_mb:.1f} MB")
    
    try:
        print("\n" + "-" * 80)
        print("Step 1: 動画の長さを取得")
        print("-" * 80)

        duration_seconds = get_video_duration(video_path)
        print(f"✓ Video duration: {duration_seconds:.1f} seconds ({duration_seconds/60:.1f} minutes)")

        print("\n" + "-" * 80)
        print("Step 2: チャンク化")
        print("-" * 80)

        chunker = VideoChunker(chunk_duration_seconds=300)  # 5分 = 300秒
        chunks = chunker.create_chunks(video_path, duration_seconds)
        print(f"✓ {len(chunks)} chunks created")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {chunk.start_time:.1f}s - {chunk.end_time:.1f}s")
        
        print("\n" + "-" * 80)
        print("Step 3: チャンク解析")
        print("-" * 80)
        
        analyzer = ChunkedVideoAnalyzer(api_key=api_key)
        chunk_results = analyzer.analyze_chunks(chunks)
        print(f"✓ {len(chunk_results)} chunks analyzed")
        
        print("\n" + "-" * 80)
        print("Step 4: 統合評価")
        print("-" * 80)
        
        integrator = ChunkIntegrator()
        final_result = integrator.integrate_chunks(chunk_results)
        print("✓ Final evaluation generated")
        
        # 結果の表示
        print("\n" + "=" * 80)
        print("解析結果")
        print("=" * 80)
        
        if "overall_evaluation" in final_result:
            overall = final_result["overall_evaluation"]
            print(f"\n総合評価スコア: {overall.get('overall_score', 'N/A')}/100")
            print(f"リスクレベル: {overall.get('risk_level', 'N/A')}")
            print(f"\nコメント:")
            print(overall.get('comment', 'N/A'))
        
        # 結果を保存
        output_dir = Path(".tmp/execution/iteration_07")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result_json_path = output_dir / "real_video_result.json"
        with open(result_json_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Results saved to: {result_json_path}")
        
        # Markdown形式でも保存
        result_md_path = output_dir / "real_video_result.md"
        with open(result_md_path, "w", encoding="utf-8") as f:
            f.write("# 実動画解析結果\n\n")
            f.write(f"**動画ファイル**: {video_path}\n")
            f.write(f"**ファイルサイズ**: {file_size_mb:.1f} MB\n")
            f.write(f"**チャンク数**: {len(chunks)}\n\n")
            
            if "overall_evaluation" in final_result:
                overall = final_result["overall_evaluation"]
                f.write("## 総合評価\n\n")
                f.write(f"- **総合スコア**: {overall.get('overall_score', 'N/A')}/100\n")
                f.write(f"- **リスクレベル**: {overall.get('risk_level', 'N/A')}\n\n")
                f.write(f"**コメント**:\n\n{overall.get('comment', 'N/A')}\n\n")
            
            f.write("## 完全な結果\n\n")
            f.write("```json\n")
            f.write(json.dumps(final_result, ensure_ascii=False, indent=2))
            f.write("\n```\n")
        
        print(f"✓ Markdown report saved to: {result_md_path}")
        
        print("\n" + "=" * 80)
        print("✓ 実動画での動作確認が完了しました")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

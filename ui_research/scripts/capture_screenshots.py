"""
UI/UXベンチマーク調査用スクリーンショット自動取得スクリプト

20サイトのスクリーンショットを3解像度（デスクトップ・タブレット・モバイル）で自動取得
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from PIL import Image
import sys


class ScreenshotCapture:
    """スクリーンショット取得クラス"""

    def __init__(self, config_path: str, output_dir: str):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 設定ファイル読み込み
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # ログファイル
        self.log_file = self.output_dir.parent / 'analysis' / 'capture_log.json'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_data = {
            'started_at': datetime.now().isoformat(),
            'sites': []
        }

    async def capture_site(self, browser: Browser, site: Dict) -> Dict:
        """単一サイトのスクリーンショット取得"""
        site_id = site['id']
        site_name = site['name']
        site_dir = self.output_dir / site_id
        site_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[{site_id}] {site_name} のキャプチャ開始...")

        site_log = {
            'site_id': site_id,
            'site_name': site_name,
            'url': site['url'],
            'status': 'success',
            'screenshots': [],
            'errors': []
        }

        # 全URLリスト（メインページ + 追加ページ）
        urls = [site['url']] + site.get('additional_pages', [])

        for viewport_name, viewport_size in self.config['viewport_sizes'].items():
            context = await browser.new_context(
                viewport={'width': viewport_size['width'], 'height': viewport_size['height']},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            for idx, url in enumerate(urls):
                page_label = 'main' if idx == 0 else f'page{idx}'
                screenshot_filename = f"{site_id}_{viewport_name}_{page_label}.png"
                screenshot_path = site_dir / screenshot_filename

                try:
                    # ページ読み込み（リトライ機能付き）
                    await self._load_page_with_retry(page, url, site.get('wait_selector', 'main'))

                    # スクリーンショット取得
                    await page.screenshot(
                        path=str(screenshot_path),
                        full_page=self.config['screenshot_settings']['full_page']
                    )

                    site_log['screenshots'].append({
                        'filename': screenshot_filename,
                        'url': url,
                        'viewport': viewport_name
                    })

                    print(f"  [OK] {viewport_name} - {page_label}: {screenshot_filename}")

                except Exception as e:
                    error_msg = f"{viewport_name}/{page_label}: {str(e)}"
                    site_log['errors'].append(error_msg)
                    site_log['status'] = 'partial'
                    print(f"  [ERROR] エラー: {error_msg}")

            await context.close()

        return site_log

    async def _load_page_with_retry(self, page: Page, url: str, wait_selector: str):
        """リトライ機能付きページ読み込み"""
        retry_attempts = self.config['screenshot_settings']['retry_attempts']
        timeout = self.config['screenshot_settings']['timeout']

        for attempt in range(retry_attempts):
            try:
                await page.goto(url, wait_until='networkidle', timeout=timeout)
                await page.wait_for_selector(wait_selector, timeout=10000)
                return
            except Exception as e:
                if attempt == retry_attempts - 1:
                    raise e
                print(f"    リトライ {attempt + 1}/{retry_attempts}...")
                await asyncio.sleep(2)

    async def run(self):
        """全サイトのスクリーンショット取得を実行"""
        print("=" * 60)
        print("UI/UXベンチマーク調査 - スクリーンショット自動取得")
        print("=" * 60)
        print(f"対象サイト数: {len(self.config['sites'])}")
        print(f"出力先: {self.output_dir}")
        print(f"解像度: {', '.join(self.config['viewport_sizes'].keys())}")
        print("=" * 60)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for idx, site in enumerate(self.config['sites'], 1):
                print(f"\n進捗: {idx}/{len(self.config['sites'])}")
                site_log = await self.capture_site(browser, site)
                self.log_data['sites'].append(site_log)

            await browser.close()

        # ログ保存
        self.log_data['completed_at'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)

        # サマリー表示
        self._print_summary()

    def _print_summary(self):
        """実行結果サマリー表示"""
        print("\n" + "=" * 60)
        print("実行結果サマリー")
        print("=" * 60)

        total_sites = len(self.log_data['sites'])
        success_sites = sum(1 for s in self.log_data['sites'] if s['status'] == 'success')
        partial_sites = sum(1 for s in self.log_data['sites'] if s['status'] == 'partial')
        total_screenshots = sum(len(s['screenshots']) for s in self.log_data['sites'])
        total_errors = sum(len(s['errors']) for s in self.log_data['sites'])

        print(f"処理サイト数: {total_sites}")
        print(f"  - 成功: {success_sites}")
        print(f"  - 部分成功: {partial_sites}")
        print(f"取得スクリーンショット数: {total_screenshots}")
        print(f"エラー数: {total_errors}")
        print(f"\nログファイル: {self.log_file}")
        print("=" * 60)


async def main():
    """メイン関数"""
    script_dir = Path(__file__).parent
    config_path = script_dir / 'site_config.json'
    output_dir = script_dir.parent / 'screenshots'

    capture = ScreenshotCapture(str(config_path), str(output_dir))
    await capture.run()


if __name__ == '__main__':
    asyncio.run(main())

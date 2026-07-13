"""共通モジュール: グラフ内の日本語表示のためのフォント設定。

各練習ノートブック（exercises/**/*.ipynb）の冒頭セルから次のように利用する::

    from jp_font import setup_japanese_font
    setup_japanese_font()

リポジトリ同梱の日本語対応フォント ``assets/fonts/101_20260705_droidsansfallbackfull.ttf``
を自動的に探索・登録し、matplotlib 3.6+ のグリフ単位フォールバックによって
「日本語=同梱フォント / 英数字=DejaVu Sans」に振り分ける。これにより OS を
問わず（macOS / Linux / Windows）グラフ内の日本語が文字化けしない。

同梱フォントが見つからない場合は、システムにインストール済みの代表的な
日本語フォントを探索する。それも無ければ既定フォントのままとなる。
"""

import os

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# リポジトリ直下からの同梱フォントの相対パス
_BUNDLED_FONT_RELPATH = os.path.join("assets", "fonts", "101_20260705_droidsansfallbackfull.ttf")

# 同梱フォントが無い場合に探すシステムフォント（優先順）
_SYSTEM_JP_FONTS = [
    "IPAexGothic", "IPAGothic", "Noto Sans CJK JP", "Noto Sans JP",
    "Hiragino Sans", "Yu Gothic", "YuGothic", "Meiryo", "MS Gothic",
    "TakaoPGothic", "VL PGothic", "Droid Sans Fallback",
]


def _search_upward(start):
    """start から親方向へ最大10階層、同梱フォントを探してパスを返す。"""
    d = os.path.abspath(start)
    for _ in range(10):
        cand = os.path.join(d, _BUNDLED_FONT_RELPATH)
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def find_bundled_font():
    """同梱の日本語フォントファイルのパスを返す（見つからなければ None）。

    このモジュール自身の位置と、実行時のカレントディレクトリの両方から
    探索するため、リポジトリ内のどこでノートブックを起動してもよい。
    """
    # モジュール自身（リポジトリ直下に置かれる想定）の位置から探す
    here = os.path.dirname(os.path.abspath(__file__))
    found = _search_upward(here)
    if found:
        return found
    # カレントディレクトリからも探す（フォールバック）
    return _search_upward(os.getcwd())


def setup_japanese_font(verbose=False):
    """matplotlib のフォントを日本語対応に設定し、採用フォント名を返す。

    Parameters
    ----------
    verbose : bool
        True のとき、採用したフォント名を出力する。

    Returns
    -------
    str or None
        採用した日本語フォント名。設定できなかった場合は None。
    """
    font_name = None

    path = find_bundled_font()
    if path:
        fm.fontManager.addfont(path)
        font_name = fm.FontProperties(fname=path).get_name()
    else:
        installed = {f.name for f in fm.fontManager.ttflist}
        for cand in _SYSTEM_JP_FONTS:
            if cand in installed:
                font_name = cand
                break

    if font_name:
        # 日本語=この フォント / 英数字=DejaVu Sans（グリフ単位フォールバック）
        family = [font_name, "DejaVu Sans"]
        plt.rcParams["font.family"] = family
        # family="sans-serif" を明示指定した要素にも反映されるようにする
        plt.rcParams["font.sans-serif"] = family + [
            f for f in plt.rcParams.get("font.sans-serif", []) if f not in family
        ]

    # 負号が豆腐（□）になるのを防ぐ
    plt.rcParams["axes.unicode_minus"] = False

    if verbose:
        print("[jp_font] font.family =", font_name or "(日本語フォント未検出・既定のまま)")
    return font_name

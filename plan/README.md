# ミアゲタビ（宇宙を見に行くガイド）立ち上げ計画

作成日：2026-10-15。同じ日に、テーマを**宇宙に統一**した（ロケット打ち上げ・天体イベント・宇宙スポット）。自動運転は別サイトで運営する（[../plan-mobility/](../plan-mobility/)）。調べて確認できなかった情報には「推測」と書いている。

**サイト：https://miagetabi.space/ （2026-10-15 公開。WordPress＋SWELL）**

| # | ファイル | 中身 |
|---|---|---|
| 1-A | [01a-market-events.md](01a-market-events.md) | 今後12か月のロケット打ち上げ・天体イベント（出典URL付き） |
| 1-B | [01b-competitors.md](01b-competitors.md) | 既存サイト・SNSと、手薄な部分 |
| 2 | [02-site-design.md](02-site-design.md) | サイト名5案、カテゴリとURL設計、直前に検索が集中することを活かす更新ルール |
| 3 | [03-first-20-articles.md](03-first-20-articles.md) | 最初に書く20本（キーワード・検索意図・公開期限・収益化の導線） |
| 4 | [templates/](templates/) | 記事テンプレート3種（打ち上げ観覧・天体イベント・宇宙スポット見学） |
| 5 | [04-90day-plan.md](04-90day-plan.md) | 90日間の週ごとのタスク、SNSの告知方法、3か月後の判断基準 |
| 6 | [06-article-quality.md](06-article-quality.md) | 記事の品質設計（8つの柱・AIの失敗の型・作成と査読の流れ）。エージェントの手順書は `../app/ops/` |
| 付録 | [05-ai-workflow.md](05-ai-workflow.md) | 下調べ・構成・更新・告知をAIで定型化するプロンプト |
| 構築 | [../site/README.md](../site/README.md) | WordPress＋SWELLの構築手順・自作プラグイン・初期設定スクリプト・固定ページの文面 |
| 公開版 | https://claude.ai/artifact/GfvPCFr2Cvigike2XgLeDF | この計画書を1ページにまとめたもの（`index.html`。`build_html.py` で作り直せる） |
| アプリ | [../app/index.html](../app/index.html) | サイト管理アプリ（公開先：https://claude.ai/artifact/CFkmjQnXk8beWmPEPwscjP ）。初期データは `../app/seed/`。エージェントの手順書と道具は `../app/ops/` |
| エージェント | 記事作成 `trig_019wvFL2AJwKjhoQQnozFSv8`・査読 `trig_01J6vdgPcBtvsQTksvFUqSzD` | クラウドの定期実行タスク。アプリから依頼するとすぐ起動し、3時間ごとにも見回る |

## いちばん大事な3点
1. **H3ロケット10号機（MMX）の打ち上げが 10/20(火) 4:41。** 記事#1は10/17までに出す。サイトが間に合わなければ、まずXで動く。
2. **この90日の山場は 12/14 のふたご座流星群**（月が早く沈む絶好の条件）。記事は11/14に公開して、直前に厚く更新する。
3. **打ち上げのない日も検索される常設ページを先に作る。** 打ち上げ予定まとめ（#3）と射場ガイド（#4・#15・#20）があれば、HTV-X2・イプシロンS・カイロスの日付が出たときに48時間以内に回ごとの記事を出せる。

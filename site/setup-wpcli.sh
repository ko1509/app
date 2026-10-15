#!/usr/bin/env bash
# ミアゲタビ（宇宙を見に行くガイド）：WordPress の初期設定をまとめて行うスクリプト（WP-CLI 用）
#
# 使い方（SSH でサーバーに入り、WordPress のフォルダで実行）:
#   cd ~/<ドメイン>/public_html
#   bash setup-wpcli.sh
#
# SSH が使えないときは、site/README.md の「手作業でやる場合」を見てください。
# 何度実行しても同じ結果になるように書いています（既にあるものは作り直しません）。
set -euo pipefail

WP="${WP:-wp}"

echo "== 一般設定（タイムゾーン・日付の形式）"
$WP option update timezone_string "Asia/Tokyo"
$WP option update date_format "Y年n月j日"
$WP option update time_format "G:i"
$WP option update start_of_week 1

echo "== パーマリンク：/カテゴリー/投稿名/"
$WP rewrite structure '/%category%/%postname%/' --hard

echo "== カテゴリー"
# 既定の「未分類」は「お知らせ」に変える
$WP term update category 1 --name="お知らせ" --slug="news" >/dev/null
make_cat () { # $1=slug $2=名前 $3=説明
  if $WP term get category "$1" --by=slug --field=term_id >/dev/null 2>&1; then
    echo "  あり: $2"
  else
    $WP term create category "$2" --slug="$1" --description="$3" >/dev/null && echo "  作成: $2"
  fi
}
make_cat launch "ロケット打ち上げ" "ロケットの打ち上げを見に行くためのガイド。見える場所・到着時刻・延期のときの動き方。"
make_cat sky    "天体イベント"     "流星群・満月・惑星の接近・宇宙ステーションの通過を、スマホで見て撮るためのガイド。"
make_cat spot   "宇宙スポット"     "ロケットの発射場・JAXAの施設・天文台・科学館など、宇宙を見に行ける場所のガイド。"
make_cat gear   "機材・持ち物"     "スマホ三脚・双眼鏡・防寒グッズなど、見に行く・撮るための道具。"

echo "== 固定ページ（下書きで作成。文面は site/pages.md）"
make_page () { # $1=slug $2=タイトル
  if [ -n "$($WP post list --post_type=page --pagename="$1" --post_status=draft,publish,pending,private,future --field=ID)" ]; then
    echo "  あり: $2"
  else
    $WP post create --post_type=page --post_status=draft --post_title="$2" --post_name="$1" >/dev/null && echo "  作成: $2"
  fi
}
make_page about   "運営者情報"
make_page contact "お問い合わせ"
# プライバシーポリシーは WordPress が最初から作る下書きを使う（設定の「プライバシー」とつながっているため）
PRIV=$($WP option get wp_page_for_privacy_policy 2>/dev/null || echo 0)
if [ "${PRIV:-0}" != "0" ] && $WP post exists "$PRIV" >/dev/null 2>&1; then
  $WP post update "$PRIV" --post_title="プライバシーポリシー・広告について" --post_name="policy" >/dev/null && echo "  更新: プライバシーポリシー・広告について"
else
  make_page policy "プライバシーポリシー・広告について"
  $WP option update wp_page_for_privacy_policy "$($WP post list --post_type=page --pagename=policy --post_status=draft,publish,pending,private,future --field=ID)" >/dev/null
fi

echo "== サンプルの記事・ページを削除"
for id in $($WP post list --post_type=post --name=hello-world --field=ID) $($WP post list --post_type=page --name=sample-page --field=ID); do
  $WP post delete "$id" --force >/dev/null && echo "  削除: $id"
done

echo "== プラグイン（SWELL と相性の良いものだけ）"
for p in seo-simple-pack wp-multibyte-patch contact-form-7 pochipp; do
  if $WP plugin is-installed "$p"; then
    $WP plugin activate "$p" >/dev/null 2>&1 || true; echo "  あり: $p"
  else
    $WP plugin install "$p" --activate >/dev/null && echo "  導入: $p"
  fi
done
if [ -f miagetabi-core.zip ]; then
  $WP plugin install miagetabi-core.zip --activate --force >/dev/null && echo "  導入: miagetabi-core"
else
  echo "  （miagetabi-core.zip をこのフォルダに置くと一緒に入ります）"
fi

echo "== コメント欄を閉じる（スパム対策。必要になったら開く）"
$WP option update default_comment_status closed
$WP option update default_ping_status closed

echo "完了。次は site/README.md の「ステップ3 SWELL の設定」へ。"

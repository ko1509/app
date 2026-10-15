<?php
/**
 * Plugin Name: ミライミニイク Core
 * Description: 宇宙を見に行くガイドのための、イベント情報（日時・状況・最終確認日・公式情報）の入力欄、記事冒頭の「今の状況」ボックス、Event構造化データ、記事テンプレート3種（ブロックパターン）を追加します。SWELLと一緒に使う前提です。
 * Version: 1.0.0
 * Requires at least: 6.3
 * Requires PHP: 7.4
 * Author: ミライミニイク
 * License: GPL-2.0-or-later
 * Text Domain: mirai-core
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MM_PREFIX = '_mm_';

/**
 * 状況の選択肢。キーは保存値、値は [表示名, schema.org の eventStatus, 色の種類]。
 */
function mm_statuses() {
	return array(
		'scheduled'   => array( '予定どおり', 'EventScheduled', 'ok' ),
		'postponed'   => array( '延期（新しい日は未定）', 'EventPostponed', 'bad' ),
		'rescheduled' => array( '日程変更', 'EventRescheduled', 'warn' ),
		'cancelled'   => array( '中止', 'EventCancelled', 'bad' ),
		'ongoing'     => array( '開催中・公開中', 'EventScheduled', 'ok' ),
		'paused'      => array( '休止中・休館中', 'EventPostponed', 'bad' ),
		'done'        => array( '終了', 'EventScheduled', 'mute' ),
	);
}

/** 入力欄の定義：キー => [ラベル, 種類, 補足] */
function mm_fields() {
	return array(
		'event_date'    => array( 'イベント日（開始日）', 'date', '打ち上げ日・極大日・展示の開始日など' ),
		'event_time'    => array( '時刻', 'text', '例：4:41　/　21:00〜翌3:00' ),
		'event_end'     => array( '終了日（期間があるとき）', 'date', '展示・公開期間などの最終日。打ち上げの予備期間はメモに書く' ),
		'status'        => array( '今の状況', 'select', '' ),
		'place'         => array( '場所', 'text', '例：種子島宇宙センター（鹿児島県南種子町）' ),
		'sources'       => array( '公式情報のURL（1行に1つ）', 'textarea', '冒頭ボックスに「公式情報」として並びます。2つ以上を推奨' ),
		'last_verified' => array( '最終確認日時', 'datetime-local', '公式情報を目で確かめた日時' ),
		'note'          => array( 'ひとことメモ（冒頭ボックスに表示）', 'text', '例：中継は3:46から　/　見学ツアーは要予約' ),
		'autobox'       => array( '記事の冒頭に「今の状況」ボックスを自動で出す', 'checkbox', '' ),
		'schema'        => array( 'Event の構造化データを出す', 'checkbox', '打ち上げ・天体イベントの回ごとの記事でオン。常設ガイドではオフ' ),
	);
}

function mm_get( $post_id, $key ) {
	return get_post_meta( $post_id, MM_PREFIX . $key, true );
}

/* ---------------------------------------------------------------
 * 入力欄（投稿の編集画面のメタボックス）
 * ------------------------------------------------------------- */
add_action( 'add_meta_boxes', function () {
	add_meta_box( 'mm_event', 'イベント情報（ミライミニイク）', 'mm_render_meta_box', 'post', 'side', 'high' );
} );

function mm_render_meta_box( $post ) {
	wp_nonce_field( 'mm_save_' . $post->ID, 'mm_nonce' );
	echo '<div class="mm-meta">';
	foreach ( mm_fields() as $key => $f ) {
		list( $label, $type, $help ) = $f;
		$id    = 'mm_' . $key;
		$name  = 'mm[' . $key . ']';
		$value = mm_get( $post->ID, $key );
		if ( 'autobox' === $key && '' === $value ) {
			$value = '1'; // 新しい記事は既定でオン
		}
		echo '<p style="margin:0 0 10px">';
		if ( 'checkbox' === $type ) {
			printf(
				'<label for="%1$s"><input type="checkbox" id="%1$s" name="%2$s" value="1" %3$s> %4$s</label>',
				esc_attr( $id ),
				esc_attr( $name ),
				checked( $value, '1', false ),
				esc_html( $label )
			);
		} else {
			printf( '<label for="%s" style="display:block;font-weight:600">%s</label>', esc_attr( $id ), esc_html( $label ) );
			if ( 'select' === $type ) {
				printf( '<select id="%s" name="%s" style="width:100%%"><option value="">（表示しない）</option>', esc_attr( $id ), esc_attr( $name ) );
				foreach ( mm_statuses() as $k => $s ) {
					printf( '<option value="%s" %s>%s</option>', esc_attr( $k ), selected( $value, $k, false ), esc_html( $s[0] ) );
				}
				echo '</select>';
			} elseif ( 'textarea' === $type ) {
				printf( '<textarea id="%s" name="%s" rows="3" style="width:100%%">%s</textarea>', esc_attr( $id ), esc_attr( $name ), esc_textarea( $value ) );
			} else {
				printf( '<input type="%s" id="%s" name="%s" value="%s" style="width:100%%">', esc_attr( $type ), esc_attr( $id ), esc_attr( $name ), esc_attr( $value ) );
			}
		}
		if ( $help ) {
			printf( '<span style="display:block;color:#646970;font-size:12px">%s</span>', esc_html( $help ) );
		}
		echo '</p>';
	}
	echo '<p style="margin:0"><button type="button" class="button" id="mm_now">最終確認を「いま」にする</button></p>';
	echo '<script>document.getElementById("mm_now").addEventListener("click",function(){var d=new Date(),p=function(n){return String(n).padStart(2,"0")};document.getElementById("mm_last_verified").value=d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate())+"T"+p(d.getHours())+":"+p(d.getMinutes());});</script>';
	echo '</div>';
}

add_action( 'save_post_post', function ( $post_id ) {
	if ( ! isset( $_POST['mm_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['mm_nonce'] ) ), 'mm_save_' . $post_id ) ) {
		return;
	}
	if ( ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) || ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}
	$in = isset( $_POST['mm'] ) && is_array( $_POST['mm'] ) ? wp_unslash( $_POST['mm'] ) : array();
	foreach ( mm_fields() as $key => $f ) {
		$type = $f[1];
		$raw  = isset( $in[ $key ] ) ? $in[ $key ] : '';
		switch ( $type ) {
			case 'checkbox':
				$val = '1' === $raw ? '1' : '0';
				break;
			case 'date':
				$val = preg_match( '/^\d{4}-\d{2}-\d{2}$/', $raw ) ? $raw : '';
				break;
			case 'datetime-local':
				$val = preg_match( '/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/', $raw ) ? $raw : '';
				break;
			case 'select':
				$val = array_key_exists( $raw, mm_statuses() ) ? $raw : '';
				break;
			case 'textarea':
				$urls = array_filter( array_map( 'esc_url_raw', array_map( 'trim', preg_split( '/\R/', (string) $raw ) ) ) );
				$val  = implode( "\n", $urls );
				break;
			default:
				$val = sanitize_text_field( $raw );
		}
		update_post_meta( $post_id, MM_PREFIX . $key, $val );
	}
} );

/* ---------------------------------------------------------------
 * 冒頭の「今の状況」ボックス（自動挿入とショートコード [mm_status]）
 * ------------------------------------------------------------- */
function mm_fmt_date( $ymd ) {
	if ( ! $ymd ) {
		return '';
	}
	$ts = strtotime( $ymd . ' 00:00:00' );
	$w  = array( '日', '月', '火', '水', '木', '金', '土' );
	return wp_date( 'Y年n月j日', $ts, new DateTimeZone( 'UTC' ) ) . '（' . $w[ (int) gmdate( 'w', $ts ) ] . '）';
}

function mm_status_box( $post_id ) {
	$date     = mm_get( $post_id, 'event_date' );
	$status   = mm_get( $post_id, 'status' );
	$verified = mm_get( $post_id, 'last_verified' );
	if ( ! $date && ! $status && ! $verified ) {
		return '';
	}
	$statuses = mm_statuses();
	$time     = mm_get( $post_id, 'event_time' );
	$end      = mm_get( $post_id, 'event_end' );
	$place    = mm_get( $post_id, 'place' );
	$note     = mm_get( $post_id, 'note' );
	$sources  = array_filter( explode( "\n", (string) mm_get( $post_id, 'sources' ) ) );

	$rows = array();
	if ( $date ) {
		if ( $end && $end !== $date ) {
			$rows[] = array( '期間', esc_html( mm_fmt_date( $date ) . ' 〜 ' . mm_fmt_date( $end ) ) );
			if ( $time ) {
				$rows[] = array( '時刻', esc_html( $time ) );
			}
		} else {
			$rows[] = array( '日時', esc_html( mm_fmt_date( $date ) . ( $time ? ' ' . $time : '' ) ) );
		}
	}
	if ( $place ) {
		$rows[] = array( '場所', esc_html( $place ) );
	}
	if ( $note ) {
		$rows[] = array( 'メモ', esc_html( $note ) );
	}
	if ( $sources ) {
		$links = array();
		foreach ( array_values( $sources ) as $i => $u ) {
			$host    = wp_parse_url( $u, PHP_URL_HOST );
			$links[] = sprintf( '<a href="%s" target="_blank" rel="noopener">%s</a>', esc_url( $u ), esc_html( $host ? $host : '公式' . ( $i + 1 ) ) );
		}
		$rows[] = array( '公式情報', implode( '　', $links ) );
	}

	$html = '<div class="mm-box">';
	if ( $status && isset( $statuses[ $status ] ) ) {
		$html .= sprintf( '<p class="mm-box__status mm-%s"><span>今の状況</span>%s</p>', esc_attr( $statuses[ $status ][2] ), esc_html( $statuses[ $status ][0] ) );
	}
	if ( $rows ) {
		$html .= '<dl class="mm-box__list">';
		foreach ( $rows as $r ) {
			$html .= '<dt>' . esc_html( $r[0] ) . '</dt><dd>' . $r[1] . '</dd>';
		}
		$html .= '</dl>';
	}
	if ( $verified ) {
		$ts    = strtotime( str_replace( 'T', ' ', $verified ) . ':00' );
		$html .= '<p class="mm-box__verified">最終確認：' . esc_html( wp_date( 'Y年n月j日 G:i', $ts, new DateTimeZone( 'UTC' ) ) ) . '　予定は変わることがあるので、出かける前に公式情報も確かめてください。</p>';
	}
	return $html . '</div>';
}

add_shortcode( 'mm_status', function () {
	return mm_status_box( get_the_ID() );
} );

add_filter( 'the_content', function ( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	$id = get_the_ID();
	if ( '0' === mm_get( $id, 'autobox' ) || has_shortcode( $content, 'mm_status' ) ) {
		return $content;
	}
	return mm_status_box( $id ) . $content;
}, 8 );

add_action( 'wp_enqueue_scripts', function () {
	$css = '
.mm-box{margin:0 0 2em;padding:1em 1.2em;border:2px solid var(--color_main,#1f4fd1);border-radius:10px;background:color-mix(in srgb,var(--color_main,#1f4fd1) 5%,transparent)}
.mm-box__status{margin:0 0 .6em!important;font-weight:700;font-size:1.1em;display:flex;align-items:center;gap:.6em;flex-wrap:wrap}
.mm-box__status span{font-size:.75em;font-weight:700;padding:.15em .7em;border-radius:99px;background:#fff;border:1px solid currentColor}
.mm-ok{color:#1a7f37}.mm-warn{color:#b25000}.mm-bad{color:#d70015}.mm-mute{color:#6e6e73}
.mm-box__list{display:grid;grid-template-columns:auto 1fr;gap:.35em 1em;margin:0}
.mm-box__list dt{font-weight:700;white-space:nowrap}.mm-box__list dd{margin:0;overflow-wrap:anywhere}
.mm-box__verified{margin:.8em 0 0!important;font-size:.85em;opacity:.8}
@media (max-width:480px){.mm-box__list{grid-template-columns:1fr}.mm-box__list dd{margin-bottom:.4em}}';
	wp_register_style( 'mirai-core', false, array(), '1.0.0' );
	wp_enqueue_style( 'mirai-core' );
	wp_add_inline_style( 'mirai-core', $css );
} );

/* ---------------------------------------------------------------
 * Event 構造化データ（JSON-LD）
 * ------------------------------------------------------------- */
add_action( 'wp_head', function () {
	if ( ! is_singular( 'post' ) ) {
		return;
	}
	$id   = get_queried_object_id();
	$date = mm_get( $id, 'event_date' );
	if ( '1' !== mm_get( $id, 'schema' ) || ! $date ) {
		return;
	}
	$time  = mm_get( $id, 'event_time' );
	$start = $date;
	if ( preg_match( '/^(\d{1,2}):(\d{2})/', (string) $time, $m ) ) {
		$start .= sprintf( 'T%02d:%02d:00+09:00', $m[1], $m[2] );
	}
	$statuses = mm_statuses();
	$status   = mm_get( $id, 'status' );
	$place    = mm_get( $id, 'place' );
	$data     = array(
		'@context'            => 'https://schema.org',
		'@type'               => 'Event',
		'name'                => wp_strip_all_tags( get_the_title( $id ) ),
		'startDate'           => $start,
		'eventAttendanceMode' => 'https://schema.org/OfflineEventAttendanceMode',
		'eventStatus'         => 'https://schema.org/' . ( isset( $statuses[ $status ] ) ? $statuses[ $status ][1] : 'EventScheduled' ),
		'location'            => array(
			'@type'   => 'Place',
			'name'    => $place ? $place : '日本',
			'address' => $place ? $place : '日本',
		),
		'description'         => wp_strip_all_tags( get_the_excerpt( $id ) ),
		'url'                 => get_permalink( $id ),
	);
	$end = mm_get( $id, 'event_end' );
	if ( $end ) {
		$data['endDate'] = $end;
	}
	$img = get_the_post_thumbnail_url( $id, 'full' );
	if ( $img ) {
		$data['image'] = array( $img );
	}
	echo '<script type="application/ld+json">' . wp_json_encode( $data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . "</script>\n";
} );

/* ---------------------------------------------------------------
 * 投稿一覧に「イベント日・状況・最終確認」の列（直前更新の見落とし防止）
 * ------------------------------------------------------------- */
add_filter( 'manage_post_posts_columns', function ( $cols ) {
	$cols['mm_event']    = 'イベント日';
	$cols['mm_status']   = '状況';
	$cols['mm_verified'] = '最終確認';
	return $cols;
} );

add_action( 'manage_post_posts_custom_column', function ( $col, $post_id ) {
	if ( 'mm_event' === $col ) {
		$d = mm_get( $post_id, 'event_date' );
		if ( $d ) {
			$days = (int) floor( ( strtotime( $d ) - strtotime( wp_date( 'Y-m-d' ) ) ) / DAY_IN_SECONDS );
			$t    = 0 === $days ? 'T−0（当日）' : ( $days > 0 ? 'T−' . $days : 'T+' . abs( $days ) );
			echo esc_html( $d ) . '<br><strong>' . esc_html( $t ) . '</strong>';
		} else {
			echo '—';
		}
	} elseif ( 'mm_status' === $col ) {
		$s  = mm_get( $post_id, 'status' );
		$ss = mm_statuses();
		echo esc_html( isset( $ss[ $s ] ) ? $ss[ $s ][0] : '—' );
	} elseif ( 'mm_verified' === $col ) {
		$v = mm_get( $post_id, 'last_verified' );
		echo esc_html( $v ? str_replace( 'T', ' ', $v ) : '—' );
	}
}, 10, 2 );

add_filter( 'manage_edit-post_sortable_columns', function ( $cols ) {
	$cols['mm_event'] = 'mm_event';
	return $cols;
} );

add_action( 'pre_get_posts', function ( $q ) {
	if ( is_admin() && $q->is_main_query() && 'mm_event' === $q->get( 'orderby' ) ) {
		$q->set( 'meta_key', MM_PREFIX . 'event_date' );
		$q->set( 'orderby', 'meta_value' );
	}
} );

/* ---------------------------------------------------------------
 * 記事テンプレート（ブロックパターン）
 * ------------------------------------------------------------- */
function mm_b_h2( $t ) {
	return "<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">" . esc_html( $t ) . "</h2>\n<!-- /wp:heading -->\n\n";
}
function mm_b_h3( $t ) {
	return "<!-- wp:heading {\"level\":3} -->\n<h3 class=\"wp-block-heading\">" . esc_html( $t ) . "</h3>\n<!-- /wp:heading -->\n\n";
}
function mm_b_p( $t ) {
	return "<!-- wp:paragraph -->\n<p>" . esc_html( $t ) . "</p>\n<!-- /wp:paragraph -->\n\n";
}
function mm_b_list( $items ) {
	$out = "<!-- wp:list -->\n<ul class=\"wp-block-list\">";
	foreach ( $items as $i ) {
		$out .= "<!-- wp:list-item -->\n<li>" . esc_html( $i ) . "</li>\n<!-- /wp:list-item -->";
	}
	return $out . "</ul>\n<!-- /wp:list -->\n\n";
}
function mm_b_status() {
	return "<!-- wp:shortcode -->\n[mm_status]\n<!-- /wp:shortcode -->\n\n";
}

add_action( 'init', function () {
	if ( ! function_exists( 'register_block_pattern' ) ) {
		return;
	}
	register_block_pattern_category( 'mirai', array( 'label' => 'ミライミニイク' ) );

	$launch = mm_b_status()
		. mm_b_p( '【3行で結論】いつ・どこで・何を持って行けばいいか。初めての人がこの3行だけ読めば動けるように書く。' )
		. mm_b_h2( 'まず結論：初めてならこの見方がおすすめ' )
		. mm_b_p( '見学場・到着時刻・持ち物を、おすすめ1つに絞って書く。' )
		. mm_b_h2( '打ち上げの基本情報' )
		. mm_b_list( array( '日時（予備期間）：', '何を運ぶ？（専門用語は一言で言い換える）：', '出典：公式発表のURL' ) )
		. mm_b_h2( '見える場所（見学場）' )
		. mm_b_p( '表：場所名／射点からの距離／見え方／駐車場／トイレ／有料・無料・抽選。公式の案内と、運営者の推測を必ず分ける。' )
		. mm_b_h2( '何時に着けばいい？当日のタイムライン' )
		. mm_b_list( array( '前日まで：宿・交通の確保', '当日 ○時：宿を出る', '○時：見学場に着く', '○時：打ち上げ', '○時：帰りの渋滞' ) )
		. mm_b_h2( '行き方（アクセス）' )
		. mm_b_p( '島外から（飛行機・高速船）と島内（レンタカー・バス）。レンタカーは台数が少ないので早めに。[AFF:交通]' )
		. mm_b_h2( '泊まる場所' )
		. mm_b_p( '延期に備えてキャンセル無料のプランを選ぶ。エリアごとの埋まりやすさ。[AFF:宿]' )
		. mm_b_h2( '持ち物チェックリスト' )
		. mm_b_list( array( 'スマホ・モバイルバッテリー', '飲み物・日よけ／防寒', '虫よけ・レジャーシート', 'あると良い：双眼鏡・三脚 [AFF:機材]' ) )
		. mm_b_h2( 'スマホで撮るコツ' )
		. mm_b_p( '動画がおすすめ。ズームしすぎない。夜の打ち上げは長秒露光で軌跡を撮る。' )
		. mm_b_h2( '延期・中止になったら' )
		. mm_b_list( array( '① 公式サイト', '② 公式X', '③ ライブ中継', '④ 自治体・観光協会' ) )
		. mm_b_p( '延期はよくあること。宿や帰りの便を延ばす／キャンセルする判断のしかた。' )
		. mm_b_h2( 'ライブ中継で見る（現地に行けない人）' )
		. mm_b_p( '中継のURLと開始時刻。' )
		. mm_b_h2( 'よくある質問' )
		. mm_b_h3( '子連れで行ける？' ) . mm_b_p( '' )
		. mm_b_h3( '音は聞こえる？' ) . mm_b_p( '' )
		. mm_b_h2( '更新履歴' )
		. mm_b_list( array( 'YYYY/MM/DD HH:MM 公開' ) );

	$sky = mm_b_status()
		. mm_b_p( '【3行で結論】いつ・何時・どの方角か。今年の見やすさ（月明かり）。スマホで撮れるか。' )
		. mm_b_h2( 'まず結論：今年はこう見るのがおすすめ' )
		. mm_b_p( '' )
		. mm_b_h2( 'いつ・何時に見ればいい？' )
		. mm_b_list( array( '○時：放射点が昇る', '○時：見ごろ', '○時：空が明るくなりはじめる', '出典：国立天文台など' ) )
		. mm_b_h2( 'どこで見る？' )
		. mm_b_p( '街灯が少なく、空が広く、安全な場所の条件。星空で有名な場所と宿。[AFF:宿]' )
		. mm_b_h2( 'スマホで撮る方法' )
		. mm_b_h3( 'iPhone' ) . mm_b_p( 'ナイトモード・三脚・露出時間。' )
		. mm_b_h3( 'Android（Pixelなど）' ) . mm_b_p( '夜景モード／天体写真モード。' )
		. mm_b_list( array( '三脚は必須 [AFF:三脚]', 'ズームしない', '流星は連写やタイムラプスで撮って、あとから探す' ) )
		. mm_b_h2( '持ち物と寒さ対策' )
		. mm_b_list( array( 'レジャーシート', '防寒具・カイロ [AFF:防寒]', '赤いライト', 'モバイルバッテリー（寒いと減りが早い）' ) )
		. mm_b_h2( '天気が悪いとき・見逃したとき' )
		. mm_b_p( '雲の予報の見方、ライブ配信、次のチャンス（次のイベントの記事へのリンク）。' )
		. mm_b_h2( 'よくある質問' )
		. mm_b_h3( '双眼鏡は必要？' ) . mm_b_p( '' )
		. mm_b_h2( '更新履歴' )
		. mm_b_list( array( 'YYYY/MM/DD 公開' ) );

	$spot = mm_b_status()
		. mm_b_p( '【3行で結論】どこにある？予約は要る？何時間あれば楽しめる？' )
		. mm_b_list( array( '場所：', '開いている日・時間：', '予約：要る／要らない（予約先）', '料金：', 'おすすめの所要時間：' ) )
		. mm_b_h2( 'どんな場所？（ひとことで）' )
		. mm_b_p( '何が見られるか。ロケットの実物・管制室・展示・プラネタリウムなど。' )
		. mm_b_h2( '見どころ' )
		. mm_b_list( array( '見どころ1：', '見どころ2：', '写真を撮っていい場所・だめな場所：' ) )
		. mm_b_h2( '見学ツアー・予約のしかた' )
		. mm_b_list( array( '① 予約ページ（URL）', '② 受付の場所と時間', '③ 当日の流れ' ) )
		. mm_b_h2( '実際に行ってみた' )
		. mm_b_p( '行った日・混み具合・かかった時間。まだ行っていないときは「訪問レポート準備中」と書き、公式情報だけで書く。' )
		. mm_b_h2( '行き方' )
		. mm_b_p( '最寄り駅・バス・駐車場。[AFF:交通]' )
		. mm_b_h2( 'あわせて行きたい宇宙スポット・泊まるなら' )
		. mm_b_p( '近くの発射場・天文台・科学館。打ち上げ観覧と組み合わせるモデルコース。[AFF:宿]' )
		. mm_b_h2( '休館・変更を確かめる方法' )
		. mm_b_p( '公式サイト・公式X。打ち上げ日の前後は見学が止まることがある。' )
		. mm_b_h2( 'よくある質問' )
		. mm_b_h3( '子ども連れでも楽しめる？' ) . mm_b_p( '' )
		. mm_b_h2( '更新履歴' )
		. mm_b_list( array( 'YYYY/MM/DD 公開' ) );

	register_block_pattern( 'mirai/launch', array( 'title' => 'A 打ち上げ観覧ガイド', 'categories' => array( 'mirai' ), 'content' => $launch ) );
	register_block_pattern( 'mirai/sky', array( 'title' => 'B 天体イベントガイド', 'categories' => array( 'mirai' ), 'content' => $sky ) );
	register_block_pattern( 'mirai/spot', array( 'title' => 'C 宇宙スポット見学ガイド', 'categories' => array( 'mirai' ), 'content' => $spot ) );
} );

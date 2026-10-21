#!/usr/bin/env python3
"""GA4 のアクセス集計を取り出して JSON にする（読み取り専用）。

環境変数：
  GA4_PROPERTY_ID            数字のプロパティID（例 412345678）
  GA4_SERVICE_ACCOUNT_JSON   閲覧者に追加したサービスアカウントの鍵（JSON そのもの）
使い方： python3 ga4_report.py [日数=28] > access.json
値は表示しない。鍵・ID は出力に含めない。
"""
import base64, json, os, sys, time, urllib.parse, urllib.request
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def token(sa):
    now = int(time.time())
    head = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = b64(json.dumps({
        "iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3000}).encode())
    key = serialization.load_pem_private_key(sa["private_key"].encode(), None)
    sig = key.sign(head + b"." + claim, padding.PKCS1v15(), hashes.SHA256())
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": (head + b"." + claim + b"." + b64(sig)).decode()}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", body)) as r:
        return json.load(r)["access_token"]


def report(tok, prop, days, dims, mets, limit=10, order=None):
    req = {"dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
           "dimensions": [{"name": d} for d in dims], "metrics": [{"name": m} for m in mets], "limit": limit}
    if order:
        req["orderBys"] = order
    r = urllib.request.Request(f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport",
                               json.dumps(req).encode(),
                               {"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    with urllib.request.urlopen(r) as f:
        d = json.load(f)
    return [{"d": [x["value"] for x in row["dimensionValues"]], "m": [float(x["value"]) for x in row["metricValues"]]}
            for row in d.get("rows", [])]


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()
    raw = os.environ.get("GA4_SERVICE_ACCOUNT_JSON", "").strip()
    if not prop or not raw:
        print("GA4_PROPERTY_ID / GA4_SERVICE_ACCOUNT_JSON が未設定です", file=sys.stderr)
        sys.exit(2)
    if not raw.startswith("{"):  # 環境変数に外側の { } を含めずに入れた場合
        raw = "{" + raw.rstrip().rstrip(",") + "}"
    sa = json.loads(raw, strict=False)
    if "client_email" not in sa:  # 鍵の行だけ入れた場合は、別の環境変数のメールを使う
        sa["client_email"] = os.environ.get("GA4_CLIENT_EMAIL", "").strip()
    if not sa["client_email"] or "private_key" not in sa:
        print("鍵に client_email か private_key がありません（GA4_CLIENT_EMAIL を足すか、JSON全体を入れ直す）", file=sys.stderr)
        sys.exit(2)
    tok = token(sa)
    by = lambda n: [{"order_by": 0}]
    tot = report(tok, prop, days, [], ["activeUsers", "sessions", "screenPageViews", "newUsers", "engagementRate"])
    daily = report(tok, prop, days, ["date"], ["activeUsers", "screenPageViews"], 400,
                   [{"dimension": {"dimensionName": "date"}}])
    top = lambda dims, met="activeUsers", n=10: [
        {"name": " / ".join(r["d"]), "users": int(r["m"][0]), "views": int(r["m"][1]) if len(r["m"]) > 1 else None}
        for r in report(tok, prop, days, dims, [met, "screenPageViews"], n,
                        [{"metric": {"metricName": met}, "desc": True}])]
    t = tot[0]["m"] if tot else [0] * 5
    out = {
        "days": days, "at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00", time.gmtime(time.time() + 9 * 3600)),
        "totals": {"users": int(t[0]), "sessions": int(t[1]), "views": int(t[2]), "newUsers": int(t[3]),
                   "engagement": round(t[4] * 100, 1)},
        "daily": [{"date": r["d"][0], "users": int(r["m"][0]), "views": int(r["m"][1])} for r in daily],
        "countries": top(["country"]), "regions": top(["country", "region"], n=12),
        "devices": top(["deviceCategory"]), "browsers": top(["browser"], n=6), "os": top(["operatingSystem"], n=6),
        "channels": top(["sessionDefaultChannelGroup"]), "sources": top(["sessionSource"], n=10),
        "pages": top(["pagePath"], n=15),
    }
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

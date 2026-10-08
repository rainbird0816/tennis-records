"""보조 소스(tennis-data.co.uk) → Sackmann 스키마 보강 CSV (§13 데이터 리스크 대응).

배경
----
2026-06 중 Jeff Sackmann 의 `tennis_atp` / `tennis_wta` 리포지토리가 비공개 처리되어
모든 원천 URL 이 HTTP 404 를 반환한다(`data/update.log` 의 연속 `miss` 참고).
그 결과 2026 시즌은 **롤랑가로스(5월)까지만** 적재돼 있고 윔블던·US오픈 이후가 비어 있다.

대응
----
tennis-data.co.uk 의 연도별 xlsx(ATP/WTA 본선 단식, 1차 소스와 동일한 '승자 관점'
세트 스코어)를 보조 소스로 받아 Sackmann 컬럼 스키마로 변환하고
`data/raw/{tour}/{tour}_matches_{year}_td.csv` 로 떨어뜨린다.
`build_db` 의 글롭(`{tour}_matches_*.csv`)이 그대로 집어가므로 적재 경로 변경은 없다.

식별자 매핑은 두 소스가 겹치는 구간(2023 ~ 2026-05)에서 학습한다:
  - **대회**: 결승 승자/패자 성(姓) + 서피스 + 개최일 근접 → `tourney_id` 링크.
    링크된 과거 시즌에서 대회명·`tourney_level`·`draw_size`·id 접미사·일자 보정을
    가져오므로 시리즈 집계(`champions.name`)와 tier 도출이 기존 행과 어긋나지 않는다.
  - **선수**: 링크된 대회 안에서 (세트 스코어, 양측 랭킹)이 일치하는 경기의
    승/패자 `player_id` 투표. 투표로 못 잡은 이름은 선수 마스터에서
    성+이니셜 후보를 뽑아 랭킹 근접도로 가린다.

학습 결과는 감사 가능하도록 `data/seed/td_{tournament,player}_map.csv` 에 기록한다.
`data/seed/td_player_overrides.csv` (tour,td_name,player_id) 가 있으면 최우선 적용.

보조 소스 한계 (적재 후에도 빈 칸)
  - 서브 스탯(ace/df/svpt…)·경기 시간·시드 없음 → `has_stats=0`, 시드/스탯바 미표시.
  - 타이브레이크 득점 없음 → 스코어보드에 `7-6` 까지만.

사용:
  python -m etl.td_supplement                 # 다운로드 + 학습 + 보강 CSV 생성
  python -m etl.td_supplement --offline       # 이미 받아둔 xlsx 로만
  python -m etl.td_supplement --year 2026
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# TD 의 xlsx 에 openpyxl 이 모르는 확장이 들어 있다 — 무해하지만 stderr 로 새어나가
# PowerShell(`$ErrorActionPreference='Stop'`) 에서 갱신 스크립트를 중단시킨다.
warnings.filterwarnings(
    "ignore", message="Unknown extension is not supported", category=UserWarning
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import RAW_DIR, SEED_DIR  # noqa: E402
from etl.build_db import canonical_name  # noqa: E402

TD_BASE = "http://tennis-data.co.uk/hrjk-85HytOjkhth76j_ygh4jf7"
SUPP_DIR = RAW_DIR / "supplement"

# 식별자(대회·선수) 매핑 학습 구간 시작 — WTA 등급 적재 시작 시즌(2021)과 맞춤.
LEARN_START = 2021
# 등급 교차검증 구간 시작 — ATP 500/250 체계 출범(2009). 대회 단위라 넓게 잡아도 가볍다.
TIER_START = 2009

TOURNEY_MAP_CSV = SEED_DIR / "td_tournament_map.csv"
PLAYER_MAP_CSV = SEED_DIR / "td_player_map.csv"
PLAYER_OVERRIDE_CSV = SEED_DIR / "td_player_overrides.csv"
TOURNEY_OVERRIDE_CSV = SEED_DIR / "td_tournament_overrides.csv"
TIER_SEED_CSV = SEED_DIR / "td_tournament_tiers.csv"

# TD Series/Tier 라벨 → 정규화 tier.
# GS·FINALS·마스터스는 derive_tier 가 시드보다 먼저 판정하므로 시드로 내보낼 필요가 없고,
# 흔들리는 건 등급(1000/500/250)뿐이다. 1차 소스의 level 코드는 연도별 승격/강등을
# 못 따라가므로(ATP_500_NAMES 고정셋, WTA 'P' 일괄 500 등) TD 라벨로 덮어쓴다.
TD_TIER_LABEL = {
    "Masters 1000": "1000", "ATP500": "500", "ATP250": "250",
    "WTA1000": "1000", "WTA500": "500", "WTA250": "250",
}
# 시드로 내보내지 않아도 되는(또는 적재 범위 밖인) 라벨 — 경고에서 제외.
#  GS·파이널스: derive_tier 가 시드보다 먼저 판정.
#  Premier/International/Tier*: 2021 이전 WTA 등급 체계 → 적재 범위 밖 (§2.2).
#  Masters/International Gold: 2009 이전 ATP 체계.
_TD_TIER_IGNORE = {
    "Grand Slam", "Masters Cup", "Tour Championships", "ATP Finals",
    "Premier", "Premier Mandatory", "Premier M", "Premier 5", "International",
    "International Gold", "Masters", "Tier I", "Tier II", "Tier III", "Tier IV",
    "WTA Elite Trophy", "Grand Slam Cup", "nan",
}

# 랭킹 근접도로 동명이인을 가릴 때 허용 오차 (초과 시 미해결로 남겨 오매핑 방지)
RANK_TOLERANCE = 40

# TD 라운드 → 결승으로부터의 깊이. 깊이 d 의 Sackmann 라운드 = _ROUND_BY_DEPTH[d].
# TD 는 대회 규모와 무관하게 '1st Round…'로만 적으므로, 결승에서 거꾸로 센 깊이로
# R128/R64/R32 를 가린다 (96 드로 마스터스의 1라운드 = R64 등).
_TD_ROUND_DEPTH = {
    "The Final": 0, "Semifinals": 1, "Quarterfinals": 2,
    "4th Round": 3, "3rd Round": 4, "2nd Round": 5, "1st Round": 6,
    "Round Robin": 99,
}
_ROUND_BY_DEPTH = {0: "F", 1: "SF", 2: "QF", 3: "R16", 4: "R32", 5: "R64",
                   6: "R128", 99: "RR"}

# 실제 쓰이는 드로 크기 — 경기 수(= draw-1)로 되짚어 draw_size 를 복원한다.
_DRAW_SIZES = (4, 8, 12, 16, 24, 28, 30, 32, 48, 56, 64, 96, 128)

# TD Comment → Sackmann score 접미사
_COMMENT_SUFFIX = {"Retired": "RET", "Walkover": "W/O", "Awarded": "DEF"}

# 출력 CSV 컬럼 (Sackmann atp_matches_*.csv 와 동일 순서)
OUT_COLS = [
    "tourney_id", "tourney_name", "surface", "draw_size", "tourney_level",
    "tourney_date", "match_num",
    "winner_id", "winner_seed", "winner_entry", "winner_name", "winner_hand",
    "winner_ht", "winner_ioc", "winner_age",
    "loser_id", "loser_seed", "loser_entry", "loser_name", "loser_hand",
    "loser_ht", "loser_ioc", "loser_age",
    "score", "best_of", "round", "minutes",
    "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon", "w_SvGms",
    "w_bpSaved", "w_bpFaced",
    "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon", "l_2ndWon", "l_SvGms",
    "l_bpSaved", "l_bpFaced",
    "winner_rank", "winner_rank_points", "loser_rank", "loser_rank_points",
]


# ───────────────────────── 이름 정규화 ─────────────────────────

def _norm(s: object) -> str:
    return re.sub(r"[^a-z]", "", str(s or "").lower())


_INITIAL_RE = re.compile(r"(?:[A-Za-z][-.]?){1,4}")


def td_parts(td_name: object) -> tuple[str, str]:
    """TD 표기 → (성, 이름 첫 이니셜).

    'De Minaur A.' → ('deminaur','a'),  'Varillas J. P.' → ('varillas','j')
    (이니셜 토큰이 여러 개면 모두 떼고 첫 글자만 쓴다.)
    """
    toks = str(td_name or "").strip().split()
    inits: list[str] = []
    while len(toks) > 1 and "." in toks[-1] and _INITIAL_RE.fullmatch(toks[-1]):
        inits.insert(0, toks.pop())
    return _norm(" ".join(toks)), _norm("".join(inits))[:1]


def sack_parts(full: object) -> tuple[str, str]:
    """Sackmann 표기 → (성, 이름 이니셜).  'Alex de Minaur' → ('deminaur','a')"""
    toks = str(full or "").split()
    if not toks:
        return "", ""
    return _norm(" ".join(toks[1:])), _norm(toks[0])[:1]


def name_compatible(td_name: object, sack_name: object, *,
                    check_initial: bool = True) -> bool:
    """성이 같은 계열이고 이니셜이 어긋나지 않으면 동일인 후보.

    `check_initial=False` 는 성만 본다. 두 소스가 쓰는 '이름'이 다른 경우
    (TD 'Osorio M.' = María Camila ↔ Sackmann 'Camila Osorio') 대응.
    """
    tl, ti = td_parts(td_name)
    sl, si = sack_parts(sack_name)
    if not tl or not sl:
        return False
    if check_initial and ti and si and ti != si:
        return False
    if tl == sl:
        return True
    # 복합 성 표기 차이: 'Mpetshi G.' ↔ 'Giovanni Mpetshi Perricard'
    long_, short = (sl, tl) if len(sl) >= len(tl) else (tl, sl)
    return len(short) >= 5 and (long_.startswith(short) or long_.endswith(short))


# ───────────────────────── 로딩 ─────────────────────────

def _fetch_one(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            data = resp.read()
    except Exception:  # noqa: BLE001
        return False
    dest.write_bytes(data)
    print(f"  ok   {dest.name}  ({len(data):,} B)")
    return True


def fetch(years: list[int], refresh_from: int | None = None) -> None:
    """연도별 파일 수신. 2012 이전 시즌은 .xls, 이후는 .xlsx 다.

    끝난 시즌 파일은 바뀌지 않으므로, 이미 받아둔 `refresh_from` 이전 연도는 건너뛴다
    (주간 갱신이 18개 시즌을 매번 다시 받지 않도록).
    """
    SUPP_DIR.mkdir(parents=True, exist_ok=True)
    if refresh_from is None:
        refresh_from = max(years) - 1
    for year in years:
        for tour, seg in (("atp", f"{year}"), ("wta", f"{year}w")):
            if year < refresh_from and _td_path(tour, year) is not None:
                continue
            got = False
            for ext in ("xlsx", "xls"):
                if _fetch_one(f"{TD_BASE}/{seg}/{year}.{ext}",
                              SUPP_DIR / f"td_{tour}_{year}.{ext}"):
                    got = True
                    break
            if not got:
                print(f"  miss td_{tour}_{year}  (xlsx/xls 모두 실패)")


def _td_path(tour: str, year: int) -> Path | None:
    for ext in ("xlsx", "xls"):
        fp = SUPP_DIR / f"td_{tour}_{year}.{ext}"
        if fp.exists():
            return fp
    return None


def _read_excel(fp: Path) -> pd.DataFrame:
    """엑셀 엔진을 확장자가 아니라 매직바이트로 고른다.

    tennis-data.co.uk 는 Apache MultiViews 라서 `.xlsx` 로 요청해도 구년도는
    레거시 `.xls`(OLE2) 본문을 내려준다 → 확장자만 믿으면 openpyxl 이 터진다.
    """
    head = fp.open("rb").read(4)
    engine = "xlrd" if head == b"\xd0\xcf\x11\xe0" else "openpyxl"
    return pd.read_excel(fp, engine=engine)


def load_td(tour: str, years: list[int]) -> pd.DataFrame:
    frames = []
    for year in years:
        fp = _td_path(tour, year)
        if fp is None:
            continue
        df = _read_excel(fp)
        df["season"] = year
        if "Series" not in df.columns:            # WTA 파일은 'Tier'
            df["Series"] = df.get("Tier")
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    td = pd.concat(frames, ignore_index=True)
    td["Date"] = pd.to_datetime(td["Date"])
    return td


def load_sack(tour: str, years: list[int]) -> pd.DataFrame:
    frames = []
    for year in years:
        fp = RAW_DIR / tour / f"{tour}_matches_{year}.csv"
        if fp.exists():
            frames.append(pd.read_csv(fp, low_memory=False))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["season"] = df.tourney_date.astype(str).str[:4].astype(int)
    return df


# ───────────────────────── 대회 링크 ─────────────────────────

def _sets_sig_sack(score: object) -> tuple:
    out = []
    for tok in str(score or "").split():
        m = re.fullmatch(r"(\d{1,2})-(\d{1,2})(?:\(\d{1,2}(?:-\d{1,2})?\))?", tok)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return tuple(out)


def _sets_sig_td(row: pd.Series, max_sets: int) -> tuple:
    out = []
    for i in range(1, max_sets + 1):
        wg, lg = row.get(f"W{i}"), row.get(f"L{i}")
        if pd.isna(wg) or pd.isna(lg):
            break
        out.append((int(wg), int(lg)))
    return tuple(out)


def link_tournaments(td: pd.DataFrame, sack: pd.DataFrame) -> tuple[dict, dict]:
    """(season, td_name) → tourney_id 링크와, td_name → 과거 시즌 프로필."""
    sack_t = (
        sack.groupby("tourney_id")
        .agg(name=("tourney_name", "first"), level=("tourney_level", "first"),
             surface=("surface", "first"), draw=("draw_size", "first"),
             date=("tourney_date", "first"), season=("season", "first"))
        .reset_index()
    )
    sack_t["dt"] = pd.to_datetime(sack_t.date.astype("int64").astype(str), format="%Y%m%d")
    finals = sack[sack["round"] == "F"]
    fin_map = {r.tourney_id: (r.winner_name, r.loser_name) for r in finals.itertuples()}

    links: dict[tuple[int, str], str] = {}
    profiles: dict[str, dict] = {}
    for (season, td_name), grp in td.groupby(["season", "Tournament"]):
        td_start = grp.Date.min()
        cands = sack_t[(sack_t.season == season) & (sack_t.surface == grp.Surface.iloc[0])]
        cands = cands[(cands.dt - td_start).abs() <= pd.Timedelta(days=10)]
        fin = grp[grp.Round == "The Final"]
        best, best_score = None, -1
        for c in cands.itertuples():
            score = 10 - abs((c.dt - td_start).days)
            wl = fin_map.get(c.tourney_id)
            if len(fin) and wl:
                score += 100 * name_compatible(fin.Winner.iloc[0], wl[0])
                score += 100 * name_compatible(fin.Loser.iloc[0], wl[1])
            if abs(len(grp) - ((c.draw or 0) - 1)) <= 8:
                score += 5
            if score > best_score:
                best, best_score = c, score
        if best is None or best_score < 100:
            continue
        links[(int(season), td_name)] = best.tourney_id
        prev = profiles.get(td_name)
        if prev is None or season >= prev["season"]:
            suffix = str(best.tourney_id).split("-", 1)[1]
            profiles[td_name] = {
                "season": int(season), "name": canonical_name(best.name),
                "level": best.level,
                "draw": int(best.draw) if pd.notna(best.draw) else None,
                "suffix": suffix,
                "date_offset": int((best.dt - td_start).days),
            }
    return links, profiles


def tier_seed_rows(tour: str, td: pd.DataFrame, sack: pd.DataFrame,
                   links: dict, profiles: dict) -> tuple[list[dict], set[str]]:
    """TD 등급 라벨 → (tour, season, name, tier) 시드 행. 미지의 라벨은 따로 반환."""
    name_of = {}
    if len(sack):
        name_of = {tid: canonical_name(g.tourney_name.iloc[0])
                   for tid, g in sack.groupby("tourney_id")}
    rows: list[dict] = []
    unknown: set[str] = set()
    for (season, td_name), grp in td.groupby(["season", "Tournament"]):
        label = str(grp["Series"].iloc[0])
        tier = TD_TIER_LABEL.get(label)
        if tier is None:
            if label not in _TD_TIER_IGNORE:
                unknown.add(f"{season} {td_name} = {label}")
            continue
        tid = links.get((int(season), td_name))
        name = name_of.get(tid) if tid else (profiles.get(td_name) or {}).get("name")
        if not name:
            continue
        rows.append({"tour": tour, "season": int(season), "name": name,
                     "tier": tier, "td_name": td_name})
    return rows, unknown


def load_tourney_overrides(tour: str) -> dict[str, dict]:
    """TD 대회명이 바뀌었거나 1차 소스에 전례가 없는 신설 대회 수동 프로필."""
    if not TOURNEY_OVERRIDE_CSV.exists():
        return {}
    df = pd.read_csv(TOURNEY_OVERRIDE_CSV)
    out: dict[str, dict] = {}
    for r in df[df.tour == tour].itertuples():
        out[str(r.td_name)] = {
            "season": 0, "name": canonical_name(str(r.name)),
            "level": str(r.level_raw), "suffix": str(r.tourney_suffix),
            "draw": int(r.draw_size) if pd.notna(r.draw_size) else None,
            "date_offset": int(r.date_offset) if pd.notna(r.date_offset) else 0,
        }
    return out


# ───────────────────────── 선수 링크 ─────────────────────────

def link_players(td: pd.DataFrame, sack: pd.DataFrame, links: dict,
                 max_sets: int) -> dict[str, int]:
    """겹치는 구간의 경기 대조로 TD 선수명 → player_id 투표."""
    sack_by_t = {tid: g for tid, g in sack.groupby("tourney_id")}
    votes: dict[str, Counter] = defaultdict(Counter)
    for (season, td_name), grp in td.groupby(["season", "Tournament"]):
        tid = links.get((int(season), td_name))
        sg = sack_by_t.get(tid) if tid else None
        if sg is None:
            continue
        index: dict[tuple, list] = defaultdict(list)
        for r in sg.itertuples():
            key = (_sets_sig_sack(r.score),
                   float(r.winner_rank) if pd.notna(r.winner_rank) else None,
                   float(r.loser_rank) if pd.notna(r.loser_rank) else None)
            index[key].append((r.winner_id, r.loser_id, r.winner_name, r.loser_name))
        for _, row in grp.iterrows():
            key = (_sets_sig_td(row, max_sets),
                   float(row.WRank) if pd.notna(row.WRank) else None,
                   float(row.LRank) if pd.notna(row.LRank) else None)
            hits = index.get(key, [])
            if len(hits) != 1:
                continue
            wid, lid, wname, lname = hits[0]
            # (세트 스코어, 양측 랭킹) 일치가 이미 강한 증거이므로 성(姓)만 확인한다.
            if name_compatible(row.Winner, wname, check_initial=False):
                votes[row.Winner][int(wid)] += 1
            if name_compatible(row.Loser, lname, check_initial=False):
                votes[row.Loser][int(lid)] += 1
    return {n: c.most_common(1)[0][0] for n, c in votes.items() if c}


def master_keys(name_first: object, name_last: object) -> set[tuple[str, str]]:
    """선수 마스터 (이름, 성) → TD 표기로 나올 수 있는 (성, 이니셜) 키 집합.

    - 복합 이름:  'Irina Camelia' + 'Begu'       → ('begu','i')
    - 복합 성:    'Maria Camila' + 'Osorio Serrano'
                  → ('osorioserrano','m'), ('osorio','m'), ('serrano','m')
    - 성/이름 역순 표기: 'Bu' + 'Yunchaokete'    → ('bu','y')
    """
    ft = str(name_first or "").split()
    lt = str(name_last or "").split()
    first, last = _norm(" ".join(ft)), _norm(" ".join(lt))
    keys = set()
    if first and last:
        keys.add((last, first[0]))
        keys.add((first, last[0]))    # 역순 표기
    if ft and lt:
        fi = _norm(ft[0])[:1]
        keys.add((_norm(lt[0]), fi))
        keys.add((_norm(lt[-1]), fi))
    return {k for k in keys if k[0] and k[1]}


def _best_ranks(tour: str) -> dict[int, int]:
    """선수별 최근 최고 랭킹 (동명이인 판별용). 20s + current 주간 랭킹 사용."""
    out: dict[int, int] = {}
    for fname in (f"{tour}_rankings_20s.csv", f"{tour}_rankings_current.csv"):
        fp = RAW_DIR / tour / fname
        if not fp.exists():
            continue
        df = pd.read_csv(fp, low_memory=False)
        for pid, rank in df.groupby("player")["rank"].min().items():
            pid = int(pid)
            if pid not in out or rank < out[pid]:
                out[pid] = int(rank)
    return out


def resolve_by_master(tour: str, names: list[str],
                      td_ranks: dict[str, list[float]]) -> tuple[dict[str, int], list[str]]:
    """투표로 못 잡은 이름: 선수 마스터 성+이니셜 후보 → 랭킹 근접도로 확정."""
    pm = RAW_DIR / tour / f"{tour}_players.csv"
    if not pm.exists():
        return {}, list(names)

    players = pd.read_csv(pm, low_memory=False)
    by_key: dict[tuple[str, str], list[int]] = defaultdict(list)
    for pid, nf, nl in zip(players.player_id, players.name_first, players.name_last):
        for key in master_keys(nf, nl):
            by_key[key].append(int(pid))

    best_rank = _best_ranks(tour)
    resolved: dict[str, int] = {}
    unresolved: list[str] = []
    for name in names:
        cands = list(dict.fromkeys(by_key.get(td_parts(name), [])))
        with_rank = [(pid, best_rank[pid]) for pid in cands if pid in best_rank]
        if len(cands) == 1:
            resolved[name] = cands[0]
        elif len(with_rank) == 1:
            resolved[name] = with_rank[0][0]
        elif with_rank and td_ranks.get(name):
            ref = min(td_ranks[name])
            pid, rank = min(with_rank, key=lambda r: abs(r[1] - ref))
            if abs(rank - ref) <= RANK_TOLERANCE:
                resolved[name] = pid
            else:
                unresolved.append(name)
        else:
            unresolved.append(name)
    return resolved, unresolved


def load_overrides() -> dict[tuple[str, str], int]:
    if not PLAYER_OVERRIDE_CSV.exists():
        return {}
    df = pd.read_csv(PLAYER_OVERRIDE_CSV)
    return {(str(r.tour), str(r.td_name)): int(r.player_id) for r in df.itertuples()}


# ───────────────────────── 보강 CSV 생성 ─────────────────────────

def _score_string(row: pd.Series, max_sets: int) -> str:
    sets = [f"{int(row[f'W{i}'])}-{int(row[f'L{i}'])}"
            for i in range(1, max_sets + 1)
            if not (pd.isna(row.get(f"W{i}")) or pd.isna(row.get(f"L{i}")))]
    suffix = _COMMENT_SUFFIX.get(str(row.get("Comment") or "").strip())
    if suffix == "W/O":
        return "W/O"
    return " ".join(sets + ([suffix] if suffix else [])).strip()


def emit(tour: str, year: int, td: pd.DataFrame, sack_year: pd.DataFrame,
         links: dict, profiles: dict, pmap: dict[str, int],
         player_meta: dict[int, tuple]) -> tuple[Path | None, dict]:
    """해당 시즌에서 1차 소스에 없는 대회만 Sackmann 스키마로 기록."""
    max_sets = 5 if tour == "atp" else 3
    existing_ids = set(sack_year.tourney_id.astype(str)) if len(sack_year) else set()
    cur = td[td.season == year]
    rows: list[dict] = []
    used_ids: set[str] = set()
    stats = {"tournaments": 0, "matches": 0, "skipped_rows": 0,
             "no_profile": [], "collision": [], "unmapped": Counter()}

    for td_name, grp in cur.groupby("Tournament", sort=False):
        if (year, td_name) in links:            # 1차 소스에 이미 있는 대회
            continue
        prof = profiles.get(td_name)
        if prof is None:
            stats["no_profile"].append(td_name)
            continue
        tourney_id = f"{year}-{prof['suffix']}"
        if tourney_id in existing_ids:
            continue
        if tourney_id in used_ids:               # 같은 시즌 내 접미사 충돌
            stats["collision"].append(f"{td_name}→{tourney_id}")
            continue
        used_ids.add(tourney_id)

        start = grp.Date.min() + timedelta(days=prof["date_offset"])
        ordered = grp.assign(
            _d=grp.Round.map(_TD_ROUND_DEPTH)
        ).dropna(subset=["_d"]).sort_values(["_d"], ascending=False, kind="stable")
        if ordered.empty:
            continue
        # TD 라운드 이름은 드로 크기를 담지 않는다 ('1st Round' 가 R32 일 수도, R128
        # 일 수도). 그 대회에 실제로 있는 라운드만 결승부터 0,1,2… 로 다시 센다.
        present = sorted({int(d) for d in ordered._d if d != 99})
        depth_of = {raw: i for i, raw in enumerate(present)}
        depth_of[99] = 99
        ordered = ordered.assign(_d=ordered._d.map(depth_of))
        # 라운드로빈 대회(투어 파이널스)는 경기 수로 드로를 되짚을 수 없다.
        draw = prof["draw"] if (ordered._d == 99).any() else \
            min(_DRAW_SIZES, key=lambda d: (abs(d - 1 - len(ordered)), d))

        n = 0
        for _, row in ordered.iterrows():
            depth = int(row["_d"])
            rnd = _ROUND_BY_DEPTH.get(depth)
            if rnd is None:
                continue
            wid, lid = pmap.get(row.Winner), pmap.get(row.Loser)
            if wid is None or lid is None:
                stats["skipped_rows"] += 1
                if wid is None:
                    stats["unmapped"][row.Winner] += 1
                if lid is None:
                    stats["unmapped"][row.Loser] += 1
                continue
            n += 1
            wmeta = player_meta.get(wid, (None, None, None))
            lmeta = player_meta.get(lid, (None, None, None))
            rows.append({
                "tourney_id": tourney_id,
                "tourney_name": prof["name"],
                "surface": row.Surface,
                "draw_size": draw,
                "tourney_level": prof["level"],
                "tourney_date": start.strftime("%Y%m%d"),
                "match_num": n,
                "winner_id": wid, "winner_name": wmeta[0],
                "winner_hand": wmeta[1], "winner_ioc": wmeta[2],
                "loser_id": lid, "loser_name": lmeta[0],
                "loser_hand": lmeta[1], "loser_ioc": lmeta[2],
                "score": _score_string(row, max_sets),
                "best_of": int(row["Best of"]) if pd.notna(row.get("Best of")) else None,
                "round": rnd,
                "winner_rank": int(row.WRank) if pd.notna(row.WRank) else None,
                "winner_rank_points": int(row.WPts) if pd.notna(row.WPts) else None,
                "loser_rank": int(row.LRank) if pd.notna(row.LRank) else None,
                "loser_rank_points": int(row.LPts) if pd.notna(row.LPts) else None,
            })
        if n:
            stats["tournaments"] += 1
            stats["matches"] += n

    out = RAW_DIR / tour / f"{tour}_matches_{year}_td.csv"
    if not rows:
        out.unlink(missing_ok=True)
        return None, stats
    pd.DataFrame(rows).reindex(columns=OUT_COLS).to_csv(out, index=False)
    return out, stats


def _player_meta(tour: str) -> dict[int, tuple]:
    fp = RAW_DIR / tour / f"{tour}_players.csv"
    if not fp.exists():
        return {}
    df = pd.read_csv(fp, low_memory=False)
    full = (df.name_first.fillna("").astype(str) + " "
            + df.name_last.fillna("").astype(str)).str.strip()
    return {int(p): (f, h if isinstance(h, str) else None,
                     i if isinstance(i, str) else None)
            for p, f, h, i in zip(df.player_id, full, df.hand, df.ioc)}


def run(years: list[int], target_years: list[int], offline: bool,
        tier_years: list[int] | None = None) -> None:
    """years: 식별자 학습 구간 / tier_years: 등급 교차검증 구간(보통 더 넓다)."""
    tier_years = sorted(set(tier_years or years) | set(years))
    if not offline:
        print(f"[td_supplement] 다운로드 {tier_years[0]}-{tier_years[-1]}")
        fetch(tier_years)

    tmap_rows, pmap_rows, tier_rows = [], [], []
    for tour in ("atp", "wta"):
        max_sets = 5 if tour == "atp" else 3
        td_all = load_td(tour, tier_years)
        if td_all.empty:
            print(f"[td_supplement] {tour}: 보조 xlsx 없음(스킵)")
            continue
        sack_all = load_sack(tour, tier_years)
        # 대회 링크는 등급 구간 전체(대회 단위라 가볍다), 선수 투표는 학습 구간만.
        links, profiles = link_tournaments(td_all, sack_all)
        overrides = load_tourney_overrides(tour)
        profiles.update(overrides)
        print(f"[td_supplement] {tour}: 대회 링크 {len(links)} / "
              f"프로필 {len(profiles)} (수동 {len(overrides)})")

        td = td_all[td_all.season.isin(years)]
        sack = sack_all[sack_all.season.isin(years)]
        pmap = link_players(td, sack, links, max_sets)
        all_names = sorted(set(td.Winner.dropna()) | set(td.Loser.dropna()))
        rest = [n for n in all_names if n not in pmap]
        td_ranks: dict[str, list[float]] = defaultdict(list)
        for _, r in td.iterrows():
            if pd.notna(r.WRank):
                td_ranks[r.Winner].append(float(r.WRank))
            if pd.notna(r.LRank):
                td_ranks[r.Loser].append(float(r.LRank))
        extra, unresolved = resolve_by_master(tour, rest, td_ranks)
        pmap.update(extra)
        ov = load_overrides()
        pmap.update({n: pid for (t, n), pid in ov.items() if t == tour})
        print(f"[td_supplement] {tour}: 선수 {len(pmap)}/{len(all_names)} "
              f"(투표 {len(pmap) - len(extra)} + 마스터 {len(extra)}) / 미해결 {len(unresolved)}")
        if unresolved:
            print("   미해결:", ", ".join(unresolved[:30]))

        rows, unknown = tier_seed_rows(tour, td_all, sack_all, links, profiles)
        tier_rows.extend(rows)
        print(f"[td_supplement] {tour}: 등급 시드 {len(rows)} 건")
        if unknown:
            print("   미지의 TD 등급 라벨:", "; ".join(sorted(unknown)[:10]))

        meta = _player_meta(tour)
        for name, pid in sorted(pmap.items()):
            pmap_rows.append({"tour": tour, "td_name": name, "player_id": pid,
                              "full_name": meta.get(pid, (None,))[0]})
        for td_name, prof in sorted(profiles.items()):
            tmap_rows.append({"tour": tour, "td_name": td_name, "name": prof["name"],
                              "tourney_suffix": prof["suffix"], "level_raw": prof["level"],
                              "draw_size": prof["draw"], "date_offset": prof["date_offset"],
                              "learned_from": prof["season"]})

        for year in target_years:
            sack_year = load_sack(tour, [year])
            out, st = emit(tour, year, td, sack_year, links, profiles, pmap, meta)
            msg = (f"[td_supplement] {tour} {year}: 보강 대회 {st['tournaments']} / "
                   f"경기 {st['matches']} / 선수 미매핑으로 제외 {st['skipped_rows']}")
            print(msg + (f" → {out.name}" if out else " (추가분 없음)"))
            if st["no_profile"]:
                print("   프로필 없는 대회:", ", ".join(st["no_profile"]))
            if st["collision"]:
                print("   id 충돌로 제외:", ", ".join(st["collision"]))
            if st["unmapped"]:
                print("   제외 선수:", ", ".join(f"{n}({c})" for n, c in
                                              st["unmapped"].most_common(20)))

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    if tmap_rows:
        pd.DataFrame(tmap_rows).to_csv(TOURNEY_MAP_CSV, index=False)
        print(f"[td_supplement] 대회 매핑 → {TOURNEY_MAP_CSV}")
    if pmap_rows:
        pd.DataFrame(pmap_rows).to_csv(PLAYER_MAP_CSV, index=False)
        print(f"[td_supplement] 선수 매핑 → {PLAYER_MAP_CSV}")
    if tier_rows:
        df = pd.DataFrame(tier_rows).drop_duplicates(["tour", "season", "name"])
        df.sort_values(["tour", "season", "name"]).to_csv(TIER_SEED_CSV, index=False)
        print(f"[td_supplement] 등급 시드 → {TIER_SEED_CSV}")


if __name__ == "__main__":
    this_year = datetime.now().year
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=LEARN_START, help="식별자 학습 시작 시즌")
    ap.add_argument("--end", type=int, default=this_year, help="학습/수신 종료 시즌")
    ap.add_argument("--tier-start", type=int, default=TIER_START,
                    help="등급 교차검증 시작 시즌 (ATP 500/250 체계 출범 = 2009)")
    ap.add_argument("--year", type=int, action="append",
                    help="보강 CSV 를 만들 시즌 (기본: 올해)")
    ap.add_argument("--offline", action="store_true", help="다운로드 생략")
    args = ap.parse_args()
    run(
        years=list(range(args.start, args.end + 1)),
        target_years=args.year or [this_year],
        offline=args.offline,
        tier_years=list(range(args.tier_start, args.end + 1)),
    )

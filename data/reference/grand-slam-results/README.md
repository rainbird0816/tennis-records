# 연도별 그랜드슬램 성적표 (레퍼런스)

선수 상세 페이지(`/player/:tour/:playerId`)에 들어갈 **연도별 그랜드슬램 표**
(performance timeline)의 레퍼런스 데이터를 모아두는 폴더입니다.

## 대상 선수

그랜드슬램에서 **16강(R16) 이상 진출 기록이 1회라도 있는 선수**.
(DB 기준: `tier='GS'` 매치에서 `round_order >= 4`)

> 자격 선수 수: ATP 약 694명 · WTA 약 656명.

## 표 형태

- 가로(열): 4개 그랜드슬램 — **호주오픈 · 롤랑가로 · 윔블던 · US오픈** (개최 시기순)
- 세로(행): 연도(내림차순 권장)
- 셀: 그 해 해당 대회에서 **도달한 라운드 코드**

### 셀 코드

| 코드 | 의미 |
|------|------|
| `W`  | 우승 |
| `F`  | 준우승(결승 패) |
| `SF` | 4강 |
| `QF` | 8강 |
| `4R` | 16강 (R16) |
| `3R` | 32강 (R32) |
| `2R` | 64강 (R64) |
| `1R` | 128강 (R128, 1회전 탈락) |
| `A`  | 불참 (해당 연도 데이터 없음) — 표에서 빈칸/A 로 처리 |
| `NH` | 미개최 (Not Held) |

`A`/`NH` 는 생성물에 포함하지 않습니다. 표 렌더 시 해당 (연도, 대회)
키가 `results` 에 없으면 불참/미개최로 간주해 빈칸 처리하세요.

## 파일 구조

```
data/reference/grand-slam-results/
├─ README.md          ← 이 문서
├─ atp/{player_id}.json
└─ wta/{player_id}.json
```

`player_id` 는 `(tour, player_id)` 복합키의 player_id 입니다 (ATP/WTA 충돌 주의).

## JSON 스키마

```jsonc
{
  "tour": "atp",
  "player_id": 104925,
  "full_name": "Novak Djokovic",
  "ioc": "SRB",
  "slams": ["Australian Open", "Roland Garros", "Wimbledon", "US Open"],
  "results": {
    "2008": { "Australian Open": "W",  "Roland Garros": "SF", "Wimbledon": "2R", "US Open": "SF" },
    "2011": { "Australian Open": "W",  "Roland Garros": "SF", "Wimbledon": "W",  "US Open": "W"  }
    // ... 출전한 연도만 (불참 연도는 생략)
  }
}
```

## 생성 방법

`scripts/gen_gs_reference.py` 가 `tennis.db` 에서 위 형식대로 추출합니다.

```bash
python scripts/gen_gs_reference.py --name "Djokovic"   # 이름 부분일치
python scripts/gen_gs_reference.py --tour atp --id 104925
python scripts/gen_gs_reference.py --all               # 자격 선수 전체(약 1,350개)
```

> 셀 코드는 그 대회·연도에서 선수의 **가장 깊은 라운드 매치**로 산출합니다
> (결승 승리 → `W`, 그 외 → 탈락한 라운드 코드).

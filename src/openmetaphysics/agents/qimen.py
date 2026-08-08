"""奇门遁甲 — 时家奇门九宫排盘 (转盘法).

Phase 5 核心实现。全部为纯函数、确定性计算: 无 I/O、无系统时钟、无随机、无 LLM。
相同输入 ⇒ 字节级相同输出。

算法流派约定 (implementation assumptions — 项目无既有规范, 均按通行转盘法,
在注释与交付报告中明确记录, 不作为 normative contract):

1. 三元: 沿用项目既有简化规则 —— 公历日号 1-10 → 上元 (+0), 11-20 → 中元
   (+3), 21-30 → 下元 (+6)。为拆补法按日近似的简化; 未实现超神接气/置闰法。
2. 局数: ju = ((节气基本局 - 1) + 三元偏移) % 9 + 1。基本局 = 节气在
   阳遁/阴遁序列中的序号 (冬至→阳遁一局, 夏至→阴遁一局)。
3. 地盘: 阳遁顺布、阴遁逆布 六仪三奇 (戊己庚辛壬癸丁丙乙)。
   阳遁 n 局甲子戊在 n 宫; 阴遁 n 局甲子戊在 (10 - n) 宫。
4. 值符: 值符星 = 旬首六仪所在地盘宫之九星 (甲子→戊、甲戌→己 … 甲寅→癸);
   值符随时干: 时干所在地盘宫 = 值符落宫; 天盘 = 地盘按
   (时干宫 - 旬首宫) mod 9 偏移顺转 (值符星带着旬首仪飞到时干宫)。
5. 值使: 值使门 = 旬首宫地盘八门, 值使随时支: 从本宫起, 阳遁顺行/阴遁逆行,
   步数 = (时支序 - 旬首支序) mod 12。
6. 八神: 值符神随值符落宫, 顺时针顺布, 跳过中宫。
7. 八门: 值使落宫后, 其余门按洛书宫序顺布, 跳过中宫。
8. 空亡: 时柱旬空二支 → 对应宫位 (坎子 / 艮丑寅 / 震卯 / 巽辰巳 / 离午 /
   坤未申 / 兑酉 / 乾戌亥)。
9. 中宫寄坤二宫: 值符/值使落中宫时寄坤二宫; 九星天禽参与转盘 (简化, 不寄宫)。
10. 真太阳时: 提供 born_location 时, 用真太阳时 (core.solar_time) 确定时辰
    (时支); 日期与日干支仍用钟表日。
11. 晚子时 (23:00-24:00) 不换日柱。

盘面语义 (与 docs/SCHEMAS.md §3.3 一致, 不修改 Schema):
- earth_plate = 地盘干 (局数所布六仪三奇)
- sky_plate   = 天盘干 (随值符顺转后的六仪三奇)
- nine_stars / eight_doors / eight_gods = 转盘后的最终盘面
- three_qi    = 天盘干中落在乙/丙/丁三奇的宫位
- is_void     = 时柱旬空对应宫位
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..core.calendar import sexagenary_day_index, solar_term_time
from ..core.engines import BaseAgent, DeterministicEngine
from ..core.models import EARTHLY_BRANCHES, HEAVENLY_STEMS, SOLAR_TERMS_24
from ..core.schemas import AgentInput, AgentOutput
from ..core.solar_time import true_solar_time

# 后天八卦 宫位 1..9 对应宫名 (洛书顺序)
PALACE_NAMES_9 = {
    1: "坎",
    2: "坤",
    3: "震",
    4: "巽",
    5: "中宫",
    6: "乾",
    7: "兑",
    8: "艮",
    9: "离",
}

# 八神 (顺时针顺布)
EIGHT_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
# 九星 (地盘固定, 天盘随值符顺转)
NINE_STARS = {
    1: "天蓬",
    2: "天芮",
    3: "天冲",
    4: "天辅",
    5: "天禽",
    6: "天心",
    7: "天柱",
    8: "天任",
    9: "天英",
}
# 八门 (地盘固定, 天盘随值使顺布; 中宫不开门)
EIGHT_DOORS = {
    1: "休门",
    2: "死门",
    3: "伤门",
    4: "杜门",
    5: None,  # 中宫不开门
    6: "开门",
    7: "惊门",
    8: "生门",
    9: "景门",
}
# 六仪 (六甲旬)
LIUYI = ["戊", "己", "庚", "辛", "壬", "癸"]
# 三奇
SANQI = ["乙", "丙", "丁"]
# 六甲 隐于六仪
LIUJIA = [
    ("甲子", "戊"),
    ("甲戌", "己"),
    ("甲申", "庚"),
    ("甲午", "辛"),
    ("甲辰", "壬"),
    ("甲寅", "癸"),
]

# 八门/八神只布八宫 (跳过中宫), 洛书宫序
DOOR_PALACES = [1, 2, 3, 4, 6, 7, 8, 9]

# 地支 → 宫位 (后天八卦配支; 中宫无支)
PALACE_BRANCHES = {
    1: [0],  # 坎: 子
    2: [7, 8],  # 坤: 未申
    3: [3],  # 震: 卯
    4: [4, 5],  # 巽: 辰巳
    6: [10, 11],  # 乾: 戌亥
    7: [9],  # 兑: 酉
    8: [1, 2],  # 艮: 丑寅
    9: [6],  # 离: 午
}


def branch_to_palace(branch_index: int) -> int:
    """地支序 (子=0 .. 亥=11) → 宫位 (1..9)."""
    for palace, branches in PALACE_BRANCHES.items():
        if branch_index in branches:
            return palace
    raise ValueError(f"no palace for branch index {branch_index}")


# 节气三元: 每个节气分 上元/中元/下元 → 局数偏移
# 上元: 日号 1-10 → 偏移 0
# 中元: 日号 11-20 → 偏移 3
# 下元: 日号 21-30 → 偏移 6
# (拆补法按日近似的简化; 见模块 docstring 约定 1)
def ju_from_day_of_month(day: int) -> int:
    """Return base ju offset (0-8) from day in month."""
    if 1 <= day <= 10:
        return 0
    elif 11 <= day <= 20:
        return 3
    else:  # 21-30
        return 6


class QimenInput(AgentInput):
    """奇门遁甲排盘输入。默认使用时家奇门：排盘时间 = 问卦时间。"""

    pass


class QimenCell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    palace: int = Field(ge=1, le=9)  # 1..9 洛书宫位
    name: str  # 坎/坤/...
    sky_plate: str | None = None  # 天盘干 (随值符顺转)
    earth_plate: str | None = None  # 地盘干 (局数所布六仪三奇)
    eight_gods: str | None = None  # 八神
    nine_stars: str | None = None  # 九星 (天盘)
    eight_doors: str | None = None  # 八门 (天盘)
    three_qi: str | None = None  # 三奇 (乙丙丁) 天盘落宫
    is_void: bool = False  # 空亡
    is_central: bool = False  # 中宫


class QimenBoard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    solar_term: str | None = None
    ju: int = Field(ge=1, le=9)  # 局数 1..9
    dun_type: Literal["yang", "yin"]  # 阳遁/阴遁
    day_of_month: int
    triple_offset: int  # 三元偏移 0/3/6
    cells: list[QimenCell]  # 9 宫格


class QimenOutput(AgentOutput):
    agent: str = "qimen"
    result: QimenBoard


# 地盘八卦顺序: 坎1 坤2 震3 巽4 中5 乾6 兑7 艮8 离9
# 节气顺序: 冬至 → 小寒 → 大寒 → 立春 → ... → 大雪
# 阳遁: 冬至(一) → 芒种(十二) → 夏至前 → 阴遁开始
# 阴遁: 夏至(一) → 大雪(十二) → 冬至前 → 阳遁开始

SOLAR_TERMS_YANGDUN = [
    "冬至",
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
]
SOLAR_TERMS_YINDUN = [
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
]
JU_PER_TERM_YANG = {term: i + 1 for i, term in enumerate(SOLAR_TERMS_YANGDUN)}
JU_PER_TERM_YIN = {term: i + 1 for i, term in enumerate(SOLAR_TERMS_YINDUN)}


def dun_type_and_base_ju(
    utc_dt: datetime.datetime,
) -> tuple[Literal["yang", "yin"], int, str]:
    """Determine 阳遁/阴遁, base ju and governing solar term from datetime.

    阳遁: 冬至(含) → 夏至前
    阴遁: 夏至(含) → 冬至前
    Base ju is the position of the governing solar term in its 遁 sequence.

    扫描前一年与当年的全部 24 节气, 取最后一个不晚于输入的时刻
    (修复: 每年 1 月 1 日 ~ 小寒 前无当年节气可取的越界问题)。
    """
    y = utc_dt.astimezone(datetime.timezone.utc).year
    terms: list[tuple[str, datetime.datetime]] = []
    for yy in (y - 1, y):
        for name, _is_jie, lon in SOLAR_TERMS_24:
            terms.append((name, solar_term_time(yy, lon)))
    terms.sort(key=lambda x: x[1])

    current_term = terms[0][0]
    for name, t in terms:
        if t <= utc_dt:
            current_term = name

    if current_term in JU_PER_TERM_YANG:
        return "yang", JU_PER_TERM_YANG[current_term], current_term
    return "yin", JU_PER_TERM_YIN[current_term], current_term


# ---------------------------------------------------------------------------
# 干支基础 (时家奇门)
# ---------------------------------------------------------------------------
def hour_branch_index(hour: int) -> int:
    """小时 → 地支序 (子=0): 23-00 子, 01-02 丑, ..., 21-22 亥."""
    return ((hour + 1) // 2) % 12


def sexagenary_hour_index(day_stem_index: int, hour_branch_index: int) -> int:
    """时干支序 (0..59): 五鼠遁 日上起时.

    甲己日 甲子时起 / 乙庚日 丙子时起 / 丙辛日 戊子时起 /
    丁壬日 庚子时起 / 戊癸日 壬子时起。
    """
    start = (day_stem_index % 5) * 2  # 甲(0) 丙(2) 戊(4) 庚(6) 壬(8)
    stem = (start + hour_branch_index) % 10
    for k in range(stem, 60, 10):
        if k % 12 == hour_branch_index:
            return k
    raise ValueError(f"no sexagenary hour for stem {stem} branch {hour_branch_index}")


def xun_shou_liuyi(sexagenary_index: int) -> str:
    """时干支所属六甲旬首所遁之六仪 (甲子→戊 ... 甲寅→癸)."""
    return LIUYI[sexagenary_index // 10]


def xun_shou_branch(sexagenary_index: int) -> int:
    """旬首之地支序 (子=0)."""
    return ((sexagenary_index // 10) * 10) % 12


def void_branch_indices(sexagenary_index: int) -> tuple[int, int]:
    """时柱旬空之二支序 (甲子旬→戌亥, 甲戌旬→申酉, ...)."""
    shou = (sexagenary_index // 10) * 10
    return (shou - 2) % 12, (shou - 1) % 12


# ---------------------------------------------------------------------------
# 地盘 / 天盘
# ---------------------------------------------------------------------------
def earth_placement(dun_type: Literal["yang", "yin"], ju: int) -> dict[int, str]:
    """地盘六仪三奇: palace(1..9) -> 干.

    阳遁顺布: 甲子戊在 ju 宫, 依次顺行。
    阴遁逆布: 甲子戊在 (10 - ju) 宫, 依次逆行。
    """
    order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    if dun_type == "yang":
        start, step = ju - 1, 1
    else:
        start, step = (9 - ju) % 9, -1
    out: dict[int, str] = {}
    for i, stem in enumerate(order):
        out[(start + step * i) % 9 + 1] = stem
    return out


@dataclass(frozen=True)
class HourPlan:
    """时家奇门的一时之盘摘要 (供 trace 与测试)."""

    hour_index: int  # 时干支序 0..59
    hour_stem: str  # 时干
    hour_branch: str  # 时支
    xun_name: str  # 六甲旬名 (甲子 ... 甲寅)
    xun_palace: int  # 旬首六仪所在地盘宫 (1..9)
    hour_stem_palace: int  # 时干所在地盘宫 (值符落宫, 可能为中宫)
    zhi_fu_star: str  # 值符星
    zhi_fu_palace: int  # 值符神起布宫 (落中宫时寄坤二宫)
    zhi_shi_door: str  # 值使门
    zhi_shi_palace: int  # 值使落宫
    void_palaces: list[int]  # 空亡宫位
    offset: int  # 天盘顺转偏移 (0..8)


def build_palaces(
    dun_type: Literal["yang", "yin"],
    base_ju: int,
    local_date: datetime.date,
    hour: int,
) -> tuple[list[QimenCell], int, int, HourPlan]:
    """Build the full 9-palace Qimen board with all placements (时家转盘法).

    流程: 三元偏移 → 局数 → 地盘 → 时干支/旬首 → 值符/值使 →
    天盘顺转 → 八神/八门 → 空亡 → 完整九宫。
    """
    triple_offset = ju_from_day_of_month(local_date.day)
    ju = ((base_ju - 1) + triple_offset) % 9 + 1
    earth = earth_placement(dun_type, ju)

    # 时干支 (五鼠遁)
    day_stem_index = sexagenary_day_index(local_date.year, local_date.month, local_date.day) % 10
    hb = hour_branch_index(hour)
    hour_index = sexagenary_hour_index(day_stem_index, hb)

    # 旬首
    xun_liuyi = xun_shou_liuyi(hour_index)
    xun_name, _ = LIUJIA[hour_index // 10]
    xun_palace = next(p for p, s in earth.items() if s == xun_liuyi)
    xun_branch = xun_shou_branch(hour_index)

    # 值符: 随时干; 时干为甲时以其遁藏之旬首仪取宫
    hour_stem = HEAVENLY_STEMS[hour_index % 10]
    hour_stem_palace = next((p for p, s in earth.items() if s == hour_stem), xun_palace)
    zhi_fu_star = NINE_STARS[xun_palace]
    zhi_fu_palace = hour_stem_palace if hour_stem_palace != 5 else 2  # 中宫寄坤二

    # 天盘: 顺转 offset = (时干宫 - 旬首宫) mod 9
    offset = (hour_stem_palace - xun_palace) % 9
    sky_gan = {p: earth[((p - 1) - offset) % 9 + 1] for p in range(1, 10)}
    sky_star = {p: NINE_STARS[((p - 1) - offset) % 9 + 1] for p in range(1, 10)}

    # 值使: 随时支; 从本宫起 阳遁顺行/阴遁逆行
    home = xun_palace if xun_palace != 5 else 2  # 旬首在中宫时寄坤二宫取门
    zhi_shi_door = EIGHT_DOORS[home]
    steps = (hb - xun_branch) % 12
    if dun_type == "yang":
        zhi_shi_palace = ((home - 1) + steps) % 9 + 1
    else:
        zhi_shi_palace = ((home - 1) - steps) % 9 + 1
    if zhi_shi_palace == 5:
        zhi_shi_palace = 2  # 值使落中宫 → 寄坤二宫

    # 八门: 值使落宫后其余门按洛书宫序顺布 (跳过中宫)
    door_offset = (DOOR_PALACES.index(zhi_shi_palace) - DOOR_PALACES.index(home)) % 8
    doors: dict[int, str | None] = {5: None}
    for p in DOOR_PALACES:
        src = DOOR_PALACES[(DOOR_PALACES.index(p) - door_offset) % 8]
        doors[p] = EIGHT_DOORS[src]

    # 八神: 值符神随值符落宫顺布 (跳过中宫)
    gods: dict[int, str] = {}
    god_start = DOOR_PALACES.index(zhi_fu_palace)
    for i, god in enumerate(EIGHT_GODS):
        gods[DOOR_PALACES[(god_start + i) % 8]] = god

    # 空亡: 时柱旬空二支 → 宫位
    void_palaces = sorted({branch_to_palace(b) for b in void_branch_indices(hour_index)})

    cells: list[QimenCell] = []
    for p in range(1, 10):
        gan = sky_gan[p]
        cells.append(
            QimenCell(
                palace=p,
                name=PALACE_NAMES_9[p],
                sky_plate=gan,
                earth_plate=earth[p],
                eight_gods=gods.get(p),
                nine_stars=sky_star[p],
                eight_doors=doors[p],
                three_qi=gan if gan in SANQI else None,
                is_void=p in void_palaces,
                is_central=(p == 5),
            )
        )

    plan = HourPlan(
        hour_index=hour_index,
        hour_stem=hour_stem,
        hour_branch=EARTHLY_BRANCHES[hb],
        xun_name=xun_name,
        xun_palace=xun_palace,
        hour_stem_palace=hour_stem_palace,
        zhi_fu_star=zhi_fu_star,
        zhi_fu_palace=zhi_fu_palace,
        zhi_shi_door=zhi_shi_door,
        zhi_shi_palace=zhi_shi_palace,
        void_palaces=void_palaces,
        offset=offset,
    )
    return cells, ju, triple_offset, plan


def effective_hour(payload: QimenInput) -> int:
    """时辰用真太阳时 (有坐标时), 否则用钟表时."""
    loc = payload.born_location
    if loc is not None:
        return true_solar_time(payload.born_at, loc.longitude)["true_solar_time"].hour
    return payload.born_at.hour


class QimenEngine(DeterministicEngine):
    version = "0.3.0"

    def calculate(self, payload: QimenInput) -> dict[str, Any]:
        born = payload.born_at
        utc = born.astimezone(datetime.timezone.utc)
        dun_type, base_ju, term_name = dun_type_and_base_ju(utc)

        hour = effective_hour(payload)
        cells, ju, triple_offset, plan = build_palaces(dun_type, base_ju, born.date(), hour)

        self.trace.record(
            "qimen.dun_type",
            "阳遁/阴遁 from 冬至/夏至 boundary",
            outputs={"dun_type": dun_type, "base_ju": base_ju, "solar_term": term_name},
        )
        self.trace.record(
            "qimen.ju",
            "局数 from 节气三元",
            outputs={"ju": ju, "triple_offset": triple_offset, "day_of_month": born.day},
        )
        self.trace.record(
            "qimen.zhifu",
            "值符随时干 (天盘顺转)",
            outputs={
                "zhi_fu_star": plan.zhi_fu_star,
                "zhi_fu_palace": plan.zhi_fu_palace,
                "xun": plan.xun_name,
                "offset": plan.offset,
            },
        )
        self.trace.record(
            "qimen.zhishi",
            "值使随时支",
            outputs={
                "zhi_shi_door": plan.zhi_shi_door,
                "zhi_shi_palace": plan.zhi_shi_palace,
            },
        )
        self.trace.record(
            "qimen.void",
            "时柱旬空",
            outputs={"void_palaces": ",".join(str(p) for p in plan.void_palaces)},
        )

        board = QimenBoard(
            solar_term=term_name,
            ju=ju,
            dun_type=dun_type,
            day_of_month=born.day,
            triple_offset=triple_offset,
            cells=cells,
        )
        return board.model_dump(mode="json")


class QimenAgent(BaseAgent):
    name = "qimen"
    engine_version = QimenEngine.version
    input_schema = QimenInput
    output_schema = QimenOutput
    engine = QimenEngine()

    def _compute_result(self, payload: QimenInput) -> dict[str, Any]:
        return self.engine.calculate(payload)

    def _metadata(self) -> dict[str, str | int | float | bool]:
        return {
            "engine_version": self.engine_version,
            "deterministic": True,
            "placement": "full_shibapan",
            "method": "zhuanpan",
            "has_nine_stars": True,
            "has_eight_doors": True,
            "has_eight_gods": True,
        }

    def _explain_fallback(self, output: QimenOutput, *, style: str = "concise") -> str:
        r = output.result
        type_cn = "阳遁" if r.dun_type == "yang" else "阴遁"
        return f"[奇门] {type_cn} {r.ju}局 节气: {r.solar_term} 共 {len(r.cells)} 宫"

from __future__ import annotations

import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..core.calendar import month_boundary_before, solar_term_time
from ..core.engines import BaseAgent, DeterministicEngine
from ..core.schemas import AgentInput, AgentOutput

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

# 八神 (顺行排盘)
EIGHT_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
# 九星 (地盘固定)
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
# 八门 (地盘固定)
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


# 节气三元: 每个节气分 上元/中元/下元 → 局数
# 上元: 1-10 日 → 阴/阳 局+0
# 中元: 11-20 日 → 阴/阳 局+3
# 下元: 21-30 日 → 阴/阳 局+6
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
    sky_plate: str | None = None  # 天盘 (天干/六甲)
    earth_plate: str | None = None  # 地盘 (九星/八门)
    eight_gods: str | None = None  # 八神
    nine_stars: str | None = None  # 九星
    eight_doors: str | None = None  # 八门
    three_qi: str | None = None  # 三奇 (乙丙丁) if present
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
# 阳遁: 冬至(一) → 惊蛰(二) → ... → 夏至前 → 阴遁开始
# 阴遁: 夏至(一) → 立秋(二) → ... → 冬至前 → 阳遁开始
# 阳遁顺排六仪，阴遁逆排

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


def dun_type_and_base_ju(utc_dt: datetime.datetime) -> tuple[Literal["yang", "yin"], int]:
    """Determine 阳遁/阴遁 and base ju from datetime.

    阳遁: 冬至(含) → 次年夏至前
    阴遁: 夏至(含) → 冬至前
    Base ju is from the current solar term.
    """
    y = utc_dt.astimezone(datetime.timezone.utc).year
    from openmetaphysics.core.models import SOLAR_TERMS_24

    terms = []
    for name, _, lon in SOLAR_TERMS_24:
        terms.append((name, solar_term_time(y, lon)))

    sorted_terms = sorted(terms, key=lambda x: x[1])
    current_term = None
    for name, t in reversed(sorted_terms):
        if t <= utc_dt:
            current_term = name
            break

    if current_term in JU_PER_TERM_YANG:
        return "yang", JU_PER_TERM_YANG[current_term]
    else:
        return "yin", JU_PER_TERM_YIN[current_term]


def build_palaces(
    dun_type: Literal["yang", "yin"], base_ju: int, day_of_month: int
) -> tuple[list[QimenCell], int, int]:
    """Build the full 9-palace Qimen board with all placements.

    Algorithm (时家奇门 转盘法):
    1. 地盘九星/八门 fixed by 宫位
    2. 局数 determines where 甲子戊 starts
    3. 阳遁顺排六仪+三奇，阴遁逆排
    4. 值符八神 starting from 甲子戊 palace
    """
    triple_offset = ju_from_day_of_month(day_of_month)
    ju = ((base_ju - 1) + triple_offset) % 9 + 1

    # palace index 0..8 maps to 1..9
    palaces: list[QimenCell] = []
    for p_idx in range(9):
        palace_num = p_idx + 1
        cell = QimenCell(
            palace=palace_num,
            name=PALACE_NAMES_9[palace_num],
            nine_stars=NINE_STARS[palace_num],
            eight_doors=EIGHT_DOORS[palace_num],
            is_central=(palace_num == 5),
        )
        palaces.append(cell)

    # Find start position for 甲子戊 based on ju
    # 阳遁: first palace from 坎一宫开始，corresponding to ju steps
    start_idx = ju - 1  # 0-based index
    order = list(range(9))  # 0..8 palace indices

    if dun_type == "yin":
        # reverse order for yin dun
        order = list(reversed(order))

    # Place 戊己庚辛壬癸丁丙乙
    placement_order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    for i, tian_gan in enumerate(placement_order):
        p_idx = (start_idx + order[i]) % 9
        palaces[p_idx].sky_plate = tian_gan
        if tian_gan in SANQI:
            palaces[p_idx].three_qi = tian_gan

    # 八神: 值符 starts at 甲子戊 palace, then clockwise
    zhi_fu_palace_idx = start_idx
    for g_idx, god in enumerate(EIGHT_GODS):
        p_idx = (zhi_fu_palace_idx + g_idx) % 9
        palaces[p_idx].eight_gods = god

    return palaces, ju, triple_offset


class QimenEngine(DeterministicEngine):
    version = "0.2.0"

    def calculate(self, payload: QimenInput) -> dict[str, Any]:
        born = payload.born_at
        utc = born.astimezone(datetime.timezone.utc)
        _, term_name, _ = month_boundary_before(born)

        dun_type, base_ju = dun_type_and_base_ju(utc)
        day_of_month = utc.day
        cells, ju, triple_offset = build_palaces(dun_type, base_ju, day_of_month)

        self.trace.record(
            "qimen.dun_type",
            "阳遁/阴遁 from 冬至/夏至 boundary",
            outputs={"dun_type": dun_type, "base_ju": base_ju, "solar_term": term_name},
        )
        self.trace.record(
            "qimen.ju",
            "局数 from 节气三元",
            outputs={"ju": ju, "triple_offset": triple_offset, "day_of_month": day_of_month},
        )

        board = QimenBoard(
            solar_term=term_name,
            ju=ju,
            dun_type=dun_type,
            day_of_month=day_of_month,
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
            "has_nine_stars": True,
            "has_eight_doors": True,
            "has_eight_gods": True,
        }

    def _explain_fallback(self, output: QimenOutput, *, style: str = "concise") -> str:
        r = output.result
        type_cn = "阳遁" if r.dun_type == "yang" else "阴遁"
        return f"[奇门] {type_cn} {r.ju}局 节气: {r.solar_term} 共 {len(r.cells)} 宫"

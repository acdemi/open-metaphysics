# Reference Qimen CHANGELOG

> 记录 reference/qimen 实现的修改（Phase 5.7 起）。
> 任何修改必须保持与 24 规范向量完全一致（`reference/tests/test_golden_vectors.py`）。

## 2026-08-09 — Phase 5.7 Alignment Sprint

### Added
- `astronomy.py`：天文/干支基础自包含移植（Meeus 同源算法，与 core 共享基础
  行为一致）。目的：使 Reference 实现完全独立于 `src/openmetaphysics`，
  满足对齐 Sprint 的独立性要求（Task F 独立实现声明）。

### Changed
- `domain.py`：移除对 `src/openmetaphysics/core/*` 的导入，改用
  `astronomy.py`（`solar_term_time` / `sexagenary_day_index` /
  `HEAVENLY_STEMS` / `SOLAR_TERMS_24` / 真太阳时）。
  行为零变化：24/24 向量逐字节一致（移植前后均验证）。

### Fixed
- 无（未发现 Reference bug）。

### Ambiguity Notes
- 无契约澄清需求。

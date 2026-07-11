开始 Phase 5。

本阶段目标：

实现高精度真太阳时（True Solar Time）计算模块。

注意：

不要使用 LLM。

不要使用 Prompt。

全部采用确定性算法。

---

功能要求：

支持：

1、中国所有地区经纬度

2、UTC 转换

3、地方平太阳时

4、均时差（Equation of Time）

5、真太阳时

6、夏令时兼容（可关闭）

输出：

`json
{
  "utc_time": "",
  "local_mean_time": "",
  "equation_of_time": "",
  "true_solar_time": "",
  "longitude_offset": "",
  "metadata": {}
}
`

---

要求：

所有计算必须可重复。

所有计算必须保留 Trace。

所有计算必须编写单元测试。

---

设计要求：

新增模块：

core/solar_time.py

不得修改：

- Bazi Engine
- Ziwei Engine
- Consensus Engine

除非确实需要接口扩展。

完成后：

更新：

README
ROADMAP
SCHEMAS

测试全部通过。

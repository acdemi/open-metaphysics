/* OpenMetaphysics 前端配置
 *
 * API 基础地址的优先级（从高到低）：
 *   1. URL 查询参数            ?api=http://127.0.0.1:8000
 *   2. localStorage            om.apiBase（页面「设置」中保存）
 *   3. 本文件                  window.OM_CONFIG.apiBase
 *
 * 后端 CORS 需要通过项目既有配置项开启（见 frontend/README.md）：
 *   OM_CORS_ORIGINS=http://127.0.0.1:5173
 */
window.OM_CONFIG = {
  apiBase: "http://127.0.0.1:8000",
  timeoutMs: 90000,

  // 预填示例来自仓库 README 的已验证调用示例：
  //   POST /agents/bazi/compute {"born_at":"1990-06-15T08:30:00+08:00","gender":"male"}
  demo: {
    date: "1990-06-15",
    time: "08:30",
    timezone: "Asia/Shanghai",
    gender: "male",
    question: "今年的工作发展如何？",
    domains: ["bazi"],
  },
};

<template>
  <div class="state-card empty-state" id="results-empty" data-testid="results-empty">
    <div class="empty-glyph" aria-hidden="true">卦</div>
    <h3>尚未开始分析</h3>
    <p>
      左侧已预填一个真实可复现的示例（出生时间 <strong>1990-06-15 08:30（Asia/Shanghai）· 男</strong>），可直接点击「开始分析」，也可以先修改任意字段。
    </p>
    <ul class="plain-list">
      <li><span class="badge badge-fact">计算</span> 由确定性规则引擎产生，同输入结果逐字节可复现。</li>
      <li><span class="badge badge-evidence">证据</span> 为后端在冻结知识语料中检索到的片段及其来源，<strong>不等于</strong>对结论的证明。</li>
      <li><span class="badge badge-interpret">解释</span> 是生成的自然语言文本；默认离线（无 LLM 时降级为确定性后备）。</li>
    </ul>
    <p class="empty-foot">本页面不使用任何前端模拟数据；所有结果均来自实际 HTTP 响应。</p>
  </div>
</template>

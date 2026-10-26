# 语音与真实设备限制

最终测试提交 `cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`。原生 Chromium speechSynthesis API 可用，但声音列表为 0；没有听到实际音频。11 种语言的有效声音、无声音、仅中文声音、延迟枚举、无 API、播放／暂停／继续／停止、错误及切换取消使用明确标记的 API mocks。不能据此签署发音或可听验收。

Windows Edge 只有中文声音的真实根因尚未确定；操作系统语言包、设备声音及浏览器服务需真实设备复测。zh-CN/zh-TW、pt-BR/pt-PT 不默默混用。原生屏幕阅读器及浏览器200%缩放也待测。

完整原文在各 QA 报告；原始声音列表及控制结果见 ../verified-validation/final-agent/results.json、../verified-validation/final-states/states-results.json 和三个 ../verified-matrix-*/matrix-results.json。

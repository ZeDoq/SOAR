export default {
  // 导航
  nav: {
    dashboard: '态势大屏',
    alerts: '告警管理',
    runs: '执行记录',
    workbench: '调查工作台',
    graph: '知识图谱',
    simulator: '攻击模拟',
    login: '登录',
    loggedInAs: '已登录',
    logout: '退出登录',
    settings: '模型配置',
  },

  // 通用
  common: {
    refresh: '刷新',
    save: '保存',
    cancel: '取消',
    close: '关闭',
    loading: '加载中...',
    noData: '暂无数据',
    viewAll: '查看全部 →',
    rebuild: '重建',
  },

  // 状态
  status: {
    completed: '已完成',
    failed: '失败',
    running: '运行中',
    queued: '排队中',
    skipped: '已跳过',
    blocked: '已阻断',
  },

  // 仪表盘
  dashboard: {
    title: '安全态势大屏',
    totalAlerts: '告警总数',
    totalRuns: '执行总数',
    avgRisk: '平均风险分',
    blocked: '已阻断',
    riskDistribution: '风险评分分布',
    actionDistribution: '处置动作分布',
    recentAlerts: '最近告警',
    recentRuns: '最近执行',
    noAlerts: '暂无告警',
    noRuns: '暂无执行',
  },

  // 表头
  table: {
    ip: 'IP 地址',
    source: '来源',
    description: '描述',
    time: '时间',
    id: '编号',
    alert: '告警',
    status: '状态',
    risk: '风险',
    action: '动作',
    template: '模板',
  },

  // 动作
  actions: {
    block: '阻断',
    monitor: '监控',
  },

  // 告警
  alerts: {
    title: '告警管理',
    searchPlaceholder: '按 IP 或描述搜索...',
    allSources: '所有来源',
    noDescription: '无描述',
    notFound: '未找到告警',
    investigation: '告警调查',
    alertInfo: '告警信息',
    ip: 'IP 地址：',
    source: '来源：',
    description: '描述：',
    time: '时间：',
    tags: '标签：',
    latestRun: '最新执行',
    risk: '风险：',
    action: '动作：',
    viewDetail: '查看详情 →',
    kbMatches: '知识库匹配',
    noMatches: '无匹配',
    relatedGraph: '关联图谱',
    noGraphData: '暂无图谱数据',
    runPlaybook: '执行剧本',
    running: '执行中...',
    classic: '经典模式',
    adaptive: '自适应模式',
    runStarted: '剧本已启动',
    noRunYet: '暂无执行记录',
    clickRun: '点击"执行剧本"开始安全响应流程',
  },

  // 执行记录
  runs: {
    title: '执行记录',
    noRuns: '暂无执行记录',
    runNumber: '执行 #{id}',
    riskScore: '风险评分：',
    steps: '执行步骤',
    notFound: '未找到执行记录',
  },

  // 步骤标签
  steps: {
    threat_intel: '威胁情报',
    risk_assessment: '风险评估',
    ai_analysis: 'AI 分析',
    network_recon: '网络侦察',
    firewall_block: '防火墙阻断',
    notify_email: '邮件通知',
    notify_slack: 'Slack 通知',
    report_generation: '报告生成',
  },

  // 步骤短标签
  stepsShort: {
    threat_intel: '情报',
    risk_assessment: '风险',
    ai_analysis: 'AI',
    network_recon: '侦察',
    firewall_block: '防火墙',
    notify_email: '邮件',
    notify_slack: 'Slack',
    report_generation: '报告',
  },

  // 调查工作台
  workbench: {
    title: '调查工作台',
    filterPlaceholder: '筛选...',
    selectAlert: '选择一条告警开始调查',
  },

  // 知识图谱
  graph: {
    title: '知识图谱',
    rebuildGraph: '重建图谱',
    rebuilding: '重建中...',
    noGraphData: '暂无图谱数据，点击"重建图谱"生成。',
    stats: '统计信息',
    nodes: '节点数：',
    edges: '边数：',
    techniques: 'ATT&CK 技术',
    noData: '暂无数据',
    clusters: 'IP 聚类',
    cluster: '聚类 {n}：',
    noClusters: '暂无聚类',
  },

  // 攻击模拟器
  simulator: {
    title: '攻击模拟器',
    runAll: '执行所有场景',
    alerts: '{count} 条告警',
    runScenario: '执行场景',
    alertsCreated: '已创建告警：',
    expected: '预期结果：',
    loading: '加载场景中...',
  },

  // 登录
  login: {
    title: '登录',
    register: '注册',
    username: '用户名',
    password: '密码',
    haveAccount: '已有账号？去登录',
    needAccount: '没有账号？去注册',
    registered: '注册成功！请登录。',
    failed: '操作失败',
  },

  // 模型配置
  settings: {
    title: '模型配置',
    subtitle: '配置 AI 分析使用的模型提供商，API Key 安全存储在服务器端。',
    addModel: '添加模型提供商',
    editModel: '编辑模型提供商',
    preset: '预置模板',
    custom: '自定义',
    name: '显示名称',
    namePlaceholder: '我的模型',
    type: '提供商类型',
    baseUrl: 'API 地址',
    apiKey: 'API Key',
    apiKeyKeep: '留空则保持原值不变',
    modelName: '模型名称',
    setDefault: '设为默认',
    default: '默认',
    test: '测试连接',
    edit: '编辑',
    delete: '删除',
    model: '模型',
    key: '密钥',
    noModels: '暂未配置模型提供商，请在上方添加。',
    fillRequired: '请填写名称、API 地址和模型名称',
    apiKeyRequired: '新增提供商时必须填写 API Key',
    fetchModels: '获取模型',
    selectFromList: '从列表中选择模型：',
    noModelsFetched: '未获取到模型列表，请检查 API Key 和地址',
    fetchFailed: '获取模型列表失败',
    saveFirst: '请先填写 API Key 和 API 地址',
  },

  // Playbook 模板名
  template: {
    full_investigation: '完整调查',
    brute_force: '暴力破解响应',
    port_scan: '端口扫描响应',
    data_exfiltration: '数据外泄响应',
    phishing: '钓鱼响应',
    ddos: 'DDoS 响应',
    low_priority: '低优先级',
  },

  // 攻击类型
  attackType: {
    brute_force: '暴力破解',
    port_scan: '端口扫描',
    data_exfiltration: '数据外泄',
    phishing: '钓鱼攻击',
    ddos: 'DDoS 攻击',
    lateral_movement: '横向移动',
    unknown: '未知',
  },

  // AI 分析
  ai: {
    confidence: '置信度',
    technique: '攻击技术',
    impact: '影响评估',
    actions: '推荐措施',
    reasoning: 'AI 推理过程',
    analyses: 'AI 分析次数',
    avgConfidence: '平均置信度',
  },

  // 威胁等级
  threatLevel: {
    malicious: '恶意',
    suspicious: '可疑',
    benign: '良性',
    false_positive: '误报',
    unknown: '未知',
  },

  // 报告
  report: {
    copy: '复制报告',
    copied: '已复制',
    download: '下载',
  },

  // 风险图标签
  riskChart: {
    '0-20': '0-20',
    '21-40': '21-40',
    '41-60': '41-60',
    '61-80': '61-80',
    '81-100': '81-100',
  },
}

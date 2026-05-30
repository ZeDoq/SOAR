export default {
  // Navigation
  nav: {
    dashboard: 'Dashboard',
    alerts: 'Alerts',
    runs: 'Runs',
    workbench: 'Workbench',
    graph: 'Graph',
    simulator: 'Simulator',
    login: 'Login',
    loggedInAs: 'Logged in as',
    logout: 'Logout',
    settings: 'Settings',
  },

  // Common
  common: {
    refresh: 'Refresh',
    save: 'Save',
    cancel: 'Cancel',
    close: 'Close',
    loading: 'Loading...',
    noData: 'No data',
    viewAll: 'View All →',
    rebuild: 'Rebuild',
  },

  // Status
  status: {
    completed: 'Completed',
    failed: 'Failed',
    running: 'Running',
    queued: 'Queued',
    skipped: 'Skipped',
    blocked: 'Blocked',
  },

  // Dashboard
  dashboard: {
    title: 'Security Dashboard',
    totalAlerts: 'Total Alerts',
    totalRuns: 'Total Runs',
    avgRisk: 'Avg Risk Score',
    blocked: 'Blocked',
    riskDistribution: 'Risk Score Distribution',
    actionDistribution: 'Action Distribution',
    recentAlerts: 'Recent Alerts',
    recentRuns: 'Recent Runs',
    noAlerts: 'No alerts',
    noRuns: 'No runs',
  },

  // Table headers
  table: {
    ip: 'IP',
    source: 'Source',
    description: 'Description',
    time: 'Time',
    id: 'ID',
    alert: 'Alert',
    status: 'Status',
    risk: 'Risk',
    action: 'Action',
    template: 'Template',
  },

  // Actions
  actions: {
    block: 'Block',
    monitor: 'Monitor',
  },

  // Alerts
  alerts: {
    title: 'Alerts',
    searchPlaceholder: 'Search by IP or description...',
    allSources: 'All Sources',
    noDescription: 'No description',
    notFound: 'No alerts found',
    investigation: 'Alert Investigation',
    alertInfo: 'Alert Info',
    ip: 'IP:',
    source: 'Source:',
    description: 'Description:',
    time: 'Time:',
    tags: 'Tags:',
    latestRun: 'Latest Run',
    risk: 'Risk:',
    action: 'Action:',
    viewDetail: 'View Full Detail →',
    kbMatches: 'Knowledge Base Matches',
    noMatches: 'No matches',
    relatedGraph: 'Related Graph',
    noGraphData: 'No graph data',
    runPlaybook: 'Run Playbook',
    running: 'Running...',
    classic: 'Classic',
    adaptive: 'Adaptive',
    runStarted: 'Playbook started',
    noRunYet: 'No runs yet',
    clickRun: 'Click "Run Playbook" to execute security response',
  },

  // Runs
  runs: {
    title: 'Playbook Runs',
    noRuns: 'No runs',
    runNumber: 'Run #{id}',
    riskScore: 'Risk Score:',
    steps: 'Steps',
    notFound: 'Run not found',
  },

  // Step labels
  steps: {
    threat_intel: 'Threat Intelligence',
    risk_assessment: 'Risk Assessment',
    ai_analysis: 'AI Analysis',
    network_recon: 'Network Recon',
    firewall_block: 'Firewall Block',
    notify_email: 'Email Notification',
    notify_slack: 'Slack Notification',
    report_generation: 'Report Generation',
  },

  // Step short labels
  stepsShort: {
    threat_intel: 'Intel',
    risk_assessment: 'Risk',
    ai_analysis: 'AI',
    network_recon: 'Recon',
    firewall_block: 'Firewall',
    notify_email: 'Email',
    notify_slack: 'Slack',
    report_generation: 'Report',
  },

  // Workbench
  workbench: {
    title: 'Investigation Workbench',
    filterPlaceholder: 'Filter...',
    selectAlert: 'Select an alert to investigate',
  },

  // Graph
  graph: {
    title: 'Knowledge Graph',
    rebuildGraph: 'Rebuild Graph',
    rebuilding: 'Rebuilding...',
    noGraphData: 'No graph data. Click "Rebuild Graph" to populate.',
    stats: 'Stats',
    nodes: 'Nodes:',
    edges: 'Edges:',
    techniques: 'Techniques',
    noData: 'No data',
    clusters: 'Clusters',
    cluster: 'Cluster {n}:',
    noClusters: 'No clusters',
  },

  // Simulator
  simulator: {
    title: 'Attack Simulator',
    runAll: 'Run All Scenarios',
    alerts: '{count} alert(s)',
    runScenario: 'Run Scenario',
    alertsCreated: 'Alerts Created:',
    expected: 'Expected:',
    loading: 'Loading scenarios...',
  },

  // Login
  login: {
    title: 'Login',
    register: 'Register',
    username: 'Username',
    password: 'Password',
    haveAccount: 'Already have an account? Login',
    needAccount: 'Need an account? Register',
    registered: 'Registered! Now login.',
    failed: 'Failed',
  },

  // Settings
  settings: {
    title: 'Model Settings',
    subtitle: 'Configure LLM providers for AI analysis. API keys are stored securely.',
    addModel: 'Add Model Provider',
    editModel: 'Edit Model Provider',
    preset: 'Preset Template',
    custom: 'Custom',
    name: 'Display Name',
    namePlaceholder: 'My Model',
    type: 'Provider Type',
    baseUrl: 'API Base URL',
    apiKey: 'API Key',
    apiKeyKeep: 'Leave empty to keep current',
    modelName: 'Model Name',
    setDefault: 'Set as Default',
    default: 'Default',
    test: 'Test',
    edit: 'Edit',
    delete: 'Delete',
    model: 'Model',
    key: 'Key',
    noModels: 'No model providers configured. Add one above.',
    fillRequired: 'Please fill in name, URL, and model name',
    apiKeyRequired: 'API key is required for new providers',
    fetchModels: 'Get Models',
    selectFromList: 'Select from available models:',
    noModelsFetched: 'No models fetched, please check API key and URL',
    fetchFailed: 'Failed to fetch models',
    saveFirst: 'Please fill in API key and URL first',
  },

  // Playbook template names
  template: {
    full_investigation: 'Full Investigation',
    brute_force: 'Brute Force Response',
    port_scan: 'Port Scan Response',
    data_exfiltration: 'Exfiltration Response',
    phishing: 'Phishing Response',
    ddos: 'DDoS Response',
    low_priority: 'Low Priority',
  },

  // Attack types
  attackType: {
    brute_force: 'Brute Force',
    port_scan: 'Port Scan',
    data_exfiltration: 'Data Exfiltration',
    phishing: 'Phishing',
    ddos: 'DDoS Attack',
    lateral_movement: 'Lateral Movement',
    unknown: 'Unknown',
  },

  // AI Analysis
  ai: {
    confidence: 'Confidence',
    technique: 'Attack Technique',
    impact: 'Impact Assessment',
    actions: 'Recommended Actions',
    reasoning: 'AI Reasoning',
    analyses: 'AI Analyses',
    avgConfidence: 'Avg Confidence',
  },

  // Threat levels
  threatLevel: {
    malicious: 'MALICIOUS',
    suspicious: 'SUSPICIOUS',
    benign: 'BENIGN',
    false_positive: 'FALSE POSITIVE',
    unknown: 'UNKNOWN',
  },

  // Report
  report: {
    copy: 'Copy Report',
    copied: 'Copied',
    download: 'Download',
  },

  // Risk chart labels
  riskChart: {
    '0-20': '0-20',
    '21-40': '21-40',
    '41-60': '41-60',
    '61-80': '61-80',
    '81-100': '81-100',
  },
}

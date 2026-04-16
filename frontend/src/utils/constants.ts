export const CAMPAIGN_STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  validating: "Валидация",
  generating: "Генерация",
  ready: "Готова",
  running: "Отправка",
  paused: "Пауза",
  completed: "Завершена",
  failed: "Ошибка",
};

export const CAMPAIGN_STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  validating: "bg-yellow-100 text-yellow-700",
  generating: "bg-purple-100 text-purple-700",
  ready: "bg-blue-100 text-blue-700",
  running: "bg-green-100 text-green-700",
  paused: "bg-orange-100 text-orange-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export const SEND_STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает",
  sent: "Отправлено",
  failed: "Ошибка",
  skipped: "Пропущено",
};

export const POLLING_INTERVALS = {
  CAMPAIGN: 5000,
  CAMPAIGN_STATS: 3000,
  WS_RECONNECT: 3000,
} as const;

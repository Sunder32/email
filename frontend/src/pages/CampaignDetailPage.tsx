import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCampaign, startCampaign, deleteCampaign } from "@/api/campaigns";
import { getVariations } from "@/api/variations";
import { getSendLogs } from "@/api/sendLogs";
import {
  getContacts,
  getCampaignReport,
  markAllValid,
  exportReportUrl,
} from "@/api/contacts";
import Button from "@/components/common/Button";
import Badge from "@/components/common/Badge";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { Play, Trash2, Download, CheckCircle2 } from "lucide-react";
import { CAMPAIGN_STATUS_LABELS, CAMPAIGN_STATUS_COLORS, SEND_STATUS_LABELS } from "@/utils/constants";
import { formatNumber, formatDate, truncate } from "@/utils/formatters";
import type { CampaignReport } from "@/types/campaign";
import toast from "react-hot-toast";
import { handleError } from "@/utils/errors";

type Tab = "logs" | "contacts" | "variations";

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const campaignId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showDelete, setShowDelete] = useState(false);
  const [tab, setTab] = useState<Tab>("logs");
  const [validationFilter, setValidationFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState("");

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => getCampaign(campaignId),
  });

  const { data: report } = useQuery({
    queryKey: ["report", campaignId],
    queryFn: () => getCampaignReport(campaignId),
  });

  const { data: logs } = useQuery({
    queryKey: ["logs", campaignId],
    queryFn: () => getSendLogs(campaignId, { size: 200 }),
    enabled: tab === "logs",
  });

  const { data: contacts } = useQuery({
    queryKey: ["contacts", campaignId, validationFilter, statusFilter, search],
    queryFn: () =>
      getContacts(campaignId, {
        validation: validationFilter || undefined,
        status: statusFilter || undefined,
        search: search || undefined,
        size: 200,
      }),
    enabled: tab === "contacts",
  });

  const { data: variations } = useQuery({
    queryKey: ["variations", campaignId],
    queryFn: () => getVariations(campaignId),
    enabled: tab === "variations",
  });

  const startMut = useMutation({
    mutationFn: () => startCampaign(campaignId),
    onSuccess: () => navigate(`/campaigns/${campaignId}/monitor`),
    onError: (e) => handleError(e),
  });

  const deleteMut = useMutation({
    mutationFn: () => deleteCampaign(campaignId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      navigate("/campaigns");
      toast.success("Кампания удалена");
    },
  });

  const markValidMut = useMutation({
    mutationFn: () => markAllValid(campaignId),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["campaign", campaignId] });
      qc.invalidateQueries({ queryKey: ["report", campaignId] });
      qc.invalidateQueries({ queryKey: ["contacts", campaignId] });
      toast.success(`Помечено как валидные: ${res.marked_valid}`);
    },
    onError: (e) => handleError(e),
  });

  if (isLoading) return <Spinner />;
  if (!campaign) return <p>Кампания не найдена</p>;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
          <div className="mt-1 flex items-center gap-2">
            <Badge
              label={CAMPAIGN_STATUS_LABELS[campaign.status] || campaign.status}
              color={CAMPAIGN_STATUS_COLORS[campaign.status]}
            />
            {campaign.skip_validation && (
              <Badge label="Без валидации" color="bg-yellow-100 text-yellow-700" />
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <a href={exportReportUrl(campaignId)} download>
            <Button variant="secondary">
              <Download className="h-4 w-4" /> Экспорт CSV
            </Button>
          </a>
          {(campaign.status === "ready" || campaign.status === "paused" || campaign.status === "draft") && (
            <Button onClick={() => startMut.mutate()} loading={startMut.isPending}>
              <Play className="h-4 w-4" /> Запустить
            </Button>
          )}
          {campaign.status === "running" && (
            <Link to={`/campaigns/${campaignId}/monitor`}>
              <Button>Мониторинг</Button>
            </Link>
          )}
          <Button variant="danger" onClick={() => setShowDelete(true)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {report && (
        <ReportBlock
          report={report}
          onMarkValid={() => markValidMut.mutate()}
          markPending={markValidMut.isPending}
        />
      )}

      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Тема письма</h3>
        <p className="text-sm text-gray-900">{campaign.original_subject}</p>
        <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-700">Текст письма</h3>
        <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm text-gray-800">
          {campaign.original_body}
        </pre>
      </div>

      <div className="mb-4 flex gap-1">
        {(["logs", "contacts", "variations"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === t ? "bg-primary-50 text-primary-700" : "text-gray-500 hover:bg-gray-100"
            }`}
          >
            {t === "logs" ? "Лог отправок" : t === "contacts" ? "Контакты" : "Вариации"}
          </button>
        ))}
      </div>

      {tab === "logs" && (
        <div className="rounded-xl border border-gray-200 bg-white">
          {logs && logs.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="px-6 py-3 font-medium">Email получателя</th>
                  <th className="px-6 py-3 font-medium">Отправлено с</th>
                  <th className="px-6 py-3 font-medium">Статус</th>
                  <th className="px-6 py-3 font-medium">Причина / Тема</th>
                  <th className="px-6 py-3 font-medium">Время</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-3 text-gray-900 font-medium">
                      {log.contact_email || `ID ${log.contact_id}`}
                    </td>
                    <td className="px-6 py-3 text-gray-500">{log.mailbox_email || "—"}</td>
                    <td className="px-6 py-3">
                      <Badge
                        label={SEND_STATUS_LABELS[log.status] || log.status}
                        color={log.status === "sent" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
                      />
                    </td>
                    <td className="px-6 py-3 text-gray-600">
                      {log.status === "failed" ? (
                        <span className="text-red-600">{log.error_label || log.error_message}</span>
                      ) : (
                        truncate(log.subject_used, 50)
                      )}
                    </td>
                    <td className="px-6 py-3 text-gray-500">{formatDate(log.sent_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState message="Нет записей" />
          )}
        </div>
      )}

      {tab === "contacts" && (
        <div>
          <div className="mb-3 flex flex-wrap gap-2">
            <select
              value={validationFilter}
              onChange={(e) => setValidationFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Все (валидация)</option>
              <option value="valid">Валидные</option>
              <option value="invalid">Невалидные</option>
              <option value="pending">Не проверены</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Все (отправка)</option>
              <option value="pending">В очереди</option>
              <option value="sent">Отправлено</option>
              <option value="failed">С ошибкой</option>
            </select>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по email..."
              className="flex-1 min-w-[200px] rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="rounded-xl border border-gray-200 bg-white">
            {contacts && contacts.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="px-6 py-3 font-medium">Email</th>
                    <th className="px-6 py-3 font-medium">Валидация</th>
                    <th className="px-6 py-3 font-medium">Отправка</th>
                    <th className="px-6 py-3 font-medium">Причина невалидности</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {contacts.map((c) => (
                    <tr key={c.id}>
                      <td className="px-6 py-3 font-medium text-gray-900">{c.email}</td>
                      <td className="px-6 py-3">
                        {c.is_valid === true ? (
                          <Badge label="✓ валидный" color="bg-green-100 text-green-700" />
                        ) : c.is_valid === false ? (
                          <Badge label="✗ невалидный" color="bg-red-100 text-red-700" />
                        ) : (
                          <Badge label="? не проверен" color="bg-gray-100 text-gray-600" />
                        )}
                      </td>
                      <td className="px-6 py-3">
                        <Badge
                          label={SEND_STATUS_LABELS[c.status] || c.status}
                          color={
                            c.status === "sent"
                              ? "bg-green-100 text-green-700"
                              : c.status === "failed"
                              ? "bg-red-100 text-red-700"
                              : "bg-gray-100 text-gray-600"
                          }
                        />
                      </td>
                      <td className="px-6 py-3 text-gray-500">{c.validation_error_label || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState message="Нет контактов" />
            )}
          </div>
        </div>
      )}

      {tab === "variations" && (
        <div className="space-y-3">
          {variations && variations.length > 0 ? (
            variations.map((v) => (
              <div key={v.id} className="rounded-xl border border-gray-200 bg-white p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{v.subject_variant}</p>
                    <p className="mt-1 text-sm text-gray-600">{v.iceberg_variant}</p>
                  </div>
                  <span className="text-xs text-gray-400">Исп.: {v.times_used}</span>
                </div>
              </div>
            ))
          ) : (
            <EmptyState message="Нет вариаций" />
          )}
        </div>
      )}

      <ConfirmDialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMut.mutate()}
        title="Удалить кампанию?"
        message="Все контакты, вариации и логи будут удалены."
        confirmLabel="Удалить"
        loading={deleteMut.isPending}
      />
    </div>
  );
}

function ReportBlock({
  report,
  onMarkValid,
  markPending,
}: {
  report: CampaignReport;
  onMarkValid: () => void;
  markPending: boolean;
}) {
  const b = report.validation_breakdown;
  const hasInvalid = report.invalid_contacts > 0;

  return (
    <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Сводка по кампании</h3>
        {hasInvalid && (
          <Button variant="secondary" size="sm" onClick={onMarkValid} loading={markPending}>
            <CheckCircle2 className="h-4 w-4" />
            Пометить всё валидным
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <Stat label="Всего контактов" value={report.total_contacts} />
        <Stat label="Отправлено" value={report.sent_count} color="text-green-600" />
        <Stat label="Ошибки отправки" value={report.failed_count} color="text-red-600" />
        <Stat label="В очереди" value={report.pending_count} color="text-gray-500" />
      </div>

      {hasInvalid && (
        <div className="mt-5 rounded-lg bg-gray-50 p-4">
          <p className="mb-2 text-sm font-medium text-gray-700">
            Невалидных: <span className="text-red-600">{report.invalid_contacts}</span>
          </p>
          <div className="grid gap-2 text-xs text-gray-600 sm:grid-cols-5">
            {b.syntax_errors > 0 && <div>Неверный формат: <b>{b.syntax_errors}</b></div>}
            {b.no_mx > 0 && <div>Домена нет: <b>{b.no_mx}</b></div>}
            {b.smtp_rejected > 0 && <div>SMTP отклонил: <b>{b.smtp_rejected}</b></div>}
            {b.disposable > 0 && <div>Одноразовые: <b>{b.disposable}</b></div>}
            {b.other > 0 && <div>Прочее: <b>{b.other}</b></div>}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  color = "text-gray-900",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{formatNumber(value)}</p>
    </div>
  );
}

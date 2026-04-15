import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCampaign, startCampaign, deleteCampaign } from "@/api/campaigns";
import { getVariations } from "@/api/variations";
import { getSendLogs } from "@/api/sendLogs";
import Button from "@/components/common/Button";
import Badge from "@/components/common/Badge";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { Play, Trash2 } from "lucide-react";
import { CAMPAIGN_STATUS_LABELS, CAMPAIGN_STATUS_COLORS, SEND_STATUS_LABELS } from "@/utils/constants";
import { formatNumber, formatDate, truncate } from "@/utils/formatters";
import toast from "react-hot-toast";

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const campaignId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showDelete, setShowDelete] = useState(false);
  const [tab, setTab] = useState<"logs" | "variations">("logs");

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => getCampaign(campaignId),
  });

  const { data: logs } = useQuery({
    queryKey: ["logs", campaignId],
    queryFn: () => getSendLogs(campaignId, { size: 100 }),
    enabled: tab === "logs",
  });

  const { data: variations } = useQuery({
    queryKey: ["variations", campaignId],
    queryFn: () => getVariations(campaignId),
    enabled: tab === "variations",
  });

  const startMut = useMutation({
    mutationFn: () => startCampaign(campaignId),
    onSuccess: () => navigate(`/campaigns/${campaignId}/monitor`),
    onError: (e: any) => toast.error(e.response?.data?.detail || "Ошибка"),
  });

  const deleteMut = useMutation({
    mutationFn: () => deleteCampaign(campaignId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      navigate("/campaigns");
      toast.success("Кампания удалена");
    },
  });

  if (isLoading) return <Spinner />;
  if (!campaign) return <p>Кампания не найдена</p>;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
          <Badge
            label={CAMPAIGN_STATUS_LABELS[campaign.status] || campaign.status}
            color={CAMPAIGN_STATUS_COLORS[campaign.status]}
          />
        </div>
        <div className="flex gap-2">
          {(campaign.status === "ready" || campaign.status === "paused") && (
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

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <InfoCard label="Всего контактов" value={formatNumber(campaign.total_contacts)} />
        <InfoCard label="Валидных" value={formatNumber(campaign.valid_contacts)} />
        <InfoCard label="Отправлено" value={formatNumber(campaign.sent_count)} />
        <InfoCard label="Ошибок" value={formatNumber(campaign.failed_count)} />
      </div>

      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Тема письма</h3>
        <p className="text-sm text-gray-900">{campaign.original_subject}</p>
        <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-700">Текст письма</h3>
        <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm text-gray-800">
          {campaign.original_body}
        </pre>
      </div>

      <div className="mb-4 flex gap-1">
        <button
          onClick={() => setTab("logs")}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
            tab === "logs" ? "bg-primary-50 text-primary-700" : "text-gray-500 hover:bg-gray-100"
          }`}
        >
          Лог отправок
        </button>
        <button
          onClick={() => setTab("variations")}
          className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
            tab === "variations" ? "bg-primary-50 text-primary-700" : "text-gray-500 hover:bg-gray-100"
          }`}
        >
          Вариации
        </button>
      </div>

      {tab === "logs" && (
        <div className="rounded-xl border border-gray-200 bg-white">
          {logs && logs.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="px-6 py-3 font-medium">Кому</th>
                  <th className="px-6 py-3 font-medium">Тема</th>
                  <th className="px-6 py-3 font-medium">Статус</th>
                  <th className="px-6 py-3 font-medium">Время</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-3 text-gray-900">{log.contact_id}</td>
                    <td className="px-6 py-3 text-gray-600">{truncate(log.subject_used, 50)}</td>
                    <td className="px-6 py-3">
                      <Badge
                        label={SEND_STATUS_LABELS[log.status] || log.status}
                        color={log.status === "sent" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
                      />
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

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

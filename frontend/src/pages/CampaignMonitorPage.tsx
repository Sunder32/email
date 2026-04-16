import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCampaign, pauseCampaign, stopCampaign, getCampaignStats } from "@/api/campaigns";
import { useCampaignProgress } from "@/hooks/useCampaignProgress";
import Button from "@/components/common/Button";
import Badge from "@/components/common/Badge";
import Spinner from "@/components/common/Spinner";
import { Pause, Square, Wifi, WifiOff } from "lucide-react";
import { formatDuration, formatNumber } from "@/utils/formatters";
import { CAMPAIGN_STATUS_LABELS, CAMPAIGN_STATUS_COLORS } from "@/utils/constants";
import toast from "react-hot-toast";

export default function CampaignMonitorPage() {
  const { id } = useParams<{ id: string }>();
  const campaignId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => getCampaign(campaignId),
    refetchInterval: 5000,
  });

  const { data: stats } = useQuery({
    queryKey: ["campaignStats", campaignId],
    queryFn: () => getCampaignStats(campaignId),
    refetchInterval: 3000,
  });

  const { progress, isConnected } = useCampaignProgress(campaignId);

  const pauseMut = useMutation({
    mutationFn: () => pauseCampaign(campaignId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaign", campaignId] });
      toast.success("Рассылка на паузе");
    },
  });

  const stopMut = useMutation({
    mutationFn: () => stopCampaign(campaignId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaign", campaignId] });
      toast.success("Рассылка остановлена");
    },
  });

  if (isLoading) return <Spinner />;
  if (!campaign) return <p>Кампания не найдена</p>;

  const sent = progress.sent || campaign.sent_count;
  const failed = progress.failed || campaign.failed_count;
  const total = progress.total || campaign.total_contacts;
  const denom = campaign.valid_contacts > 0 ? campaign.valid_contacts : total;
  const pct = denom > 0 ? Math.round((sent / denom) * 100) : 0;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
          <div className="mt-1 flex items-center gap-3">
            <Badge
              label={CAMPAIGN_STATUS_LABELS[campaign.status] || campaign.status}
              color={CAMPAIGN_STATUS_COLORS[campaign.status]}
            />
            <span className="flex items-center gap-1 text-sm text-gray-500">
              {isConnected ? (
                <><Wifi className="h-3.5 w-3.5 text-green-500" /> Live</>
              ) : (
                <><WifiOff className="h-3.5 w-3.5 text-red-400" /> Offline</>
              )}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {campaign.status === "running" && (
            <>
              <Button variant="secondary" onClick={() => pauseMut.mutate()} loading={pauseMut.isPending}>
                <Pause className="h-4 w-4" /> Пауза
              </Button>
              <Button variant="danger" onClick={() => stopMut.mutate()} loading={stopMut.isPending}>
                <Square className="h-4 w-4" /> Остановить
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <MetricCard label="Отправлено" value={formatNumber(sent)} sub={`из ${formatNumber(total)}`} />
        <MetricCard label="Ошибки" value={formatNumber(failed)} sub="" />
        <MetricCard label="Прогресс" value={`${pct}%`} sub="" />
        <MetricCard
          label="Осталось"
          value={formatDuration(stats?.eta_seconds)}
          sub={stats?.elapsed_seconds ? `Прошло: ${formatDuration(stats.elapsed_seconds)}` : ""}
        />
      </div>

      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-gray-600">Прогресс отправки</span>
          <span className="font-medium">{pct}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className="h-full rounded-full bg-primary-500 transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {(progress.currentDomain || progress.currentMailbox) && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Текущая отправка</h3>
          <div className="grid gap-2 sm:grid-cols-2 text-sm">
            <div>
              <span className="text-gray-500">Домен: </span>
              <span className="font-medium">{progress.currentDomain}</span>
            </div>
            <div>
              <span className="text-gray-500">Ящик: </span>
              <span className="font-medium">{progress.currentMailbox}</span>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-sm font-semibold text-gray-700">Последние отправки</h3>
        </div>
        {progress.log.length > 0 ? (
          <div className="divide-y divide-gray-50 text-sm">
            {progress.log.map((entry, i) => (
              <div key={i} className="flex items-center justify-between px-6 py-3">
                <div>
                  <span className="font-medium text-gray-900">{entry.contact}</span>
                  <span className="ml-2 text-gray-400">{entry.mailbox}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-xs">{entry.time}</span>
                  <Badge
                    label={entry.status === "sent" ? "OK" : "ERR"}
                    color={entry.status === "sent" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="px-6 py-8 text-center text-sm text-gray-400">Ожидание данных...</p>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

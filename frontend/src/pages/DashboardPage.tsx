import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCampaigns } from "@/api/campaigns";
import { getDomains } from "@/api/domains";
import { Send, Globe, Mail, TrendingUp } from "lucide-react";
import Badge from "@/components/common/Badge";
import Spinner from "@/components/common/Spinner";
import { CAMPAIGN_STATUS_LABELS, CAMPAIGN_STATUS_COLORS } from "@/utils/constants";
import { formatNumber, formatDate } from "@/utils/formatters";

export default function DashboardPage() {
  const { data: campaigns, isLoading: loadingC } = useQuery({
    queryKey: ["campaigns"],
    queryFn: getCampaigns,
  });
  const { data: domains, isLoading: loadingD } = useQuery({
    queryKey: ["domains"],
    queryFn: getDomains,
  });

  if (loadingC || loadingD) return <Spinner />;

  const totalMailboxes = domains?.reduce((s, d) => s + d.mailboxes.length, 0) ?? 0;
  const activeCampaigns = campaigns?.filter((c) => c.status === "running") ?? [];
  const totalSent = campaigns?.reduce((s, c) => s + c.sent_count, 0) ?? 0;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Дашборд</h1>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Globe} label="Доменов" value={domains?.length ?? 0} />
        <StatCard icon={Mail} label="Ящиков" value={totalMailboxes} />
        <StatCard icon={Send} label="Активных рассылок" value={activeCampaigns.length} />
        <StatCard icon={TrendingUp} label="Всего отправлено" value={formatNumber(totalSent)} />
      </div>

      <div className="rounded-xl border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Последние кампании</h2>
        </div>
        {campaigns && campaigns.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {campaigns.slice(0, 10).map((c) => (
              <Link
                key={c.id}
                to={c.status === "running" ? `/campaigns/${c.id}/monitor` : `/campaigns/${c.id}`}
                className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition"
              >
                <div>
                  <p className="font-medium text-gray-900">{c.name}</p>
                  <p className="mt-0.5 text-sm text-gray-500">{formatDate(c.created_at)}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">
                    {formatNumber(c.sent_count)} / {formatNumber(c.total_contacts)}
                  </span>
                  <Badge
                    label={CAMPAIGN_STATUS_LABELS[c.status] || c.status}
                    color={CAMPAIGN_STATUS_COLORS[c.status]}
                  />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="px-6 py-8 text-center text-sm text-gray-400">Нет кампаний</p>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50">
        <Icon className="h-5 w-5 text-primary-600" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{label}</p>
    </div>
  );
}

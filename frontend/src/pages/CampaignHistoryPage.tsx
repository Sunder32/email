import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCampaigns } from "@/api/campaigns";
import Badge from "@/components/common/Badge";
import Spinner from "@/components/common/Spinner";
import EmptyState from "@/components/common/EmptyState";
import { CAMPAIGN_STATUS_LABELS, CAMPAIGN_STATUS_COLORS } from "@/utils/constants";
import { formatNumber, formatDate } from "@/utils/formatters";

export default function CampaignHistoryPage() {
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: getCampaigns,
  });

  if (isLoading) return <Spinner />;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Кампании</h1>

      {campaigns && campaigns.length > 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="px-6 py-3 font-medium">Название</th>
                <th className="px-6 py-3 font-medium">Статус</th>
                <th className="px-6 py-3 font-medium">Отправлено</th>
                <th className="px-6 py-3 font-medium">Ошибки</th>
                <th className="px-6 py-3 font-medium">Контактов</th>
                <th className="px-6 py-3 font-medium">Создана</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {campaigns.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50 transition">
                  <td className="px-6 py-4">
                    <Link
                      to={c.status === "running" ? `/campaigns/${c.id}/monitor` : `/campaigns/${c.id}`}
                      className="font-medium text-primary-600 hover:text-primary-700"
                    >
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <Badge
                      label={CAMPAIGN_STATUS_LABELS[c.status] || c.status}
                      color={CAMPAIGN_STATUS_COLORS[c.status]}
                    />
                  </td>
                  <td className="px-6 py-4">{formatNumber(c.sent_count)}</td>
                  <td className="px-6 py-4">{formatNumber(c.failed_count)}</td>
                  <td className="px-6 py-4">
                    {c.valid_contacts > 0 && c.valid_contacts !== c.total_contacts
                      ? `${formatNumber(c.valid_contacts)} / ${formatNumber(c.total_contacts)}`
                      : formatNumber(c.total_contacts)}
                  </td>
                  <td className="px-6 py-4 text-gray-500">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="Нет созданных кампаний" />
      )}
    </div>
  );
}
